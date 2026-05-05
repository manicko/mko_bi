"""File utilities for the application.

Provides file operations using platformdirs for temp files and validation helpers.
"""

import logging
import shutil
from pathlib import Path
from uuid import UUID

import platformdirs

from mko_bi.models.enums import FileExtensionEnum, MimeTypeEnum

logger = logging.getLogger(__name__)


def get_user_temp_dir(user_id: UUID | str) -> Path:
    """Get temporary directory for a user using platformdirs.

    Args:
        user_id: User identifier (UUID or string).

    Returns:
        Path: Temporary directory path for the user.
    """
    cache_dir = Path(platformdirs.user_cache_dir("mko_bi", appauthor=False))
    temp_dir = cache_dir / "uploads" / str(user_id)
    temp_dir.mkdir(parents=True, exist_ok=True)
    logger.info("User temp directory: user_id=%s, path=%s", user_id, temp_dir)
    return temp_dir


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Clean up temporary directory after processing.

    Args:
        temp_dir: Path to temporary directory to delete.
    """
    try:
        if temp_dir.exists() and temp_dir.is_dir():
            shutil.rmtree(temp_dir)
            logger.info("Temp directory cleaned up: path=%s", temp_dir)
    except OSError as e:
        logger.error("Failed to cleanup temp directory %s: %s", temp_dir, e)


def validate_file_extension(filename: str) -> bool:
    """Validate file extension for upload.

    Args:
        filename: Name of the file to validate.

    Returns:
        bool: True if extension is allowed, False otherwise.
    """
    allowed_extensions = {ext.value for ext in FileExtensionEnum}
    file_ext = Path(filename).suffix.lower()
    # Handle .csv.gz case
    if file_ext == ".gz":
        stem = Path(filename).stem
        if Path(stem).suffix.lower() == ".csv":
            file_ext = "csv.gz"
    is_valid = file_ext in allowed_extensions
    logger.info("File extension validation: filename=%s, valid=%s", filename, is_valid)
    return is_valid


def validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type for upload.

    Args:
        mime_type: MIME type to validate.

    Returns:
        bool: True if MIME type is allowed, False otherwise.
    """
    allowed_mime_types = {mime.value for mime in MimeTypeEnum}
    is_valid = mime_type.lower() in allowed_mime_types
    logger.info("MIME type validation: mime_type=%s, valid=%s", mime_type, is_valid)
    return is_valid
