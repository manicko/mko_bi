"""Time utilities for the application.

Provides time operations using datetime for consistent time handling.
"""

import logging
from datetime import datetime, timedelta, timezone as tz, UTC

from mkobi.utils.exceptions import HTTPException

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
            HTTPException: If parsing fails.

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
            raise HTTPException(
                status_code=400,
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
            HTTPException: If parsing fails.

        Example:
            >>> utils = TimeUtils()
            >>> dt = utils.parse_iso("2026-04-27T12:00:00+00:00")
        """
        try:
            return datetime.fromisoformat(date_string)
        except ValueError as e:
            logger.error("Failed to parse ISO date string '%s': %s", date_string, e)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ISO date format: {date_string}",
            ) from e

    def add(
        self,
        dt: datetime,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> datetime:
        """Add time delta to datetime.

        Args:
            dt: Base datetime.
            days: Days to add. Defaults to 0.
            hours: Hours to add. Defaults to 0.
            minutes: Minutes to add. Defaults to 0.
            seconds: Seconds to add. Defaults to 0.

        Returns:
            datetime: New datetime with added delta.

        Example:
            >>> utils = TimeUtils()
            >>> future = utils.add(datetime.now(), days=1, hours=2)
        """
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return dt + delta

    def subtract(
        self,
        dt: datetime,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> datetime:
        """Subtract time delta from datetime.

        Args:
            dt: Base datetime.
            days: Days to subtract. Defaults to 0.
            hours: Hours to subtract. Defaults to 0.
            minutes: Minutes to subtract. Defaults to 0.
            seconds: Seconds to subtract. Defaults to 0.

        Returns:
            datetime: New datetime with subtracted delta.

        Example:
            >>> utils = TimeUtils()
            >>> past = utils.subtract(datetime.now(), days=1)
        """
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return dt - delta

    def diff(
        self,
        dt1: datetime,
        dt2: datetime,
        unit: str = "seconds",
    ) -> float:
        """Calculate difference between two datetimes.

        Args:
            dt1: First datetime.
            dt2: Second datetime.
            unit: Unit for result ('seconds', 'minutes', 'hours', 'days').
                  Defaults to "seconds".

        Returns:
            float: Difference in specified unit.

        Raises:
            ValueError: If unit is not supported.

        Example:
            >>> utils = TimeUtils()
            >>> diff = utils.diff(dt1, dt2, "hours")
        """
        delta = dt2 - dt1
        total_seconds = delta.total_seconds()

        if unit == "seconds":
            return total_seconds
        elif unit == "minutes":
            return total_seconds / 60
        elif unit == "hours":
            return total_seconds / 3600
        elif unit == "days":
            return total_seconds / 86400
        else:
            raise ValueError(f"Unsupported unit: {unit}")

    def start_of_day(self, dt: datetime | None = None) -> datetime:
        """Get start of day (00:00:00) for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: Start of day with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> start = utils.start_of_day()
        """
        if dt is None:
            dt = self.now()
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def end_of_day(self, dt: datetime | None = None) -> datetime:
        """Get end of day (23:59:59.999999) for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: End of day with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> end = utils.end_of_day()
        """
        if dt is None:
            dt = self.now()
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    def timestamp(self, dt: datetime | None = None) -> float:
        """Get Unix timestamp for datetime.

        Args:
            dt: Datetime to convert. Defaults to current time.

        Returns:
            float: Unix timestamp.

        Example:
            >>> utils = TimeUtils()
            >>> ts = utils.timestamp()
        """
        if dt is None:
            dt = self.now()
        return dt.timestamp()

    def from_timestamp(self, timestamp: float) -> datetime:
        """Convert Unix timestamp to datetime.

        Args:
            timestamp: Unix timestamp.

        Returns:
            datetime: Datetime with instance timezone.

        Example:
            >>> utils = TimeUtils()
            >>> dt = utils.from_timestamp(1640995200.0)
        """
        return datetime.fromtimestamp(timestamp, tz=self.timezone)

    def is_expired(
        self,
        dt: datetime,
        expiration_seconds: int,
    ) -> bool:
        """Check if datetime has expired.

        Args:
            dt: Datetime to check.
            expiration_seconds: Expiration time in seconds.

        Returns:
            bool: True if expired, False otherwise.

        Example:
            >>> utils = TimeUtils()
            >>> if utils.is_expired(token_time, 3600):
            ...     print("Token expired")
        """
        now = self.now()
        return (now - dt).total_seconds() > expiration_seconds

    def format_for_display(self, dt: datetime) -> str:
        """Format datetime for human-readable display.

        Args:
            dt: Datetime to format.

        Returns:
            str: Human-readable datetime string.

        Example:
            >>> utils = TimeUtils()
            >>> utils.format_for_display(datetime.now())
            '2026-04-27 12:00:00 UTC'
        """
        return f"{self.format(dt)} {dt.tzinfo}"

    def to_utc(self, dt: datetime) -> datetime:
        """Convert datetime to UTC.

        Args:
            dt: Datetime to convert.

        Returns:
            datetime: Datetime in UTC.

        Example:
            >>> utils = TimeUtils()
            >>> utc_dt = utils.to_utc(datetime.now())
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.timezone)
        return dt.astimezone(UTC)

    def to_timezone(self, dt: datetime, target_tz: tz) -> datetime:
        """Convert datetime to target timezone.

        Args:
            dt: Datetime to convert.
            target_tz: Target timezone.

        Returns:
            datetime: Datetime in target timezone.

        Example:
            >>> utils = TimeUtils()
            >>> tz_obj = tz(timedelta(hours=3))
            >>> local_dt = utils.to_timezone(datetime.now(), tz_obj)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.timezone)
        return dt.astimezone(target_tz)

    def get_week_start(self, dt: datetime | None = None) -> datetime:
        """Get start of week (Monday) for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: Start of week with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> week_start = utils.get_week_start()
        """
        if dt is None:
            dt = self.now()
        start = dt - timedelta(days=dt.weekday())
        return self.start_of_day(start)

    def get_week_end(self, dt: datetime | None = None) -> datetime:
        """Get end of week (Sunday) for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: End of week with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> week_end = utils.get_week_end()
        """
        if dt is None:
            dt = self.now()
        end = dt + timedelta(days=6 - dt.weekday())
        return self.end_of_day(end)

    def get_month_start(self, dt: datetime | None = None) -> datetime:
        """Get start of month for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: Start of month with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> month_start = utils.get_month_start()
        """
        if dt is None:
            dt = self.now()
        return self.start_of_day(dt.replace(day=1))

    def get_month_end(self, dt: datetime | None = None) -> datetime:
        """Get end of month for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: End of month with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> month_end = utils.get_month_end()
        """
        if dt is None:
            dt = self.now()
        next_month = dt.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        return self.end_of_day(last_day)

    def get_year_start(self, dt: datetime | None = None) -> datetime:
        """Get start of year for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: Start of year with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> year_start = utils.get_year_start()
        """
        if dt is None:
            dt = self.now()
        return self.start_of_day(dt.replace(month=1, day=1))

    def get_year_end(self, dt: datetime | None = None) -> datetime:
        """Get end of year for given datetime.

        Args:
            dt: Datetime to use. Defaults to current time.

        Returns:
            datetime: End of year with timezone info.

        Example:
            >>> utils = TimeUtils()
            >>> year_end = utils.get_year_end()
        """
        if dt is None:
            dt = self.now()
        return self.end_of_day(dt.replace(month=12, day=31))

    def is_business_day(self, dt: datetime | None = None) -> bool:
        """Check if date is a business day (Monday-Friday).

        Args:
            dt: Datetime to check. Defaults to current time.

        Returns:
            bool: True if business day, False otherwise.

        Example:
            >>> utils = TimeUtils()
            >>> if utils.is_business_day():
            ...     print("Business day")
        """
        if dt is None:
            dt = self.now()
        return dt.weekday() < 5

    def add_business_days(
        self,
        dt: datetime,
        days: int,
    ) -> datetime:
        """Add business days to datetime.

        Args:
            dt: Base datetime.
            days: Business days to add (can be negative).

        Returns:
            datetime: New datetime with added business days.

        Example:
            >>> utils = TimeUtils()
            >>> future = utils.add_business_days(datetime.now(), 5)
        """
        current = dt
        days_added = 0
        direction = 1 if days > 0 else -1

        while days_added < abs(days):
            current = current + timedelta(days=direction)
            if self.is_business_day(current):
                days_added += 1

        return current
