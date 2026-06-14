"""Repository for processing log operations.

Provides methods for working with data processing logs.
Implements IProcessingLogRepository interface.
"""

import logging
from datetime import datetime, UTC, time
from uuid import UUID
from typing import cast

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mkobi.db.models import processing_logs as processing_log_model
from mkobi.db.models.processing_logs import ProcessingLog
from mkobi.interfaces.repository_interfaces import IProcessingLogRepository
from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead

logger = logging.getLogger(__name__)


class ProcessingLogRepository(IProcessingLogRepository):
    """Repository for processing log operations.

    Provides methods for creating, reading and updating
    processing logs in the database.
    Implements IProcessingLogRepository interface.
    """
    async def create_log(
        self,
        dashboard_id: UUID | None,
        status: ProcessingStatus,
        message: str | None,
        db: AsyncSession,
    ) -> ProcessingLog:
        """Create new processing log.

        Args:
            dashboard_id: Dashboard identifier (optional).
            status: Processing status.
            message: Error or success message (optional).
            db: Async database session.

        Returns:
            Created processing log model.
        """
        try:
            log_data = {
                "dashboard_id": dashboard_id,
                "status": status,
                "message": message,
                "started_at": datetime.now(UTC),
            }
            log_obj = processing_log_model.ProcessingLog(**log_data)
            db.add(log_obj)
            await db.flush()
            await db.refresh(log_obj)
            logger.info(
                "Processing log created: id=%s, dashboard_id=%s, status=%s",
                log_obj.id,
                dashboard_id,
                status,
            )
            return log_obj
        except SQLAlchemyError as e:
            logger.error("Error creating log: %s", e)
            raise
    async def update_status(
        self,
        log_id: UUID,
        status: ProcessingStatus,
        message: str | None,
        db: AsyncSession,
        finished_at: datetime | None = None,
        error_code: str | None = None,
    ) -> None:
        """Update processing log status.

        Args:
            log_id: Log identifier.
            status: New status.
            message: Message (optional).
            db: Async database session.
            finished_at: Explicit finished_at timestamp (optional).
            error_code: Error code for RFC 7807 error reporting (optional).
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            )
            log_obj = result.scalar_one_or_none()
            if not log_obj:
                logger.warning("Log not found for update: id=%s", log_id)
                return

            log_obj.status = status
            if message is not None:
                log_obj.message = message
            if error_code is not None:
                log_obj.error_code = error_code

            # Set finished_at on completed or failed status, or use explicit value
            if finished_at is not None:
                log_obj.finished_at = finished_at
            elif status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED):
                log_obj.finished_at = datetime.now(UTC)

            await db.flush()
            logger.info("Log status updated: id=%s, status=%s", log_id, status)
        except SQLAlchemyError as e:
            logger.error("Error updating log status id=%s: %s", log_id, e)
            raise
    async def get_by_dashboard(
        self,
        dashboard_id: UUID | None,
        db: AsyncSession,
    ) -> list[ProcessingLogRead]:
        """Get all processing logs for dashboard.

        Args:
            dashboard_id: Dashboard identifier (can be None).
            db: Async database session.

        Returns:
            List of processing logs for dashboard as Pydantic models.
        """
        try:
            query = (
                select(processing_log_model.ProcessingLog)
                .options(selectinload(processing_log_model.ProcessingLog.dashboard))
            )
            if dashboard_id is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.dashboard_id == dashboard_id
                )
            else:
                query = query.where(
                    processing_log_model.ProcessingLog.dashboard_id.is_(None)
                )
            query = query.order_by(processing_log_model.ProcessingLog.started_at.desc())
            result = await db.execute(query)
            logs = list(result.scalars().all())
            logger.info(
                "Logs retrieved for dashboard_id=%s, count: %s",
                dashboard_id,
                len(logs),
            )
            result_logs: list[ProcessingLogRead] = []
            for log in logs:
                log_read = ProcessingLogRead.model_validate(log)
                log_read.dashboard_name = log.dashboard.name if log.dashboard else None
                result_logs.append(log_read)
            return result_logs
        except SQLAlchemyError as e:
            logger.error("Error getting logs dashboard_id=%s: %s", dashboard_id, e)
            raise
    async def get_filtered(
        self,
        filters: ProcessingLogFilter,
        db: AsyncSession,
    ) -> list[ProcessingLogRead]:
        """Get processing logs with filtering.

        Args:
            filters: Filter parameters.
            db: Async database session.

        Returns:
            List of processing logs as Pydantic models.
        """
        try:
            query = (
                select(processing_log_model.ProcessingLog)
                .options(selectinload(processing_log_model.ProcessingLog.dashboard))
            )

            if filters.dashboard_id is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.dashboard_id
                    == filters.dashboard_id
                )

            if filters.status is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.status == filters.status
                )

            if filters.date_from is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.started_at >= filters.date_from
                )

            if filters.date_to is not None:
                # Convert datetime to end of day for inclusive filtering
                end_of_day = datetime.combine(filters.date_to.date(), time(23, 59, 59, 999999))
                query = query.where(
                    processing_log_model.ProcessingLog.started_at <= end_of_day
                )

            query = query.order_by(processing_log_model.ProcessingLog.started_at.desc())

            if filters.skip > 0:
                query = query.offset(filters.skip)

            if filters.limit > 0:
                query = query.limit(filters.limit)

            result = await db.execute(query)
            logs = list(result.scalars().all())
            logger.info(
                "Filtered logs retrieved, count: %s",
                len(logs),
            )
            result_logs: list[ProcessingLogRead] = []
            for log in logs:
                log_read = ProcessingLogRead.model_validate(log)
                log_read.dashboard_name = log.dashboard.name if log.dashboard else None
                result_logs.append(log_read)
            return result_logs
        except SQLAlchemyError as e:
            logger.error("Error getting filtered logs: %s", e)
            raise
    async def get_latest_by_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> ProcessingLogRead | None:
        """Get latest processing log for dashboard.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.

        Returns:
            Latest processing log or None if not found.
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog)
                .options(selectinload(processing_log_model.ProcessingLog.dashboard))
                .where(processing_log_model.ProcessingLog.dashboard_id == dashboard_id)
                .order_by(processing_log_model.ProcessingLog.started_at.desc())
                .limit(1)
            )
            log = result.scalar_one_or_none()
            if log:
                logger.info(
                    "Latest log retrieved for dashboard_id=%s: id=%s",
                    dashboard_id,
                    log.id,
                )
                log_read: ProcessingLogRead = ProcessingLogRead.model_validate(log)
                log_read.dashboard_name = log.dashboard.name if log.dashboard else None
                return cast(ProcessingLogRead | None, log_read)
            else:
                logger.info("No logs found for dashboard_id=%s", dashboard_id)
                return None
        except SQLAlchemyError as e:
            logger.error(
                "Error getting latest log dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    async def get_by_id(
        self,
        log_id: UUID,
        db: AsyncSession,
    ) -> ProcessingLogRead | None:
        """Get log by ID.

        Args:
            log_id: Log identifier.
            db: Async database session.

        Returns:
            Log model or None if not found.
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog)
                .options(selectinload(processing_log_model.ProcessingLog.dashboard))
                .where(processing_log_model.ProcessingLog.id == log_id)
            )
            log = result.scalar_one_or_none()
            if log:
                logger.info("Log retrieved: id=%s", log_id)
                log_read: ProcessingLogRead = ProcessingLogRead.model_validate(log)
                log_read.dashboard_name = log.dashboard.name if log.dashboard else None
                return cast(ProcessingLogRead | None, log_read)
            else:
                logger.info("Log not found: id=%s", log_id)
                return None
        except SQLAlchemyError as e:
            logger.error("Error getting log id=%s: %s", log_id, e)
            raise

    async def delete(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """Delete processing logs by dashboard ID.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.

        Returns:
            True if logs were deleted, False if none found.
        """
        try:
            stmt = delete(processing_log_model.ProcessingLog).where(
                processing_log_model.ProcessingLog.dashboard_id == dashboard_id
            )
            result = await db.execute(stmt)
            rowcount: int = cast(int, result.rowcount)
            deleted = rowcount > 0
            await db.flush()
            if deleted:
                logger.info("Logs deleted for dashboard_id=%s", dashboard_id)
            else:
                logger.warning("No logs found to delete for dashboard_id=%s", dashboard_id)
            return deleted
        except SQLAlchemyError as e:
            logger.error("Error deleting logs dashboard_id=%s: %s", dashboard_id, e)
            raise

    async def delete_old_logs(
        self,
        cutoff: datetime,
        db: AsyncSession,
    ) -> int:
        """Delete processing logs in terminal states older than cutoff.

        Args:
            cutoff: Datetime cutoff - logs with finished_at before this are deleted.
            db: Async database session.

        Returns:
            int: Number of deleted log entries.
        """
        try:
            stmt = (
                delete(processing_log_model.ProcessingLog)
                .where(
                    processing_log_model.ProcessingLog.status.in_(
                        [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
                    ),
                    processing_log_model.ProcessingLog.finished_at < cutoff,
                )
            )
            result = await db.execute(stmt)
            count = result.rowcount or 0
            await db.flush()
            if count > 0:
                logger.info("Deleted %d old processing logs (cutoff=%s)", count, cutoff)
            return count
        except SQLAlchemyError as e:
            logger.error("Error deleting old logs: %s", e)
            raise
