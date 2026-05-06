"""Абстрактные интерфейсы для репозиториев.

Определяет контракты для всех репозиториев в системе.
Используются для внедрения зависимостей и разрыва циклических импортов.
"""

import abc
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class IRepository(abc.ABC):
    """Базовый интерфейс репозитория."""

    @abc.abstractmethod
    async def get(self, id: UUID, db: AsyncSession) -> Any | None:
        """Получить объект по ID."""
        pass

    @abc.abstractmethod
    async def get_all(self, db: AsyncSession) -> list[Any]:
        """Получить все объекты."""
        pass

    @abc.abstractmethod
    async def create(self, db: AsyncSession, **kwargs) -> Any | None:
        """Создать новый объект."""
        pass

    @abc.abstractmethod
    async def update(self, id: UUID, db: AsyncSession, **kwargs) -> Any | None:
        """Обновить объект."""
        pass

    @abc.abstractmethod
    async def delete(self, id: UUID, db: AsyncSession) -> bool:
        """Удалить объект."""
        pass


class IUserRepository(IRepository):
    """Интерфейс репозитория пользователей."""

    @abc.abstractmethod
    async def get_by_email(self, email: str, db: AsyncSession) -> Any | None:
        """Получить пользователя по email."""
        pass


class IDashboardRepository(IRepository):
    """Интерфейс репозитория дашбордов."""

    @abc.abstractmethod
    async def get_by_name(self, name: str, db: AsyncSession) -> Any | None:
        """Получить дашборд по имени."""
        pass

    @abc.abstractmethod
    async def get_by_user(self, user_id: UUID, db: AsyncSession) -> list[Any]:
        """Получить дашборды по пользователю (доступные пользователю)."""
        pass


class IAccessRepository(abc.ABC):
    """Интерфейс репозитория прав доступа."""

    @abc.abstractmethod
    async def grant_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> Any | None:
        """Предоставить пользователю доступ к дашборду."""
        pass

    @abc.abstractmethod
    async def revoke_access(
        self, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> bool:
        """Отозвать доступ пользователя к дашборду."""
        pass

    @abc.abstractmethod
    async def check_access(
        self, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> str | None:
        """Проверить уровень доступа пользователя к дашборду."""
        pass

    @abc.abstractmethod
    async def get_user_dashboards(
        self, user_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Получить все дашборды, доступные пользователю."""
        pass

    @abc.abstractmethod
    async def get_all(self, db: AsyncSession) -> list[Any]:
        """Получить все права доступа."""
        pass


class IAggregatedDataRepository(IRepository):
    """Интерфейс репозитория агрегированных данных."""

    @abc.abstractmethod
    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Получить агрегированные данные по ID дашборда."""
        pass

    @abc.abstractmethod
    async def get_by_graph_id(
        self, graph_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Получить агрегированные данные по ID графика."""
        pass


class IFilterRepository(IRepository):
    """Интерфейс репозитория фильтров."""

    @abc.abstractmethod
    async def get_by_name(self, name: str, db: AsyncSession) -> Any | None:
        """Получить фильтр по имени."""
        pass


class IGraphRepository(IRepository):
    """Интерфейс репозитория графиков."""

    @abc.abstractmethod
    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Получить графики по ID дашборда."""
        pass

    @abc.abstractmethod
    async def get_by_name_and_dashboard(
        self, name: str, dashboard_id: UUID, db: AsyncSession
    ) -> Any | None:
        """Получить график по имени и ID дашборда."""
        pass


class IProcessingConfigRepository(IRepository):
    """Интерфейс репозитория настроек обработки."""

    @abc.abstractmethod
    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> Any | None:
        """Получить настройки обработки по ID дашборда."""
        pass


class IProcessingLogRepository(IRepository):
    """Интерфейс репозитория логов обработки."""

    @abc.abstractmethod
    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Получить логи обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    async def get_by_status(
        self, status: str, db: AsyncSession
    ) -> list[Any]:
        """Получить логи обработки по статусу."""
        pass
