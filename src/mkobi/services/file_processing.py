"""File processing logic for data upload.

Provides validation, upload processing, and task management functions
extracted from DataService to improve modularity and testability.
"""

from pathlib import Path
from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.config import get_config
from mkobi.core.logging_config import get_logger
from mkobi.core.task_queue import enqueue_job
from mkobi.data.loaders.loader import detect_file_type
from mkobi.models.enums import FileExtensionEnum, MimeTypeEnum, ProcessingStatus, UploadMode

logger = get_logger(__name__)


def validate_mime_type(content_type: str | None) -> None:
    """Validate MIME-type of uploaded file.

    Args:
        content_type: MIME type string from upload header.

    Raises:
        ValueError: If MIME type is None or not in the allowed list.
    """
    if content_type is None:
        raise ValueError("Content-Type header is required")

    allowed_mime_types = MimeTypeEnum.allowed_values()
    if content_type not in allowed_mime_types:
        logger.error(
            "Invalid MIME-type: %s. Allowed: %s",
            content_type,
            allowed_mime_types,
        )
        raise ValueError(f"Invalid MIME-type: {content_type}")


def validate_file(
    file_path: Path,
    filename: str | None,
    content_type: str | None,
    max_file_size: int,
) -> int:
    """Validate uploaded file.

    Checks file content, MIME type, format, and size limits.

    Args:
        file_path: Path to the uploaded file.
        filename: Original filename from upload.
        content_type: MIME type from upload header.
        max_file_size: Maximum allowed file size in bytes.

    Returns:
        int: The file size in bytes.

    Raises:
        ValueError: If any validation check fails.
    """
    # 1. Check file exists and get size
    if not file_path.exists():
        raise ValueError("File not found")

    file_size = file_path.stat().st_size

    # Check file content is not empty
    if file_size == 0:
        raise ValueError("File content is empty")

    # 2. Check MIME-type
    validate_mime_type(content_type)

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
    if file_size > max_file_size:
        logger.error(
            "File exceeds maximum size: %s (%d > %d)",
            filename,
            file_size,
            max_file_size,
        )
        raise ValueError(
            f"File '{filename}' exceeds maximum size "
            f"({file_size} > {max_file_size} bytes)"
        )

    logger.info(
        "File validated successfully: %s (%d bytes)", filename, file_size
    )
    return file_size


async def process_upload_with_session(
    file_path: Path,
    dashboard_id: UUID,
    log_repo: Any,
    filename: str | None,
    content_type: str | None,
    mode: UploadMode,
    max_file_size: int,
    db: AsyncSession,
    processing_config: dict[str, Any] | None = None,
) -> UUID:
    """Process uploaded file with an active session.

    Validates, renames to final location with log ID, creates processing log,
    and enqueues the background job.

    Args:
        file_path: Path to the uploaded file (already streamed to temp).
        dashboard_id: Target dashboard ID.
        log_repo: Processing log repository.
        filename: Original filename.
        content_type: MIME type of uploaded file.
        mode: Upload mode (OVERWRITE clears old data, APPEND keeps it).
        max_file_size: Maximum allowed file size in bytes.
        db: Database session.
        processing_config: Optional processing configuration for transformations.

    Returns:
        UUID: The processing log ID (task ID).

    Raises:
        ValueError: If file validation fails.
        OSError: If file cannot be moved to final location.
    """
    # Validate file at temp path
    file_size = validate_file(file_path, filename, content_type, max_file_size)

    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Detect file type using enum-based function
    file_ext = (
        ".csv.gz"
        if filename and detect_file_type(filename) == FileExtensionEnum.CSV_GZ
        else ".csv"
    )

    # Create processing log entry with STARTED status first
    log = await log_repo.create_log(
        db=db,
        dashboard_id=dashboard_id,
        status=ProcessingStatus.STARTED,
        message=f"Upload started with mode={mode}",
    )
    await db.flush()

    logger.info(
        "File validated for processing: size=%d, mode=%s",
        file_size, mode
    )

    # Update status to UPLOADED after validation
    await log_repo.update_status(
        log_id=log.id,
        status=ProcessingStatus.UPLOADED,
        message=f"File uploaded successfully, awaiting processing. mode={mode}",
        db=db,
    )
    await db.commit()

    # Move file to final location with log ID as filename AFTER successful commit
    final_file_path = upload_dir / f"{log.id}{file_ext}"
    try:
        file_path.replace(final_file_path)
    except Exception:
        logger.error(
            "Failed to move file to final path after commit, log_id=%s",
            log.id,
            exc_info=True
        )
        raise

    logger.info(
        "File moved to final location: path=%s, size=%d, mode=%s",
        final_file_path, file_size, mode
    )

    # Enqueue job with processing config - use log.id as the identifier
    await enqueue_processing_job(
        file_path=str(final_file_path),
        dashboard_id=dashboard_id,
        task_id=log.id,
        mode=str(mode),
        processing_config=processing_config,
    )

    logger.info(
        "Task enqueued: task_id=%s, dashboard_id=%s, mode=%s, config=%s",
        log.id,
        dashboard_id,
        mode,
        "present" if processing_config else "none",
    )

    return cast(UUID, log.id)


def find_task_file(task_id: UUID) -> str:
    """Find temporary file for a processing task.

    Args:
        task_id: Processing log ID.

    Returns:
        str: Path to the task's temporary file.

    Raises:
        ValueError: If no file is found for the task.
    """
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))

    if not task_files:
        raise ValueError(f"File for task {task_id} not found in temp directory")

    return str(task_files[0])


async def get_and_validate_processing_log(
    task_id: UUID,
    dashboard_id: UUID,
    log_repo: Any,
    db: Any,
) -> Any:
    """Retrieve and validate a processing log entry.

    Args:
        task_id: Processing log ID.
        dashboard_id: Expected dashboard ID.
        log_repo: Processing log repository.
        db: Database session.

    Returns:
        The processing log entry.

    Raises:
        ValueError: If task not found or doesn't belong to dashboard.
    """
    log = await log_repo.get_by_id(task_id, db)
    if log is None:
        raise ValueError(f"Processing task {task_id} not found")

    if log.dashboard_id is not None and log.dashboard_id != dashboard_id:
        logger.warning(
            "Task ownership mismatch: task_id=%s, task_dashboard_id=%s, requested_dashboard_id=%s",
            task_id,
            log.dashboard_id,
            dashboard_id,
        )
        raise ValueError(
            f"Task {task_id} does not belong to dashboard {dashboard_id}"
        )

    return log


async def enqueue_processing_job(
    file_path: str,
    dashboard_id: UUID,
    task_id: UUID,
    mode: str = "overwrite",
    processing_config: dict[str, Any] | None = None,
) -> None:
    """Enqueue a background processing job.

    Args:
        file_path: Path to the CSV file to process.
        dashboard_id: Target dashboard ID.
        task_id: Processing log ID.
        mode: Upload mode (overwrite or append).
        processing_config: Processing configuration dictionary for transformations.
    """
    from mkobi.workers.data_worker import process_csv_background

    await enqueue_job(
        process_csv_background,
        file_path=file_path,
        dashboard_id=str(dashboard_id),
        task_id=str(task_id),
        log_id=str(task_id),
        mode=mode,
        processing_config_dict=processing_config,
    )