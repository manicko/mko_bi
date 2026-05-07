"""Data processing service.

Provides business logic for uploading, processing and tracking
data processing status for dashboards.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.config import get_config
from mkobi.core.permissions import check_dashboard_access
from mkobi.core.redis_client import get_redis_client
from mkobi.core.security import RateLimiter
from mkobi.core.task_queue import enqueue_job
from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.db.session import get_session
from mkobi.interfaces.service_interfaces import IDataService
from mkobi.models.data import (
    ProcessingConfig,
    ProcessingResult,
    ProcessingResultData,
    ProcessingStatusResponse,
    UploadResponse,
)
from mkobi.models.enums import MimeTypeEnum, ProcessingStatus, UploadMode
from mkobi.services.processing_log_service import get_by_id

logger = logging.getLogger(__name__)


class DataService(IDataService):
    """Data service class for processing data."""

    def __init__(self, db: AsyncSession | None = None):
        """Initialize service."""
        self._db = db
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
        db: AsyncSession | None = None,
    ) -> UploadResponse:
        """Process uploaded file and save aggregates."""
        actual_db = db or self._db
        if actual_db is None:
            async with get_session() as session:
                return await self._process_upload_with_session(
                    file_content,
                    dashboard_id,
                    user_id,
                    filename,
                    content_type,
                    session,
                )
        return await self._process_upload_with_session(
            file_content,
            dashboard_id,
            user_id,
            filename,
            content_type,
            actual_db,
        )

    async def _process_upload_with_session(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None,
        filename: str | None,
        content_type: str | None,
        db: AsyncSession,
    ) -> UploadResponse:
        """Internal method for processing with session."""
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

        # Generate task ID
        task_id = uuid.uuid4()

        # Save file to temporary directory
        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_ext = ".csv.gz" if filename and filename.endswith(".gz") else ".csv"
        temp_file_path = upload_dir / f"{task_id}{file_ext}"

        try:
            temp_file_path.write_bytes(file_content)
            logger.info("File saved: path=%s", temp_file_path)
        except Exception as e:
            logger.error("File save error: %s", e)
            raise

        # Create processing log entry
        log_repo = ProcessingLogRepository()
        log = await log_repo.create_log(
            db=db,
            dashboard_id=dashboard_id,
            status=ProcessingStatus.STARTED,
            message="Upload started",
        )
        await db.commit()

        # Enqueue job
        await enqueue_job(
            "process_upload_task",
            file_path=str(temp_file_path),
            dashboard_id=str(dashboard_id),
            task_id=str(task_id),
            log_id=str(log.id),
        )

        logger.info(
            "Task enqueued: task_id=%s, dashboard_id=%s",
            task_id,
            dashboard_id,
        )

        return UploadResponse(
            task_id=task_id,
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
        actual_db = db or self._db
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
        agg_repo = AggregatedDataRepository()
        records = await agg_repo.get_by_graph(
            db=db,
            graph_id=graph_id,
        )

        result = []
        for record in records:
            result.append(
                ProcessingResultData(
                    dims=record.dims,
                    metrics=record.metrics,
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
        actual_db = db or self._db
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
        from mkobi.db.repositories.graph_repo import GraphRepository

        repo = GraphRepository(db)
        graphs = await repo.get_by_dashboard(dashboard_id)

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
        actual_db = db or self._db
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
        from mkobi.db.repositories.graph_repo import GraphRepository

        repo = GraphRepository(db)
        graphs = await repo.get_by_dashboard(dashboard_id)

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
        """Validate uploaded file."""
        # 1. Check MIME-type
        self._validate_mime_type(content_type)

        # 2. Check file format
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

        # 3. Check file size
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


# --- Backward compatibility functions ---


async def process_upload(
    file_content: bytes,
    dashboard_id: UUID,
    user_id: UUID | None = None,
    filename: str | None = None,
    content_type: str | None = None,
    db: AsyncSession | None = None,
) -> UploadResponse:
    """Backward compatibility wrapper."""
    service = DataService(db=db)
    return await service.process_upload(
        file_content,
        dashboard_id,
        user_id,
        filename,
        content_type,
    )


async def upload_file(
    filename: str | None,
    file_path: Path,
    content_type: str | None,
    dashboard_id: UUID,
    user_id: UUID,
    mode: UploadMode,
    db: AsyncSession | None = None,
) -> UploadResponse:
    """Backward compatibility wrapper for uploading file."""
    service = DataService(db=db)
    file_content = Path(file_path).read_bytes()
    return await service.process_upload(
        file_content=file_content,
        dashboard_id=dashboard_id,
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        db=db,
    )


async def trigger_processing(
    task_id: UUID,
    dashboard_id: UUID,
    user_id: UUID,
    processing_config: ProcessingConfig | None = None,
    db: AsyncSession | None = None,
) -> ProcessingStatusResponse:
    """Backward compatibility wrapper for triggering processing."""

    log = await get_by_id(task_id, db)
    if not log:
        raise ValueError(f"Task {task_id} not found")
    return ProcessingStatusResponse(
        task_id=task_id,
        status=log.status,
        message=log.message,
    )


async def get_processing_status(
    task_id: UUID,
    user_id: UUID,
    db: AsyncSession | None = None,
) -> ProcessingStatusResponse:
    """Backward compatibility wrapper for getting processing status."""

    log = await get_by_id(task_id, db)
    if not log:
        raise ValueError(f"Task {task_id} not found")
    return ProcessingStatusResponse(
        task_id=task_id,
        status=log.status,
        message=log.message,
    )


async def get_processing_result(
    task_id: UUID,
    user_id: UUID,
    db: AsyncSession | None = None,
) -> ProcessingResult:
    """Backward compatibility wrapper for getting processing result."""

    log = await get_by_id(task_id, db)
    if not log:
        raise ValueError(f"Task {task_id} not found")

    # Get aggregated data
    agg_repo = AggregatedDataRepository()
    records = await agg_repo.get_by_dashboard(
        db=db,
        dashboard_id=log.dashboard_id,
    )

    return ProcessingResult(
        success=True,
        task_id=task_id,
        dashboard_id=log.dashboard_id,
        rows_processed=len(records),
        message=log.message,
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
