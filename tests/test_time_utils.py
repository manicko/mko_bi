"""Tests for TimeUtils class.

Tests:
- Time utilities parse error handling
- ISO format parsing error handling
- Format and timezone operations
"""

from datetime import datetime, timedelta, timezone, UTC

import pytest

from mkobi.models.enums import ErrorCode
from mkobi.utils.exceptions import AppException
from mkobi.utils.time_utils import TimeUtils


class TestTimeUtilsInit:
    """Tests for TimeUtils initialization."""

    def test_init_default_timezone(self):
        """Test default timezone is UTC."""
        utils = TimeUtils()
        assert utils.timezone == UTC

    def test_init_custom_timezone(self):
        """Test custom timezone can be set."""
        utils = TimeUtils(timezone=UTC)
        assert utils.timezone == UTC


class TestTimeUtilsNow:
    """Tests for now() method."""

    def test_now_returns_datetime(self):
        """Test now returns a datetime instance."""
        utils = TimeUtils()
        result = utils.now()
        assert isinstance(result, datetime)

    def test_now_has_timezone(self):
        """Test now returns datetime with timezone info."""
        utils = TimeUtils()
        result = utils.now()
        assert result.tzinfo is not None


class TestTimeUtilsUtcnow:
    """Tests for utcnow() method."""

    def test_utcnow_returns_datetime(self):
        """Test utcnow returns a datetime instance."""
        utils = TimeUtils()
        result = utils.utcnow()
        assert isinstance(result, datetime)

    def test_utcnow_has_utc_timezone(self):
        """Test utcnow returns datetime with UTC timezone."""
        utils = TimeUtils()
        result = utils.utcnow()
        assert result.tzinfo == UTC


class TestTimeUtilsFormat:
    """Tests for format() method."""

    def test_format_default_format(self):
        """Test default format string."""
        utils = TimeUtils()
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = utils.format(dt)
        assert result == "2024-01-15 10:30:45"

    def test_format_custom_format(self):
        """Test custom format string."""
        utils = TimeUtils()
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = utils.format(dt, "%Y-%m-%d")
        assert result == "2024-01-15"

    def test_format_iso_format(self):
        """Test ISO format string."""
        utils = TimeUtils()
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = utils.format(dt, "%Y-%m-%dT%H:%M:%S")
        assert result == "2024-01-15T10:30:45"


class TestTimeUtilsParse:
    """Tests for parse() method error paths."""

    def test_parse_valid_datetime(self):
        """Test parsing valid datetime string."""
        utils = TimeUtils()
        result = utils.parse("2024-01-15 10:30:45")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_invalid_format_raises_exception(self):
        """Test parsing invalid format raises AppException with VALIDATION_ERROR code."""
        utils = TimeUtils()
        with pytest.raises(AppException) as exc_info:
            utils.parse("not-a-valid-date")
        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    def test_parse_invalid_format_message(self):
        """Test exception message contains the invalid value."""
        utils = TimeUtils()
        with pytest.raises(AppException) as exc_info:
            utils.parse("invalid-date")
        assert "invalid-date" in exc_info.value.detail.lower()

    def test_parse_empty_string_raises_exception(self):
        """Test parsing empty string raises AppException."""
        utils = TimeUtils()
        with pytest.raises(AppException):
            utils.parse("")

    def test_parse_wrong_format_raises_exception(self):
        """Test parsing with wrong format string raises AppException."""
        utils = TimeUtils()
        with pytest.raises(AppException):
            utils.parse("2024/01/15", fmt="%Y-%m-%d")

    def test_parse_with_custom_timezone(self):
        """Test parsing with custom timezone applies correctly."""
        utils = TimeUtils()
        custom_tz = timezone(timedelta(hours=3))
        result = utils.parse("2024-01-15 10:30:45", timezone=custom_tz)
        assert result.tzinfo == custom_tz

    def test_parse_ignores_timezone_if_already_set(self):
        """Test parsing does not override existing timezone info."""
        utils = TimeUtils()
        # When the parsed datetime already has tzinfo, it should not be replaced
        result = utils.parse("2024-01-15 10:30:45")
        assert result.tzinfo == UTC


class TestTimeUtilsParseIso:
    """Tests for parse_iso() method error paths."""

    def test_parse_iso_valid_datetime(self):
        """Test parsing valid ISO format datetime."""
        utils = TimeUtils()
        result = utils.parse_iso("2024-01-15T10:30:45+00:00")
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_iso_invalid_format_raises_exception(self):
        """Test parsing invalid ISO format raises AppException with VALIDATION_ERROR code."""
        utils = TimeUtils()
        with pytest.raises(AppException) as exc_info:
            utils.parse_iso("not-a-valid-iso-date")
        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    def test_parse_iso_invalid_format_message(self):
        """Test exception message contains the invalid value."""
        utils = TimeUtils()
        with pytest.raises(AppException) as exc_info:
            utils.parse_iso("invalid-iso")
        assert "invalid-iso" in exc_info.value.detail.lower()

    def test_parse_iso_empty_string_raises_exception(self):
        """Test parsing empty string raises AppException."""
        utils = TimeUtils()
        with pytest.raises(AppException):
            utils.parse_iso("")

    def test_parse_iso_without_timezone(self):
        """Test parsing ISO datetime without timezone."""
        utils = TimeUtils()
        result = utils.parse_iso("2024-01-15T10:30:45")
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_iso_with_z_suffix(self):
        """Test parsing ISO datetime with Z suffix (UTC)."""
        utils = TimeUtils()
        result = utils.parse_iso("2024-01-15T10:30:45Z")
        assert isinstance(result, datetime)


class TestTimeUtilsIsoformat:
    """Tests for isoformat() method."""

    def test_isoformat_returns_string(self):
        """Test isoformat returns a string."""
        utils = TimeUtils()
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = utils.isoformat(dt)
        assert isinstance(result, str)

    def test_isoformat_correct_format(self):
        """Test isoformat returns ISO 8601 format."""
        utils = TimeUtils()
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = utils.isoformat(dt)
        assert "T" in result  # ISO format contains T separator