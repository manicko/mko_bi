from mkobi.models.enums import (  # noqa: F401
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

# Aliases for backwards compatibility
UserRoleEnum = UserRole
PermissionEnum = DashboardPermission
GraphTypeEnum = GraphType
FilterTypeEnum = FilterType
ProcessingStatusEnum = ProcessingStatus  # For backwards compatibility

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
