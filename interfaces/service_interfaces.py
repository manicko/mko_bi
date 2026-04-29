"""Абстрактные интерфейсы для сервисов.

Определяет контракты для всех сервисов в системе.
"""

import abc
from typing import List, Optional, Dict, Any
from uuid import UUID

from mko_bi.models.user import UserRead, UserCreate
from mko_bi.models.dashboard import DashboardRead, DashboardCreate
from mko_bi.models.graph import GraphRead, GraphCreate
from mko_bi.models.filter import FilterRead, FilterCreate
from mko_bi.models.processing_config import ProcessingConfigRead, ProcessingConfigCreate
from mko_bi.models.processing_log import ProcessingLogRead, ProcessingLogCreate


class IAuthService(abc.ABC):
    """Интерфейс сервиса аутентификации."""

    @abc.abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Аутентифицировать пользователя и вернуть токен."""
        pass

    @abc.abstractmethod
    def create_access_token(self, user_id: UUID) -> str:
        """Создать access токен для пользователя."""
        pass

    @abc.abstractmethod
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Декодировать токен и вернуть payload."""
        pass


class IUserService(abc.ABC):
    """Интерфейс сервиса пользователей."""

    @abc.abstractmethod
    def create_user(self, email: str, password: str, role: str) -> UserRead:
        """Создать нового пользователя."""
        pass

    @abc.abstractmethod
    def get_user_by_id(self, user_id: UUID) -> Optional[UserRead]:
        """Получить пользователя по ID."""
        pass

    @abc.abstractmethod
    def get_user_by_email(self, email: str) -> Optional[UserRead]:
        """Получить пользователя по email."""
        pass

    @abc.abstractmethod
    def update_user_role(self, user_id: UUID, new_role: str) -> Optional[UserRead]:
        """Обновить роль пользователя."""
        pass

    @abc.abstractmethod
    def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя."""
        pass

    @abc.abstractmethod
    def get_all_users(self) -> List[UserRead]:
        """Получить всех пользователей."""
        pass


class IDashboardService(abc.ABC):
    """Интерфейс сервиса дашбордов."""

    @abc.abstractmethod
    def create_dashboard(self, name: str, description: Optional[str], layout_id: UUID, created_by: UUID) -> DashboardRead:
        """Создать новый дашборд."""
        pass

    @abc.abstractmethod
    def get_dashboard_by_id(self, dashboard_id: UUID) -> Optional[DashboardRead]:
        """Получить дашборд по ID."""
        pass

    @abc.abstractmethod
    def get_dashboard_by_name(self, name: str) -> Optional[DashboardRead]:
        """Получить дашборд по имени."""
        pass

    @abc.abstractmethod
    def get_dashboards_by_user(self, user_id: UUID) -> List[DashboardRead]:
        """Получить дашборды по создателю."""
        pass

    @abc.abstractmethod
    def update_dashboard(self, dashboard_id: UUID, name: Optional[str], description: Optional[str], layout_id: Optional[UUID]) -> Optional[DashboardRead]:
        """Обновить дашборд."""
        pass

    @abc.abstractmethod
    def delete_dashboard(self, dashboard_id: UUID) -> bool:
        """Удалить дашборд."""
        pass

    @abc.abstractmethod
    def get_all_dashboards(self) -> List[DashboardRead]:
        """Получить все дашборды."""
        pass


class IGraphService(abc.ABC):
    """Интерфейс сервиса графиков."""

    @abc.abstractmethod
    def create_graph(self, dashboard_id: UUID, name: str, type_: str, config: Dict[str, Any], dimensions: Dict[str, Any], metrics: Dict[str, Any]) -> GraphRead:
        """Создать новый график."""
        pass

    @abc.abstractmethod
    def get_graph_by_id(self, graph_id: UUID) -> Optional[GraphRead]:
        """Получить график по ID."""
        pass

    @abc.abstractmethod
    def get_graph_by_name_and_dashboard(self, name: str, dashboard_id: UUID) -> Optional[GraphRead]:
        """Получить график по имени и ID дашборда."""
        pass

    @abc.abstractmethod
    def get_graphs_by_dashboard(self, dashboard_id: UUID) -> List[GraphRead]:
        """Получить графики по ID дашборда."""
        pass

    @abc.abstractmethod
    def update_graph(self, graph_id: UUID, name: Optional[str], type_: Optional[str], config: Optional[Dict[str, Any]], dimensions: Optional[Dict[str, Any]], metrics: Optional[Dict[str, Any]]) -> Optional[GraphRead]:
        """Обновить график."""
        pass

    @abc.abstractmethod
    def delete_graph(self, graph_id: UUID) -> bool:
        """Удалить график."""
        pass


class IFilterService(abc.ABC):
    """Интерфейс сервиса фильтров."""

    @abc.abstractmethod
    def create_filter(self, name: str, type_: str, config: Dict[str, Any]) -> FilterRead:
        """Создать новый фильтр."""
        pass

    @abc.abstractmethod
    def get_filter_by_id(self, filter_id: UUID) -> Optional[FilterRead]:
        """Получить фильтр по ID."""
        pass

    @abc.abstractmethod
    def get_filter_by_name(self, name: str) -> Optional[FilterRead]:
        """Получить фильтр по имени."""
        pass

    @abc.abstractmethod
    def update_filter(self, filter_id: UUID, name: Optional[str], type_: Optional[str], config: Optional[Dict[str, Any]]) -> Optional[FilterRead]:
        """Обновить фильтр."""
        pass

    @abc.abstractmethod
    def delete_filter(self, filter_id: UUID) -> bool:
        """Удалить фильтр."""
        pass

    @abc.abstractmethod
    def get_all_filters(self) -> List[FilterRead]:
        """Получить все фильтры."""
        pass


class IDataService(abc.ABC):
    """Интерфейс сервиса данных."""

    @abc.abstractmethod
    def process_upload(self, file_content: bytes, dashboard_id: UUID) -> bool:
        """Обработать загруженный файл и сохранить агрегаты."""
        pass

    @abc.abstractmethod
    def get_aggregated_data(self, dashboard_id: UUID, graph_id: UUID) -> List[Dict[str, Any]]:
        """Получить агрегированные данные для графика."""
        pass

    @abc.abstractmethod
    def get_available_metrics(self, dashboard_id: UUID) -> List[str]:
        """Получить список доступных метрик для дашборда."""
        pass

    @abc.abstractmethod
    def get_available_dimensions(self, dashboard_id: UUID) -> List[str]:
        """Получить список доступных измерений для дашборда."""
        pass


class IProcessingConfigService(abc.ABC):
    """Интерфейс сервиса настроек обработки."""

    @abc.abstractmethod
    def create_processing_config(self, dashboard_id: UUID, settings: Dict[str, Any]) -> ProcessingConfigRead:
        """Создать настройки обработки для дашборда."""
        pass

    @abc.abstractmethod
    def get_processing_config_by_dashboard(self, dashboard_id: UUID) -> Optional[ProcessingConfigRead]:
        """Получить настройки обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    def update_processing_config(self, dashboard_id: UUID, settings: Dict[str, Any]) -> Optional[ProcessingConfigRead]:
        """Обновить настройки обработки."""
        pass

    @abc.abstractmethod
    def delete_processing_config(self, dashboard_id: UUID) -> bool:
        """Удалить настройки обработки."""
        pass


class IProcessingLogService(abc.ABC):
    """Интерфейс сервиса логов обработки."""

    @abc.abstractmethod
    def create_processing_log(self, dashboard_id: UUID, status: str, message: Optional[str] = None) -> ProcessingLogRead:
        """Создать запись лога обработки."""
        pass

    @abc.abstractmethod
    def get_processing_logs_by_dashboard(self, dashboard_id: UUID) -> List[ProcessingLogRead]:
        """Получить логи обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    def get_processing_logs_by_status(self, status: str) -> List[ProcessingLogRead]:
        """Получить логи обработки по статусу."""
        pass

    @abc.abstractmethod
    def update_processing_log(self, log_id: UUID, status: Optional[str], message: Optional[str], finished_at: Optional[Any]) -> Optional[ProcessingLogRead]:
        """Обновить запись лога обработки."""
        pass

    @abc.abstractmethod
    def delete_processing_log(self, log_id: UUID) -> bool:
        """Удалить запись лога обработки."""
        pass