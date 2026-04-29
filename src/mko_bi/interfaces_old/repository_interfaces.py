"""Абстрактные интерфейсы для репозиториев.

Определяет контракты для всех репозиториев в системе.
"""

import abc
from typing import Generic, TypeVar, List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

# Import models for type hints in specific repository interfaces
from mko_bi.db.models import user as user_model
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.models import access as access_model
from mko_bi.db.models import aggregated_data as aggregated_data_model
from mko_bi.db.models import graphs as graph_model
from mko_bi.db.models import filters as filter_model
from mko_bi.db.models import processing_configs as processing_config_model
from mko_bi.db.models import processing_logs as processing_log_model

# Generic type for models
T = TypeVar('T')


class IRepository(abc.ABC, Generic[T]):
    """Базовый интерфейс репозитория."""

    @classmethod
    @abc.abstractmethod
    def get(cls, id: UUID, db: Session) -> Optional[T]:
        """Получить объект по ID."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_all(cls, db: Session) -> List[T]:
        """Получить все объекты."""
        pass

    @classmethod
    @abc.abstractmethod
    def create(cls, db: Session, **kwargs) -> Optional[T]:
        """Создать новый объект."""
        pass

    @classmethod
    @abc.abstractmethod
    def update(cls, id: UUID, db: Session, **kwargs) -> Optional[T]:
        """Обновить объект."""
        pass

    @classmethod
    @abc.abstractmethod
    def delete(cls, id: UUID, db: Session) -> bool:
        """Удалить объект."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_session(cls) -> Session:
        """Получить новую сессию."""
        pass


class IUserRepository(IRepository):
    """Интерфейс репозитория пользователей."""

    @classmethod
    @abc.abstractmethod
    def get_by_email(cls, email: str, db: Session) -> Optional[user_model.User]:
        """Получить пользователя по email."""
        pass


class IDashboardRepository(IRepository):
    """Интерфейс репозитория дашбордов."""

    @classmethod
    @abc.abstractmethod
    def get_by_name(cls, name: str, db: Session) -> Optional[dashboard_model.Dashboard]:
        """Получить дашборд по имени."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_by_user(cls, user_id: UUID, db: Session) -> List[dashboard_model.Dashboard]:
        """Получить дашборды по пользователю (доступные пользователю)."""
        pass


class IAccessRepository(abc.ABC):
    """Интерфейс репозитория прав доступа."""

    @classmethod
    @abc.abstractmethod
    def grant_access(
        cls,
        db: Session,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> Optional[access_model.DashboardAccess]:
        """Предоставить пользователю доступ к дашборду."""
        pass

    @classmethod
    @abc.abstractmethod
    def revoke_access(
        cls, user_id: UUID, dashboard_id: UUID, db: Session
    ) -> bool:
        """Отозвать доступ пользователя к дашборду."""
        pass

    @classmethod
    @abc.abstractmethod
    def check_access(
        cls, user_id: UUID, dashboard_id: UUID, db: Session
    ) -> Optional[str]:
        """Проверить уровень доступа пользователя к дашборду."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_user_dashboards(
        cls, user_id: UUID, db: Session
    ) -> List[dashboard_model.Dashboard]:
        """Получить все дашборды, доступные пользователю."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_all(cls, db: Session) -> List[access_model.DashboardAccess]:
        """Получить все права доступа."""
        pass


class IAggregatedDataRepository(IRepository):
    """Интерфейс репозитория агрегированных данных."""

    @classmethod
    @abc.abstractmethod
    def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: Session
    ) -> List[aggregated_data_model.AggregatedData]:
        """Получить агрегированные данные по ID дашборда."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_by_graph_id(
        cls, graph_id: UUID, db: Session
    ) -> List[aggregated_data_model.AggregatedData]:
        """Получить агрегированные данные по ID графика."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_by_dims_and_metrics(
        cls,
        dashboard_id: UUID,
        graph_id: UUID,
        dims: Dict[str, Any],
        metrics: Dict[str, Any],
        db: Session
    ) -> Optional[aggregated_data_model.AggregatedData]:
        """Получить агрегированные данные по измерениям и метрикам."""
        pass

    @classmethod
    @abc.abstractmethod
    def create_bulk(
        cls, db: Session, objects: List[Dict[str, Any]]
    ) -> List[aggregated_data_model.AggregatedData]:
        """Создать несколько записей агрегированных данных."""
        pass


class IGraphRepository(IRepository):
    """Интерфейс репозитория графиков."""

    @classmethod
    @abc.abstractmethod
    def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: Session
    ) -> List[graph_model.Graph]:
        """Получить графики по ID дашборда."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_by_name_and_dashboard(
        cls, name: str, dashboard_id: UUID, db: Session
    ) -> Optional[graph_model.Graph]:
        """Получить график по имени и ID дашборда."""
        pass


class IFilterRepository(IRepository):
    """Интерфейс репозитория фильтров."""

    @classmethod
    @abc.abstractmethod
    def get_by_name(cls, name: str, db: Session) -> Optional[filter_model.Filter]:
        """Получить фильтр по имени."""
        pass


class IProcessingConfigRepository(IRepository):
    """Интерфейс репозитория настроек обработки."""

    @classmethod
    @abc.abstractmethod
    def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: Session
    ) -> Optional[processing_config_model.ProcessingConfig]:
        """Получить настройки обработки по ID дашборда."""
        pass


class IProcessingLogRepository(IRepository):
    """Интерфейс репозитория логов обработки."""

    @classmethod
    @abc.abstractmethod
    def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: Session
    ) -> List[processing_log_model.ProcessingLog]:
        """Получить логи обработки по ID дашборда."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_by_status(
        cls, status: str, db: Session
    ) -> List[processing_log_model.ProcessingLog]:
        """Получить логи обработки по статусу."""
        pass