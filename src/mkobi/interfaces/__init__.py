"""Abstract interfaces for dependency injection.

Contains interfaces for repositories and services,
used to break circular dependencies
and improve code testability.
"""

from mkobi.interfaces.repository_interfaces import (
    IRepository,
    IUserRepository,
    IDashboardRepository,
    IAccessRepository,
    IAggregatedDataRepository,
    IFilterRepository,
    IProcessingConfigRepository,
    IProcessingLogRepository,
    IGraphRepository,
)

from mkobi.interfaces.service_interfaces import (
    IAuthService,
    IUserService,
    IDashboardService,
    IFilterService,
    IDataService,
    IProcessingConfigService,
    IProcessingLogService,
)

__all__ = [
    # Repository interfaces
    "IRepository",
    "IUserRepository",
    "IDashboardRepository",
    "IAccessRepository",
    "IAggregatedDataRepository",
    "IFilterRepository",
    "IProcessingConfigRepository",
    "IProcessingLogRepository",
    "IGraphRepository",
    # Service interfaces
    "IAuthService",
    "IUserService",
    "IDashboardService",
    "IFilterService",
    "IDataService",
    "IProcessingConfigService",
    "IProcessingLogService",
]