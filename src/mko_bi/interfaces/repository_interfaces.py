"""Абстрактные интерфейсы для репозиториев.

Определяет контракты для всех репозиториев в системе.
Используются для внедрения зависимостей и разрыва циклических импортов.
"""

import abc
from typing import Generic, TypeVar, Any
from uuid import UUID

from sqlalchemy.orm import Session

# Generic type for models
T = TypeVar('T')


class IRepository(abc.ABC, Generic[T]):
    """Базовый интерфейс репозитория."""

    @abc.abstractmethod
    def get(self, id: UUID, db: Session) -> T | None:
        """Получить объект по ID."""
        pass

    @abc.abstractmethod
    def get_all(self, db: Session) -> list[T]:
        """Получить все объекты."""
        pass

    @abc.abstractmethod
    def create(self, db: Session, **kwargs) -> T | None:
        """Создать новый объект."""
        pass

    @abc.abstractmethod
    def update(self, id: UUID, db: Session, **kwargs) -> T | None:
        """Обновить объект."""
        pass

    @abc.abstractmethod
    def delete(self, id: UUID, db: Session) -> bool:
        """Удалить объект."""
        pass

    @abc.abstractmethod
    def get_session(self) -> Session:
        """Получить новую сессию."""
        pass


class IUserRepository(IRepository):
    """Интерфейс репозитория пользователей."""

    @abc.abstractmethod
    def get_by_email(self, email: str, db: Session) -> Any | None:
        """Получить пользователя по email."""
        pass


class IDashboardRepository(IRepository):
    """Интерфейс репозитория дашбордов."""

    @abc.abstractmethod
    def get_by_name(self, name: str, db: Session) -> Any | None:
        """Получить дашборд по имени."""
        pass

    @abc.abstractmethod
    def get_by_user(self, user_id: UUID, db: Session) -> list[Any]:
        """Получить дашборды по пользователю (доступные пользователю)."""
        pass


class IAccessRepository(abc.ABC):
    """Интерфейс репозитория прав доступа."""

    @abc.abstractmethod
    def grant_access(
        self,
        db: Session,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> Any | None:
        """Предоставить пользователю доступ к дашборду."""
        pass

    @abc.abstractmethod
    def revoke_access(
        self, user_id: UUID, dashboard_id: UUID, db: Session
    ) -> bool:
        """Отозвать доступ пользователя к дашборду."""
        pass

    @abc.abstractmethod
    def check_access(
        self, user_id: UUID, dashboard_id: UUID, db: Session
    ) -> str | None:
        """Проверить уровень доступа пользователя к дашборду."""
        pass

    @abc.abstractmethod
    def get_user_dashboards(
        self, user_id: UUID, db: Session
    ) -> list[Any]:
        """Получить все дашборды, доступные пользователю."""
        pass

    @abc.abstractmethod
    def get_all(self, db: Session) -> list[Any]:
        """Получить все права доступа."""
        pass


class IAggregatedDataRepository(IRepository):
    """Интерфейс репозитория агрегированных данных."""

    @abc.abstractmethod
    def get_by_dashboard_id(
        self, dashboard_id: UUID, db: Session
    ) -> list[Any]:
        """Получить агрегированные данные по ID дашборда."""
        pass

    @abc.abstractmethod
    def get_by_graph_id(
        self, graph_id: UUID, db: Session
    ) -> list[Any]:
        """Получить агрегированные данные по ID графика."""
        pass

    @abc.abstractmethod
    def create_bulk(
        self, db: Session, objects: list[dict[str, Any]]
    ) -> list[Any]:
        """Создать несколько записей агрегированных данных."""
        pass


class IFilterRepository(IRepository):
    """Интерфейс репозитория фильтров."""

    @abc.abstractmethod
    def get_by_name(self, name: str, db: Session) -> Any | None:
        """Получить фильтр по имени."""
        pass


class IProcessingConfigRepository(IRepository):
    """Интерфейс репозитория настроек обработки."""

    @abc.abstractmethod
    def get_by_dashboard_id(
        self, dashboard_id: UUID, db: Session
    ) -> Any | None:
        """Получить настройки обработки по ID дашборда."""
        pass


class IProcessingLogRepository(IRepository):
    """Интерфейс репозитория логов обработки."""

    @abc.abstractmethod
    def get_by_dashboard_id(
        self, dashboard_id: UUID, db: Session
    ) -> list[Any]:
        """Получить логи обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    def get_by_status(
        self, status: str, db: Session
    ) -> list[Any]:
        """Получить логи обработки по статусу."""
        pass