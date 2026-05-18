"""Data processing service.

Provides business logic for uploading, processing and tracking
data processing status for dashboards.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.config import get_config
from mkobi.core.logging_config import get_logger
from mkobi.core.permissions import check_dashboard_access, PermissionError
from mkobi.core.redis_client import get_redis_client
from mkobi.core.security import RateLimiter
from mkobi.db.session import get_session
from mkobi.interfaces.repository_interfaces import (
    IAggregatedDataRepository,
    IGraphRepository,
    IProcessingLogRepository,
)
from mkobi.interfaces.service_interfaces import IDataService
from mkobi.models.data import ProcessingResultData, ProcessingResult, ProcessingStatusResponse, UploadResponse
from mkobi.models.enums import ProcessingStatus, UploadMode
from mkobi.services.file_processing import (
    enqueue_processing_job,
    find_task_file,
    get_and_validate_processing_log,
    process_upload_with_session,
)

logger = get_logger(__name__)


class DataService(IDataService):
    """Data service class for processing data."""

    def __init__(
        self,
        agg_repo: IAggregatedDataRepository,
        log_repo: IProcessingLogRepository,
        graph_repo: IGraphRepository,
    ) -> None:
        """Initialize service with injected repositories."""
        self.agg_repo = agg_repo
        self.log_repo = log_repo
        self.graph_repo = graph_repo
        self._upload_rate_limiter: RateLimiter | None = None
        self._rate_limiter_healthy: bool = False
        config = get_config()
        try:
            self._upload_rate_limiter = RateLimiter(
                get_redis_client(),
                fail_closed=config.rate_limiter_fail_closed,
            )
            self._rate_limiter_healthy = True
        except Exception as e:
            logger.error(
                "Rate limiter disabled due to Redis unavailability: %s", e,
            )
            if config.rate_limiter_fail_closed:
                logger.critical(
                    "Rate limiter FAIL-CLOSED mode enabled - uploads will be rejected"
                )
            else:
                logger.warning(
                    "Rate limiter disabled - uploads will not be rate-limited"
                )
            self._upload_rate_limiter = None
        self._upload_rate_limit = 10
        self._upload_rate_period = 60
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
                return await self._execute_upload(
                    file_content, dashboard_id, user_id,
                    filename, content_type, mode, session,
                )
        return await self._execute_upload(
            file_content, dashboard_id, user_id,
            filename, content_type, mode, actual_db,
        )

    async def _execute_upload(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None,
        filename: str | None,
        content_type: str | None,
        mode: UploadMode,
        db: AsyncSession,
    ) -> UploadResponse:
        """Execute upload with permission check and file processing."""
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
                    user_id, dashboard_id,
                )
                raise PermissionError(
                    "No permission to process data for this dashboard"
                )

        log_id = await process_upload_with_session(
            file_content=file_content,
            dashboard_id=dashboard_id,
            log_repo=self.log_repo,
            filename=filename,
            content_type=content_type,
            mode=mode,
            max_file_size=self._max_file_size,
            db=db,
        )

        return UploadResponse(
            task_id=log_id,
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
        if db is None:
            async with get_session() as session:
                return await self._get_aggregated_data_with_session(
                    dashboard_id, graph_id, session,
                )
        return await self._get_aggregated_data_with_session(
            dashboard_id, graph_id, db,
        )

    async def _get_aggregated_data_with_session(
        self, dashboard_id: UUID, graph_id: UUID, db: AsyncSession,
    ) -> list[ProcessingResultData]:
        """Get aggregated data for a graph within a dashboard."""
        records = await self.agg_repo.get_by_graph_id(
            graph_id, db, dashboard_id=dashboard_id,
        )
        return [
            ProcessingResultData(
                columns=list(record.dims.keys()) + list(record.metrics.keys()),
                rows=1,
                dashboard_id=record.dashboard_id,
                preview=[{**record.dims, **record.metrics}],
            )
            for record in records
        ]

    async def get_available_metrics(
        self, dashboard_id: UUID, db: AsyncSession | None = None,
    ) -> list[str]:
        """Get available metrics for dashboard."""
        if db is None:
            async with get_session() as session:
                return await self._get_available_metrics_with_session(dashboard_id, session)
        return await self._get_available_metrics_with_session(dashboard_id, db)

    async def _get_available_metrics_with_session(
        self, dashboard_id: UUID, db: AsyncSession,
    ) -> list[str]:
        """Collect metric names from all graphs in a dashboard."""
        graphs = await self.graph_repo.get_by_dashboard_id(dashboard_id, db)
        metrics: set[str] = set()
        for graph in graphs:
            if graph.metrics:
                metrics.update(graph.metrics)
        return list(metrics)

    async def get_available_dimensions(
        self, dashboard_id: UUID, db: AsyncSession | None = None,
    ) -> list[str]:
        """Get available dimensions for dashboard."""
        if db is None:
            async with get_session() as session:
                return await self._get_available_dimensions_with_session(dashboard_id, session)
        return await self._get_available_dimensions_with_session(dashboard_id, db)

    async def _get_available_dimensions_with_session(
        self, dashboard_id: UUID, db: AsyncSession,
    ) -> list[str]:
        """Collect dimension names from all graphs in a dashboard."""
        graphs = await self.graph_repo.get_by_dashboard_id(dashboard_id, db)
        dimensions: set[str] = set()
        for graph in graphs:
            if graph.dimensions:
                dimensions.update(graph.dimensions)
        return list(dimensions)

    async def trigger_processing(
        self,
        task_id: UUID,
        dashboard_id: UUID,
        user_id: UUID,
        processing_config: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> ProcessingStatusResponse:
        """Trigger processing of uploaded file."""
        if db is None:
            async with get_session() as session:
                return await self.trigger_processing(
                    task_id, dashboard_id, user_id, processing_config, session
                )
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id, dashboard_id=dashboard_id,
                required_permission="edit", db=db,
            )
            if not has_access:
                logger.warning(
                    "Processing denied: user_id=%s, dashboard_id=%s",
                    user_id, dashboard_id,
                )
                raise PermissionError("No permission to process data for this dashboard")
        log = await get_and_validate_processing_log(
            task_id=task_id, dashboard_id=dashboard_id,
            log_repo=self.log_repo, db=db,
        )
        file_path = find_task_file(task_id)
        await self.log_repo.update_status(
            log_id=task_id, status=ProcessingStatus.PROCESSING,
            message="Processing triggered manually", db=db,
        )
        await db.commit()
        await enqueue_processing_job(
            file_path=file_path, dashboard_id=dashboard_id,
            task_id=task_id, mode="overwrite",
        )
        logger.info(
            "Processing triggered: task_id=%s, dashboard_id=%s",
            task_id, dashboard_id,
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
        """Get processing status."""
        if db is None:
            async with get_session() as session:
                return await self.get_processing_status(task_id, user_id, session)
        log = await self.log_repo.get_by_id(task_id, db)
        if log is None:
            raise ValueError(f"Processing task {task_id} not found")
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id, dashboard_id=log.dashboard_id,
                required_permission="view", db=db,
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
        """Get processing result."""
        if db is None:
            async with get_session() as session:
                return await self.get_processing_result(task_id, user_id, session)
        log = await self.log_repo.get_by_id(task_id, db)
        if log is None:
            raise ValueError(f"Processing task {task_id} not found")
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id, dashboard_id=log.dashboard_id,
                required_permission="view", db=db,
            )
            if not has_access:
                raise PermissionError("No permission to view this dashboard")
        if log.status != ProcessingStatus.SUCCESS:
            return ProcessingResult(
                success=False, task_id=task_id,
                dashboard_id=log.dashboard_id, rows_processed=0,
                message=f"Processing not complete. Status: {log.status}",
            )
        graphs = await self.graph_repo.get_by_dashboard_id(log.dashboard_id, db)
        rows_processed = 0
        if graphs:
            agg_data = await self.agg_repo.get_by_graph_id(graphs[0].id, db)
            rows_processed = len(agg_data) if agg_data else 0
        return ProcessingResult(
            success=True, task_id=task_id,
            dashboard_id=log.dashboard_id, rows_processed=rows_processed,
            message="Processing completed successfully",
        )

