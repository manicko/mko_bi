import logging

from mkobi.models.enums import (  # noqa: F401, E402
    AggregationFunctionEnum,
    BarmodeEnum,
    ButtonVariant,
    ComponentSize,
    DashboardPermission,
    EnvironmentEnum,
    FileExtensionEnum,
    FilterOperatorEnum,
    FilterType,
    GraphType,
    MimeTypeEnum,
    OrientationEnum,
    ProcessingStatus,
    RegistrationStatus,
    UploadMode,
    UserRole,
    YoyModeEnum,
)

logger = logging.getLogger(__name__)

# Aliases for backwards compatibility
UserRoleEnum = UserRole
PermissionEnum = DashboardPermission
GraphTypeEnum = GraphType
FilterTypeEnum = FilterType
ProcessingStatusEnum = ProcessingStatus

__all__ = [
    "AggregationFunctionEnum",
    "BarmodeEnum",
    "ButtonVariant",
    "ComponentSize",
    "DashboardPermission",
    "EnvironmentEnum",
    "FileExtensionEnum",
    "FilterOperatorEnum",
    "FilterType",
    "FilterTypeEnum",
    "GraphType",
    "GraphTypeEnum",
    "MimeTypeEnum",
    "OrientationEnum",
    "ProcessingStatus",
    "ProcessingStatusEnum",
    "RegistrationStatus",
    "UploadMode",
    "UserRole",
    "UserRoleEnum",
    "YoyModeEnum",
]
