"""Абстрактные интерфейсы для внедрения зависимостей.

Содержит интерфейсы для репозиториев и сервисов,
которые используются для разрыва циклических зависимостей
и улучшения тестируемости кода.
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
    # Service interfaces
    "IAuthService",
    "IUserService",
    "IDashboardService",
    "IFilterService",
    "IDataService",
    "IProcessingConfigService",
    "IProcessingLogService",
]