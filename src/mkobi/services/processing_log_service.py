"""Processing log service.

Provides business logic for creating, updating and reading processing logs.

All methods are async and comply with task 011_processing_logs.md requirements.
"""

import logging
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.session import get_session
from mkobi.interfaces.repository_interfaces import IProcessingLogRepository
from mkobi.interfaces.service_interfaces import IProcessingLogService
from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead

logger = logging.getLogger(__name__)


class ProcessingLogService(IProcessingLogService):
    """Service for processing log business logic.

    Provides methods for managing processing log lifecycle.
    Called from DataPipeline at each processing stage.
    """

    def __init__(self, log_repo: IProcessingLogRepository) -> None:
        """Initialize service with injected repository.

        Args:
            log_repo: Processing log repository instance.
        """
        self.log_repo = log_repo
        logger.info("ProcessingLogService initialized with injected repository")

    async def create_processing_log(
        self,
        dashboard_id: UUID,
        status: str,
        message: str | None = None,
        db: AsyncSession | None = None,
    ) -> ProcessingLogRead:
        """Create processing log entry."""
        if db is None:
            async with get_session() as db:
                return await self.create_processing_log(
                    dashboard_id, status, message, db
                )

        log = await self.log_repo.create_log(dashboard_id, ProcessingStatus(status), message, db)
        return cast(ProcessingLogRead, ProcessingLogRead.model_validate(log))

    async def get_processing_logs_by_dashboard(
        self, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> list[ProcessingLogRead]:
        """Get processing logs by dashboard ID."""
        if db is None:
            async with get_session() as db:
                return await self.get_processing_logs_by_dashboard(dashboard_id, db)

        logs = await self.log_repo.get_by_dashboard(dashboard_id, db)
        return cast(list[ProcessingLogRead], logs)  # Already returns list[ProcessingLogRead]

    async def get_processing_logs_by_status(
        self, status: str, db: AsyncSession | None = None
    ) -> list[ProcessingLogRead]:
        """Get processing logs by status."""
        if db is None:
            async with get_session() as db:
                return await self.get_processing_logs_by_status(status, db)

        filters = ProcessingLogFilter(status=ProcessingStatus(status))
        logs = await self.log_repo.get_filtered(filters, db)
        return cast(list[ProcessingLogRead], logs)  # Already returns list[ProcessingLogRead]

    async def update_processing_log(
        self,
        log_id: UUID,
        status: str | None,
        message: str | None,
        finished_at: str | None,  # Ignored, calculated from status
        db: AsyncSession | None = None,
    ) -> ProcessingLogRead | None:
        """Update processing log entry."""
        if db is None:
            async with get_session() as db:
                return await self.update_processing_log(
                    log_id, status, message, finished_at, db
                )

        await self.log_repo.update_status(
            log_id,
            ProcessingStatus(status) if status else ProcessingStatus.STARTED,
            message,
            db,
        )

        log = await self.log_repo.get_latest_by_dashboard(log_id, db)
        return log  # Already returns ProcessingLogRead | None

    async def delete_processing_log(
        self, log_id: UUID, db: AsyncSession | None = None
    ) -> bool:
        """Delete processing log entry."""
        if db is None:
            async with get_session() as db:
                return await self.delete_processing_log(log_id, db)

        # Get the log first to find its dashboard_id
        log = await self.log_repo.get_by_id(log_id, db)
        if log is None:
            return False

        # Delete all logs for the dashboard
        return await self.log_repo.delete(log.dashboard_id, db)

    async def create_started_log(
        self, dashboard_id: UUID | None, db: AsyncSession
    ) -> ProcessingLogRead:
        """Create log with STARTED status."""
        logger.info("Creating STARTED log: dashboard_id=%s", dashboard_id)
        log = await self.log_repo.create_log(
            dashboard_id, ProcessingStatus.STARTED, "Processing started", db
        )
        return cast(ProcessingLogRead, ProcessingLogRead.model_validate(log))

    async def update_to_uploaded(
        self, log_id: UUID, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Update log status to UPLOADED."""
        logger.info("Updating log to UPLOADED: log_id=%s", log_id)
        await self.log_repo.update_status(
            log_id, ProcessingStatus.UPLOADED, "File uploaded successfully", db
        )
        log = await self.log_repo.get_latest_by_dashboard(log_id, db)
        return log

    async def update_to_processing(
        self, log_id: UUID, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Update log status to PROCESSING."""
        logger.info("Updating log to PROCESSING: log_id=%s", log_id)
        await self.log_repo.update_status(
            log_id, ProcessingStatus.PROCESSING, "Processing data", db
        )
        log = await self.log_repo.get_latest_by_dashboard(log_id, db)
        return log

    async def update_to_success(
        self, log_id: UUID, message: str | None, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Update log status to SUCCESS."""
        logger.info("Updating log to SUCCESS: log_id=%s", log_id)
        await self.log_repo.update_status(
            log_id,
            ProcessingStatus.SUCCESS,
            message or "Processing completed successfully",
            db,
        )
        log = await self.log_repo.get_by_id(log_id, db)
        return log

    async def update_to_failed(
        self, log_id: UUID, error: str, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Update log status to FAILED."""
        logger.error("Updating log to FAILED: log_id=%s, error=%s", log_id, error)
        await self.log_repo.update_status(log_id, ProcessingStatus.FAILED, error, db)
        log = await self.log_repo.get_by_id(log_id, db)
        return log

    async def get_filtered(
        self, filters: ProcessingLogFilter, db: AsyncSession
    ) -> list[ProcessingLogRead]:
        """Get filtered processing logs."""
        logger.info("Getting filtered logs: filters=%s", filters)
        result = await self.log_repo.get_filtered(filters, db)
        return cast(list[ProcessingLogRead], result)



