"""Репозитории для работы с базой данных.

Содержит реализации паттерна Repository для всех моделей:
- UserRepository: операции с пользователями
- DashboardRepository: операции с дашбордами
- AccessRepository: управление правами доступа
"""

from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.user_repo import UserRepository

__all__ = ["UserRepository", "DashboardRepository", "AccessRepository"]
