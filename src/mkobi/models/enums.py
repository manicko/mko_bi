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
    COMPLETED = "completed"
    FAILED = "failed"


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


class ErrorCode(StrEnum):
    """Centralized error codes for all API errors.

    Categories organized by functional area. All codes use UPPER_SNAKE_CASE
    convention for type safety and easy serialization.
    """

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Authentication errors
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    INVALID_TOKEN = "INVALID_TOKEN"

    # Authorization errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCESS_DENIED = "ACCESS_DENIED"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    DASHBOARD_NOT_FOUND = "DASHBOARD_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    GRAPH_NOT_FOUND = "GRAPH_NOT_FOUND"
    FILTER_NOT_FOUND = "FILTER_NOT_FOUND"
    LAYOUT_NOT_FOUND = "LAYOUT_NOT_FOUND"
    PROCESSING_CONFIG_NOT_FOUND = "PROCESSING_CONFIG_NOT_FOUND"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"

    # File errors
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"

    # Conflict errors
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    FILTER_ALREADY_BOUND = "FILTER_ALREADY_BOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"

    # Processing errors
    PROCESSING_FAILED = "PROCESSING_FAILED"
    PROCESSING_IN_PROGRESS = "PROCESSING_IN_PROGRESS"
