"""Enumerations for application components.

Uses StrEnum for type safety and easy serialization.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """System user roles."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DashboardPermission(StrEnum):
    """Dashboard access levels."""

    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class GraphType(StrEnum):
    """Chart types."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"


class FilterType(StrEnum):
    """Filter types."""

    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"


class RegistrationStatus(StrEnum):
    """Registration request statuses."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UploadMode(StrEnum):
    """Data upload modes."""

    OVERWRITE = "overwrite"
    APPEND = "append"


class ProcessingStatus(StrEnum):
    """Data processing statuses."""

    STARTED = "started"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    COMPLETED = "completed"


class EnvironmentEnum(StrEnum):
    """Application environments."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class MimeTypeEnum(StrEnum):
    """Allowed MIME types for uploaded files."""

    TEXT_CSV = "text/csv"
    APPLICATION_GZIP = "application/gzip"
    APPLICATION_X_GZIP = "application/x-gzip"

    @classmethod
    def allowed_values(cls) -> list[str]:
        """Returns list of allowed MIME types."""
        return [member.value for member in cls]


class FileExtensionEnum(StrEnum):
    """Allowed file extensions."""

    CSV = "csv"
    CSV_GZ = "csv.gz"

    @classmethod
    def allowed_values(cls) -> list[str]:
        """Returns list of allowed file extensions."""
        return [member.value for member in cls]


# Additional enums used in dashboards


class ButtonVariant(StrEnum):
    """Button style variants."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    LIGHT = "light"
    DARK = "dark"


class ComponentSize(StrEnum):
    """Component sizes."""

    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"


class OrientationEnum(StrEnum):
    """Chart orientation."""

    VERTICAL = "v"
    HORIZONTAL = "h"


class BarmodeEnum(StrEnum):
    """Bar chart display mode."""

    GROUP = "group"
    STACK = "stack"


class YoyModeEnum(StrEnum):
    """Year-over-year comparison display mode."""

    ABSOLUTE = "absolute"
    PERCENT = "percent"


class AggregationFunctionEnum(StrEnum):
    """Data aggregation functions."""

    SUM = "sum"
    MEAN = "mean"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"
    FIRST = "first"
    LAST = "last"


class FilterOperatorEnum(StrEnum):
    """Data filtering operators."""

    EQ = "=="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
