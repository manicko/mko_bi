"""Репозитории для работы с базой данных.

Содержит реализации паттерна Repository для всех моделей:
- UserRepository: операции с пользователями
- DashboardRepository: операции с дашбордами
- AccessRepository: управление правами доступа
- FilterRepository: управление фильтрами
- ProcessingConfigRepository: управление настройками обработки
- ProcessingLogRepository: управление логами обработки
- AggregatedDataRepository: управление агрегированными данными
"""

from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.filter_repo import FilterRepository
from mko_bi.db.repositories.processing_config_repo import ProcessingConfigRepository
from mko_bi.db.repositories.processing_log_repo import ProcessingLogRepository
from mko_bi.db.repositories.user_repo import UserRepository

__all__ = [
    "UserRepository",
    "DashboardRepository",
    "AccessRepository",
    "AggregatedDataRepository",
    "FilterRepository",
    "ProcessingConfigRepository",
    "ProcessingLogRepository",
]
