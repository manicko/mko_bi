"""Repositories for database operations.

Contains Repository pattern implementations for all models:
- UserRepository: user operations
- DashboardRepository: dashboard operations
- AccessRepository: access rights management
- FilterRepository: filter management
- ProcessingConfigRepository: processing settings management
- ProcessingLogRepository: processing log management
- AggregatedDataRepository: aggregated data management
"""

from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.db.repositories.processing_config_repo import ProcessingConfigRepository
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.db.repositories.user_repo import UserRepository

__all__ = [
    "UserRepository",
    "DashboardRepository",
    "AccessRepository",
    "AggregatedDataRepository",
    "FilterRepository",
    "ProcessingConfigRepository",
    "ProcessingLogRepository",
]
