"""Temporary file cleanup utilities.

Provides functions for cleaning up task-specific and stale temporary files
from the upload directory. Also provides cleanup for old processing logs.
"""

import uuid
from datetime import datetime, UTC, timedelta
from pathlib import Path

from sqlalchemy import delete

from mkobi.config import get_config
from mkobi.core.logging_config import get_logger
from mkobi.db.models.processing_logs import ProcessingLog
from mkobi.db.session import get_session
from mkobi.models.enums import ProcessingStatus

logger = get_logger(__name__)


def cleanup_task_files(task_id: uuid.UUID) -> None:
    """Delete temporary task files.

    Removes all files in the upload temp directory that match the given task ID.

    Args:
        task_id: The processing log ID whose temp files should be removed.
    """
    logger.info("Cleaning up task files: task_id=%s", task_id)
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)

    # Handle both .csv and .csv.gz files
    csv_files = list(upload_dir.glob(f"*{task_id}*.csv*"))

    for file_path in csv_files:
        try:
            file_path.unlink()
            logger.info("File deleted: %s", file_path)
        except Exception as e:
            logger.error("Error deleting file %s: %s", file_path, e)


def cleanup_stale_temp_files(max_age_hours: int | None = None) -> int:
    """Delete stale temporary files older than the specified threshold.

    This function is designed to be called on application startup to clean up
    orphaned temp files from previous runs (e.g., worker crashes, container restarts).

    Args:
        max_age_hours: Maximum age of files in hours before deletion.
            If None, uses the configured threshold (default 24 hours).

    Returns:
        int: Number of files deleted.
    """
    from time import time

    config = get_config()
    threshold_hours = (
        max_age_hours if max_age_hours is not None else config.stale_file_threshold_hours
    )
    upload_dir = Path(config.upload_temp_dir)

    if threshold_hours <= 0:
        logger.warning("Invalid threshold %d hours, skipping cleanup", threshold_hours)
        return 0

    if not upload_dir.exists():
        logger.info("Upload temp directory does not exist: %s", upload_dir)
        return 0

    # Calculate cutoff time (seconds since epoch)
    cutoff_seconds = threshold_hours * 3600
    current_time = time()
    deleted_count = 0

    # Find all CSV files in upload directory
    csv_files = list(upload_dir.glob("*.csv*"))

    for file_path in csv_files:
        try:
            # Check file modification time
            mtime = file_path.stat().st_mtime
            file_age_seconds = current_time - mtime

            if file_age_seconds > cutoff_seconds:
                file_path.unlink()
                logger.info(
                    "Deleted stale temp file: %s (age: %.1f hours)",
                    file_path,
                    file_age_seconds / 3600,
                )
                deleted_count += 1
        except Exception as e:
            logger.error("Error processing file %s: %s", file_path, e)

    if deleted_count > 0:
        logger.info("Cleaned up %d stale temp files", deleted_count)

    return deleted_count


async def cleanup_old_processing_logs(retention_days: int | None = None) -> int:
    """Delete processing logs in terminal states older than the retention period.

    This function is designed to be called periodically (e.g., via a background task)
    to clean up completed and failed processing logs that are no longer needed for
    display or monitoring.

    Args:
        retention_days: Number of days to keep logs. If None, uses the configured
            logs_retention_days setting (default 30 days).

    Returns:
        int: Number of deleted log entries.
    """
    config = get_config()
    days = retention_days if retention_days is not None else config.logs_retention_days
    cutoff = datetime.now(UTC) - timedelta(days=days)

    async with get_session() as db:
        async with db.begin():
            stmt = (
                delete(ProcessingLog)
                .where(
                    ProcessingLog.status.in_(
                        [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
                    ),
                    ProcessingLog.finished_at < cutoff,
                )
            )
            result = await db.execute(stmt)
            count = result.rowcount or 0

    if count > 0:
        logger.info("Cleaned up %d old processing logs (retention=%dd)", count, days)

    return count
