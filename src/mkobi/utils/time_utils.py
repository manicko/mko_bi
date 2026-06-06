"""Time utilities for the application.

Provides time operations using datetime for consistent time handling.
"""

import logging
from datetime import datetime, timezone as tz, UTC

from mkobi.models.enums import ErrorCode
from mkobi.utils.exceptions import AppException

logger = logging.getLogger(__name__)


class TimeUtils:
    """Utility class for time operations.

    Provides methods for common time operations including getting current time,
    formatting, parsing, and time calculations using datetime.

    Attributes:
        timezone: Default timezone for time operations.
    """

    def __init__(self, timezone: tz | None = None) -> None:
        """Initialize TimeUtils.

        Args:
            timezone: Default timezone for time operations. If None, uses UTC.

        Example:
            >>> utils = TimeUtils()  # Uses UTC
            >>> utils = TimeUtils(timezone=tz(timedelta(hours=3)))
        """
        self.timezone = timezone if timezone else UTC

    def now(self) -> datetime:
        """Get current time in the default timezone.

        Returns:
            datetime: Current time with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> current = utils.now()
        """
        return datetime.now(self.timezone)

    def utcnow(self) -> datetime:
        """Get current UTC time.

        Returns:
            datetime: Current UTC time with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> utc_time = utils.utcnow()
        """
        return datetime.now(UTC)

    def format(self, dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime to string.

        Args:
            dt: Datetime to format.
            fmt: Format string. Defaults to "%Y-%m-%d %H:%M:%S".

        Returns:
            str: Formatted datetime string.

        Example:
            >>> utils = TimeUtils()
            >>> utils.format(datetime.now(), "%Y-%m-%d")
            '2026-04-27'
        """
        return dt.strftime(fmt)

    def parse(
        self,
        date_string: str,
        fmt: str = "%Y-%m-%d %H:%M:%S",
        timezone: tz | None = None,
    ) -> datetime:
        """Parse string to datetime.

        Args:
            date_string: String to parse.
            fmt: Format string. Defaults to "%Y-%m-%d %H:%M:%S".
            timezone: Optional timezone to apply. Defaults to instance timezone.

        Returns:
            datetime: Parsed datetime with timezone info.

        Raises:
            AppException: If parsing fails.

        Example:
            >>> utils = TimeUtils()
            >>> dt = utils.parse("2026-04-27 12:00:00")
        """
        try:
            dt = datetime.strptime(date_string, fmt)
            tz_to_use = timezone if timezone else self.timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz_to_use)
            return dt
        except ValueError as e:
            logger.error("Failed to parse date string '%s': %s", date_string, e)
            raise AppException(
                code=ErrorCode.VALIDATION_ERROR,
                detail=f"Invalid date format: {date_string}",
            ) from e

    def isoformat(self, dt: datetime) -> str:
        """Format datetime to ISO 8601 string.

        Args:
            dt: Datetime to format.

        Returns:
            str: ISO 8601 formatted string.

        Example:
            >>> utils = TimeUtils()
            >>> utils.isoformat(datetime.now())
            '2026-04-27T12:00:00+00:00'
        """
        return dt.isoformat()

    def parse_iso(self, date_string: str) -> datetime:
        """Parse ISO 8601 string to datetime.

        Args:
            date_string: ISO 8601 string to parse.

        Returns:
            datetime: Parsed datetime with timezone info.

        Raises:
            AppException: If parsing fails.

        Example:
            >>> utils = TimeUtils()
            >>> dt = utils.parse_iso("2026-04-27T12:00:00+00:00")
        """
        try:
            return datetime.fromisoformat(date_string)
        except ValueError as e:
            logger.error("Failed to parse ISO date string '%s': %s", date_string, e)
            raise AppException(
                code=ErrorCode.VALIDATION_ERROR,
                detail=f"Invalid ISO date format: {date_string}",
            ) from e
