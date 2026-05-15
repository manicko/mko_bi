"""Data processing service.

Provides business logic for uploading, processing and tracking
data processing status for dashboards.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.config import get_config
from mkobi.core.permissions import check_dashboard_access, PermissionError
from mkobi.core.redis_client import get_redis_client
from mkobi.core.security import RateLimiter
from mkobi.core.task_queue import enqueue_job
from mkobi.data.loaders.loader import detect_file_type
from mkobi.db.session import get_session
from mkobi.interfaces.repository_interfaces import (
    IAggregatedDataRepository,
    IGraphRepository,
    IProcessingLogRepository,
)
from mkobi.interfaces.service_interfaces import IDataService
from mkobi.models.data import ProcessingResultData, ProcessingResult, ProcessingStatusResponse, UploadResponse
from mkobi.models.enums import FileExtensionEnum, MimeTypeEnum, ProcessingStatus, UploadMode

logger = logging.getLogger(__name__)


class DataService(IDataService):
    """Data service class for processing data."""

    def __init__(
        self,
        agg_repo: IAggregatedDataRepository,
        log_repo: IProcessingLogRepository,
        graph_repo: IGraphRepository,
    ) -> None:
        """Initialize service with injected repositories.

        Args:
            agg_repo: Aggregated data repository.
            log_repo: Processing log repository.
            graph_repo: Graph repository.
        """
        self.agg_repo = agg_repo
        self.log_repo = log_repo
        self.graph_repo = graph_repo
        self._upload_rate_limiter: RateLimiter | None = None
        # Try to initialize Redis, but don't fail if Redis is unavailable
        try:
            self._upload_rate_limiter = RateLimiter(get_redis_client())
        except Exception:
            logger.warning("Redis unavailable, rate limiting disabled")
            self._upload_rate_limiter = None
        config = get_config()
        self._upload_rate_limit = 10  # requests
        self._upload_rate_period = 60  # seconds (1 minute)
        self._max_file_size = config.max_file_size

    async def process_upload(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        mode: UploadMode = UploadMode.OVERWRITE,
        db: AsyncSession | None = None,
    ) -> UploadResponse:
        """Process uploaded file and save aggregates.

        Args:
            file_content: Raw file content bytes.
            dashboard_id: Target dashboard ID.
            user_id: Optional user ID for permission check.
            filename: Original filename.
            content_type: MIME type of uploaded file.
            mode: Upload mode (OVERWRITE clears old data, APPEND keeps it).
            db: Optional database session.

        Returns:
            UploadResponse with task information.
        """
        actual_db = db
        if actual_db is None:
            async with get_session() as session:
                return await self._process_upload_with_session(
                    file_content,
                    dashboard_id,
                    user_id,
                    filename,
                    content_type,
                    mode,
                    session,
                )
        return await self._process_upload_with_session(
            file_content,
            dashboard_id,
            user_id,
            filename,
            content_type,
            mode,
            actual_db,
        )

    async def _process_upload_with_session(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None,
        filename: str | None,
        content_type: str | None,
        mode: UploadMode,
        db: AsyncSession,
    ) -> UploadResponse:
        """Internal method for processing with session.

        Args:
            file_content: Raw file content bytes.
            dashboard_id: Target dashboard ID.
            user_id: Optional user ID for permission check.
            filename: Original filename.
            content_type: MIME type of uploaded file.
            mode: Upload mode (OVERWRITE clears old data, APPEND keeps it).
            db: Database session.
        """
        # Validate file
        self._validate_file(filename, file_content, content_type)

        # Check access permissions
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id,
                dashboard_id=dashboard_id,
                required_permission="edit",
                db=db,
            )
            if not has_access:
                logger.warning(
                    "Processing denied: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                raise PermissionError(
                    "No permission to process data for this dashboard"
                )

        # Save file to temporary directory
        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Detect file type using enum-based function
        file_ext = ".csv.gz" if filename and detect_file_type(filename) == FileExtensionEnum.CSV_GZ else ".csv"

        # Create processing log entry with STARTED status
        log = await self.log_repo.create_log(
            db=db,
            dashboard_id=dashboard_id,
            status=ProcessingStatus.STARTED,
            message=f"Upload started with mode={mode}",
        )
        await db.flush()

        # Use log.id for the file path to ensure consistency
        temp_file_path = upload_dir / f"{log.id}{file_ext}"

        try:
            async with aiofiles.open(temp_file_path, mode='wb') as f:
                await f.write(file_content)
            logger.info("File saved: path=%s, mode=%s", temp_file_path, mode)
        except Exception as e:
            logger.error("File save error: %s", e)
            raise

        # Update status to UPLOADED after file is saved successfully
        await self.log_repo.update_status(
            log_id=log.id,
            status=ProcessingStatus.UPLOADED,
            message=f"File uploaded successfully, awaiting processing. mode={mode}",
            db=db,
        )
        await db.commit()

        # Enqueue job with mode parameter - use log.id as the identifier
        from mkobi.workers.data_worker import process_csv_background
        await enqueue_job(
            process_csv_background,
            file_path=str(temp_file_path),
            dashboard_id=str(dashboard_id),
            task_id=str(log.id),
            log_id=str(log.id),
            mode=str(mode),
        )

        logger.info(
            "Task enqueued: task_id=%s, dashboard_id=%s, mode=%s",
            log.id,
            dashboard_id,
            mode,
        )

        return UploadResponse(
            task_id=log.id,
            filename=filename or "unknown",
            dashboard_id=dashboard_id,
            status=ProcessingStatus.UPLOADED,
            message="File uploaded successfully, processing queued",
            uploaded_at=datetime.now(),
        )

    async def get_aggregated_data(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[ProcessingResultData]:
        """Get aggregated data for graph."""
        actual_db = db
        if actual_db is None:
            async with get_session() as session:
                return await self._get_aggregated_data_with_session(
                    dashboard_id,
                    graph_id,
                    session,
                )
        return await self._get_aggregated_data_with_session(
            dashboard_id,
            graph_id,
            actual_db,
        )

    async def _get_aggregated_data_with_session(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        db: AsyncSession,
    ) -> list[ProcessingResultData]:
        """Internal method to get aggregated data."""
        records = await self.agg_repo.get_by_graph_id(
            graph_id, db,
        )

        result = []
        for record in records:
            result.append(
                ProcessingResultData(
                    columns=list(record.dims.keys()) + list(record.metrics.keys()),
                    rows=1,
                    dashboard_id=record.dashboard_id,
                    preview=[{**record.dims, **record.metrics}],
                )
            )
        return result

    async def get_available_metrics(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[str]:
        """Get available metrics for dashboard.

        Args:
            dashboard_id: Dashboard identifier.
            db: Optional async session.

        Returns:
            list[str]: List of available metric names.
        """
        actual_db = db
        if actual_db is None:
            async with get_session() as session:
                return await self._get_available_metrics_with_session(
                    dashboard_id, session
                )
        return await self._get_available_metrics_with_session(dashboard_id, actual_db)

    async def _get_available_metrics_with_session(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> list[str]:
        """Internal method to get available metrics."""
        graphs = await self.graph_repo.get_by_dashboard_id(dashboard_id, db)

        metrics: set[str] = set()
        for graph in graphs:
            if graph.metrics:
                metrics.update(graph.metrics)

        return list(metrics)

    async def get_available_dimensions(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[str]:
        """Get available dimensions for dashboard.

        Args:
            dashboard_id: Dashboard identifier.
            db: Optional async session.

        Returns:
            list[str]: List of available dimension names.
        """
        actual_db = db
        if actual_db is None:
            async with get_session() as session:
                return await self._get_available_dimensions_with_session(
                    dashboard_id, session
                )
        return await self._get_available_dimensions_with_session(
            dashboard_id, actual_db
        )

    async def _get_available_dimensions_with_session(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> list[str]:
        """Internal method to get available dimensions."""
        graphs = await self.graph_repo.get_by_dashboard_id(dashboard_id, db)

        dimensions: set[str] = set()
        for graph in graphs:
            if graph.dimensions:
                dimensions.update(graph.dimensions)

        return list(dimensions)

    # --- Helper methods ---

    def _validate_mime_type(self, content_type: str | None) -> None:
        """Validate MIME-type of uploaded file."""
        if content_type is None:
            logger.warning("MIME-type not specified, skipping check")
            return

        allowed_mime_types = MimeTypeEnum.allowed_values()
        if content_type not in allowed_mime_types:
            logger.error(
                "Invalid MIME-type: %s. Allowed: %s",
                content_type,
                allowed_mime_types,
            )
            raise ValueError(f"Invalid MIME-type: {content_type}")

    def _validate_file(
        self,
        filename: str | None,
        file_content: bytes,
        content_type: str | None,
    ) -> None:
        """Validate uploaded file.

        Checks file content, MIME type, format, and size limits.
        """
        # 1. Check file content is not empty
        if not file_content:
            raise ValueError("File content is empty")

        # 2. Check MIME-type
        self._validate_mime_type(content_type)

        # 3. Check file format
        config = get_config()
        allowed_extensions = config.allowed_file_types
        if filename and not any(
            filename.lower().endswith(ext.lower()) for ext in allowed_extensions
        ):
            logger.error(
                "Invalid file format: %s. Allowed: %s",
                filename,
                allowed_extensions,
            )
            raise ValueError(
                f"Invalid file format: '{filename}'. "
                f"Allowed formats: {', '.join(allowed_extensions)}"
            )

        # 4. Check file size
        if len(file_content) > self._max_file_size:
            logger.error(
                "File exceeds maximum size: %s (%d > %d)",
                filename,
                len(file_content),
                self._max_file_size,
            )
            raise ValueError(
                f"File '{filename}' exceeds maximum size "
                f"({len(file_content)} > {self._max_file_size} bytes)"
            )

        logger.info(
            "File validated successfully: %s (%d bytes)", filename, len(file_content)
        )

    async def trigger_processing(
        self,
        task_id: UUID,
        dashboard_id: UUID,
        user_id: UUID,
        processing_config: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> ProcessingStatusResponse:
        """Trigger processing of uploaded file.

        Args:
            task_id: Processing log ID (used to find the file).
            dashboard_id: Target dashboard ID.
            user_id: User ID for permission check.
            processing_config: Optional processing configuration.
            db: Optional database session.

        Returns:
            ProcessingStatusResponse with current status.
        """
        if db is None:
            async with get_session() as session:
                return await self.trigger_processing(
                    task_id, dashboard_id, user_id, processing_config, session
                )

        # Check user permissions
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id,
                dashboard_id=dashboard_id,
                required_permission="edit",
                db=db,
            )
            if not has_access:
                logger.warning(
                    "Processing denied: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                raise PermissionError("No permission to process data for this dashboard")

        # Get the processing log
        log = await self.log_repo.get_by_id(task_id, db)
        if log is None:
            raise ValueError(f"Processing task {task_id} not found")

        # Find the file in temp directory
        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))
        
        if not task_files:
            raise ValueError(f"File for task {task_id} not found in temp directory")

        file_path = str(task_files[0])
        
        # Update log status to processing
        await self.log_repo.update_status(
            log_id=task_id,
            status=ProcessingStatus.PROCESSING,
            message="Processing triggered manually",
            db=db,
        )
        await db.commit()

        # Enqueue job
        from mkobi.workers.data_worker import process_csv_background
        
        mode = "overwrite"  # Default mode for manual trigger
        await enqueue_job(
            process_csv_background,
            file_path=file_path,
            dashboard_id=str(dashboard_id),
            task_id=str(task_id),
            log_id=str(task_id),
            mode=mode,
        )

        logger.info(
            "Processing triggered: task_id=%s, dashboard_id=%s",
            task_id,
            dashboard_id,
        )

        return ProcessingStatusResponse(
            task_id=task_id,
            filename=log.message or "unknown",
            dashboard_id=dashboard_id,
            status=ProcessingStatus.PROCESSING,
            progress=0,
            message="Processing triggered",
        )

    async def get_processing_status(
        self,
        task_id: UUID,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> ProcessingStatusResponse:
        """Get processing status.

        Args:
            task_id: Processing log ID.
            user_id: User ID for permission check.
            db: Optional database session.

        Returns:
            ProcessingStatusResponse with current status.
        """
        if db is None:
            async with get_session() as session:
                return await self.get_processing_status(task_id, user_id, session)

        # Get the processing log
        log = await self.log_repo.get_by_id(task_id, db)
        if log is None:
            raise ValueError(f"Processing task {task_id} not found")

        # Check user permissions (user should have view access to the dashboard)
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id,
                dashboard_id=log.dashboard_id,
                required_permission="view",
                db=db,
            )
            if not has_access:
                raise PermissionError("No permission to view this dashboard")

        return ProcessingStatusResponse(
            task_id=task_id,
            filename=log.message or "unknown",
            dashboard_id=log.dashboard_id,
            status=log.status,
            progress=50 if log.status == ProcessingStatus.PROCESSING else 100 if log.status == ProcessingStatus.SUCCESS else 0,
            message=log.message,
            started_at=log.started_at,
            completed_at=log.finished_at,
        )

    async def get_processing_result(
        self,
        task_id: UUID,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> ProcessingResult:
        """Get processing result.

        Args:
            task_id: Processing log ID.
            user_id: User ID for permission check.
            db: Optional database session.

        Returns:
            ProcessingResult with processed data.
        """
        if db is None:
            async with get_session() as session:
                return await self.get_processing_result(task_id, user_id, session)

        # Get the processing log
        log = await self.log_repo.get_by_id(task_id, db)
        if log is None:
            raise ValueError(f"Processing task {task_id} not found")

        # Check user permissions
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id,
                dashboard_id=log.dashboard_id,
                required_permission="view",
                db=db,
            )
            if not has_access:
                raise PermissionError("No permission to view this dashboard")

        # Check if processing is complete
        if log.status != ProcessingStatus.SUCCESS:
            return ProcessingResult(
                success=False,
                task_id=task_id,
                dashboard_id=log.dashboard_id,
                rows_processed=0,
                message=f"Processing not complete. Status: {log.status}",
            )

        # Get aggregated data for the dashboard
        # For simplicity, get data for the first graph
        graphs = await self.graph_repo.get_by_dashboard_id(log.dashboard_id, db)
        
        rows_processed = 0
        if graphs:
            graph_id = graphs[0].id
            agg_data = await self.agg_repo.get_by_graph_id(graph_id, db)
            rows_processed = len(agg_data) if agg_data else 0

        return ProcessingResult(
            success=True,
            task_id=task_id,
            dashboard_id=log.dashboard_id,
            rows_processed=rows_processed,
            message="Processing completed successfully",
        )

# Cleanup function
def cleanup_task_files(task_id: uuid.UUID) -> None:
    """Delete temporary task files."""
    logger.info("Cleaning up task files: task_id=%s", task_id)
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)

    # Fix: handle both .csv and .csv.gz files
    csv_files = list(upload_dir.glob(f"*{task_id}*.csv*"))

    for file_path in csv_files:
        try:
            file_path.unlink()
            logger.info("File deleted: %s", file_path)
        except Exception as e:
            logger.error("Error deleting file %s: %s", file_path, e)
