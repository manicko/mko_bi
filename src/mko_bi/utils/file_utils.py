"""File utilities for the application.

Provides file operations using pathlib for safe and consistent file handling.
"""

import logging
from pathlib import Path

from mko_bi.utils.exceptions import HTTPException

logger = logging.getLogger(__name__)


class FileUtils:
    """Utility class for file operations.

    Provides methods for common file operations including upload, save,
    delete, and existence checks using pathlib for safe path handling.

    Attributes:
        base_path: Base directory for file operations.
    """

    def __init__(self, base_path: str | Path | None = None) -> None:
        """Initialize FileUtils.

        Args:
            base_path: Base directory for file operations. If None, uses current directory.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> utils = FileUtils()  # Uses current directory
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload(self, file_content: bytes, filename: str, subdir: str | None = None) -> Path:
        """Upload and save file content.

        Saves file content to the specified location. Creates subdirectory if needed.

        Args:
            file_content: Raw bytes of the file to upload.
            filename: Name of the file (including extension).
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            Path: Full path to the saved file.

        Raises:
            HTTPException: If file save fails.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> path = utils.upload(b"file content", "data.csv.gz")
        """
        try:
            target_dir = self.base_path
            if subdir:
                target_dir = target_dir / subdir
                target_dir.mkdir(parents=True, exist_ok=True)

            file_path = target_dir / filename
            file_path.write_bytes(file_content)
            logger.info("File uploaded successfully: %s", file_path)
            return file_path
        except OSError as e:
            logger.error("Failed to upload file %s: %s", filename, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {filename}",
            ) from e

    def save(self, content: str | bytes, filename: str, subdir: str | None = None) -> Path:
        """Save content to a file.

        Saves text or binary content to the specified file.

        Args:
            content: Content to save (text or bytes).
            filename: Name of the file (including extension).
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            Path: Full path to the saved file.

        Raises:
            HTTPException: If file save fails.

        Example:
            >>> utils = FileUtils("/tmp/data")
            >>> path = utils.save("text content", "output.txt")
        """
        try:
            target_dir = self.base_path
            if subdir:
                target_dir = target_dir / subdir
                target_dir.mkdir(parents=True, exist_ok=True)

            file_path = target_dir / filename
            if isinstance(content, str):
                file_path.write_text(content, encoding="utf-8")
            else:
                file_path.write_bytes(content)
            logger.info("File saved successfully: %s", file_path)
            return file_path
        except OSError as e:
            logger.error("Failed to save file %s: %s", filename, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {filename}",
            ) from e

    def delete(self, filename: str, subdir: str | None = None) -> bool:
        """Delete a file.

        Removes the specified file from the filesystem.

        Args:
            filename: Name of the file to delete.
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            bool: True if file was deleted, False if file did not exist.

        Raises:
            HTTPException: If deletion fails due to permissions or other errors.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> utils.delete("old_file.csv.gz")
        """
        try:
            target_dir = self.base_path
            if subdir:
                target_dir = target_dir / subdir

            file_path = target_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info("File deleted successfully: %s", file_path)
                return True
            logger.warning("File not found for deletion: %s", file_path)
            return False
        except OSError as e:
            logger.error("Failed to delete file %s: %s", filename, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file: {filename}",
            ) from e

    def exists(self, filename: str, subdir: str | None = None) -> bool:
        """Check if a file exists.

        Args:
            filename: Name of the file to check.
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            bool: True if file exists, False otherwise.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> if utils.exists("data.csv.gz"):
            ...     print("File exists")
        """
        target_dir = self.base_path
        if subdir:
            target_dir = target_dir / subdir
        file_path = target_dir / filename
        return file_path.exists()

    def read(self, filename: str, subdir: str | None = None) -> bytes:
        """Read file content as bytes.

        Args:
            filename: Name of the file to read.
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            bytes: File content.

        Raises:
            HTTPException: If file does not exist or cannot be read.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> content = utils.read("data.csv.gz")
        """
        try:
            target_dir = self.base_path
            if subdir:
                target_dir = target_dir / subdir

            file_path = target_dir / filename
            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {filename}",
                )
            return file_path.read_bytes()
        except HTTPException:
            raise
        except OSError as e:
            logger.error("Failed to read file %s: %s", filename, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {filename}",
            ) from e

    def read_text(self, filename: str, subdir: str | None = None) -> str:
        """Read file content as text.

        Args:
            filename: Name of the file to read.
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            str: File content as text.

        Raises:
            HTTPException: If file does not exist or cannot be read.

        Example:
            >>> utils = FileUtils("/tmp/data")
            >>> content = utils.read_text("output.txt")
        """
        try:
            target_dir = self.base_path
            if subdir:
                target_dir = target_dir / subdir

            file_path = target_dir / filename
            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {filename}",
                )
            return file_path.read_text(encoding="utf-8")
        except HTTPException:
            raise
        except OSError as e:
            logger.error("Failed to read text file %s: %s", filename, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {filename}",
            ) from e

    def list_files(self, subdir: str | None = None, pattern: str = "*") -> list[Path]:
        """List files in directory.

        Args:
            subdir: Optional subdirectory under base_path. Defaults to None.
            pattern: Glob pattern for filtering files. Defaults to "*".

        Returns:
            list[Path]: List of file paths matching the pattern.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> files = utils.list_files(pattern="*.csv.gz")
        """
        target_dir = self.base_path
        if subdir:
            target_dir = target_dir / subdir
        return list(target_dir.glob(pattern))

    def get_size(self, filename: str, subdir: str | None = None) -> int:
        """Get file size in bytes.

        Args:
            filename: Name of the file.
            subdir: Optional subdirectory under base_path. Defaults to None.

        Returns:
            int: File size in bytes.

        Raises:
            HTTPException: If file does not exist.

        Example:
            >>> utils = FileUtils("/tmp/uploads")
            >>> size = utils.get_size("data.csv.gz")
        """
        target_dir = self.base_path
        if subdir:
            target_dir = target_dir / subdir

        file_path = target_dir / filename
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename}",
            )
        return file_path.stat().st_size
