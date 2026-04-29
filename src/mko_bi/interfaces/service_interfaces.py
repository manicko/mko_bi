"""Абстрактные интерфейсы для сервисов.

Определяет контракты для всех сервисов в системе.
"""

import abc
from typing import Any
from uuid import UUID

from mko_bi.models.user import UserRead
from mko_bi.models.dashboard import DashboardRead
from mko_bi.models.graph import GraphRead
from mko_bi.models.filters import FilterRead
from mko_bi.models.processing_configs import ProcessingConfigRead
from mko_bi.models.processing_logs import ProcessingLogRead


class IAuthService(abc.ABC):
    """Интерфейс сервиса аутентификации."""

    @abc.abstractmethod
    def register_user(self, email: str, password: str, role: str, db: Any = None) -> UserRead:
        """Зарегистрировать нового пользователя."""
        pass

    @abc.abstractmethod
    def authenticate_user(self, email: str, password: str, db: Any = None) -> Any | None:
        """Аутентифицировать пользователя и вернуть данные."""
        pass

    @abc.abstractmethod
    def login_user(self, email: str, password: str, db: Any = None) -> dict[str, Any]:
        """Выполнить вход и вернуть JWT токен."""
        pass

    @abc.abstractmethod
    def refresh_token(self, user_id: Any, email: str, role: str, db: Any = None) -> dict[str, Any]:
        """Обновить JWT токен."""
        pass

    @abc.abstractmethod
    def create_access_token(self, user_id: Any, role: Any) -> str:
        """Создать access токен для пользователя."""
        pass

    @abc.abstractmethod
    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Проверить JWT токен и вернуть данные."""
        pass


class IUserService(abc.ABC):
    """Интерфейс сервиса пользователей."""

    @abc.abstractmethod
    def create_user(self, email: str, password: str, role: str) -> UserRead:
        """Создать нового пользователя."""
        pass

    @abc.abstractmethod
    def get_user_by_id(self, user_id: UUID) -> UserRead | None:
        """Получить пользователя по ID."""
        pass

    @abc.abstractmethod
    def get_user_by_email(self, email: str) -> UserRead | None:
        """Получить пользователя по email."""
        pass

    @abc.abstractmethod
    def update_user_role(self, user_id: UUID, new_role: str) -> UserRead | None:
        """Обновить роль пользователя."""
        pass

    @abc.abstractmethod
    def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя."""
        pass

    @abc.abstractmethod
    def get_all_users(self) -> list[UserRead]:
        """Получить всех пользователей."""
        pass


class IDashboardService(abc.ABC):
    """Интерфейс сервиса дашбордов."""

    @abc.abstractmethod
    def create_dashboard(self, name: str, description: str | None, layout_id: UUID, created_by: UUID) -> DashboardRead:
        """Создать новый дашборд."""
        pass

    @abc.abstractmethod
    def get_dashboard_by_id(self, dashboard_id: UUID) -> DashboardRead | None:
        """Получить дашборд по ID."""
        pass

    @abc.abstractmethod
    def get_dashboard_by_name(self, name: str) -> DashboardRead | None:
        """Получить дашборд по имени."""
        pass

    @abc.abstractmethod
    def get_dashboards_by_user(self, user_id: UUID) -> list[DashboardRead]:
        """Получить дашборды по создателю."""
        pass

    @abc.abstractmethod
    def update_dashboard(self, dashboard_id: UUID, name: str | None, description: str | None, layout_id: UUID | None) -> DashboardRead | None:
        """Обновить дашборд."""
        pass

    @abc.abstractmethod
    def delete_dashboard(self, dashboard_id: UUID) -> bool:
        """Удалить дашборд."""
        pass

    @abc.abstractmethod
    def get_all_dashboards(self) -> list[DashboardRead]:
        """Получить все дашборды."""
        pass


class IGraphService(abc.ABC):
    """Интерфейс сервиса графиков."""

    @abc.abstractmethod
    def create_graph(self, dashboard_id: UUID, name: str, type_: str, config: dict[str, Any], dimensions: dict[str, Any], metrics: dict[str, Any]) -> GraphRead:
        """Создать новый график."""
        pass

    @abc.abstractmethod
    def get_graph_by_id(self, graph_id: UUID) -> GraphRead | None:
        """Получить график по ID."""
        pass

    @abc.abstractmethod
    def get_graph_by_name_and_dashboard(self, name: str, dashboard_id: UUID) -> GraphRead | None:
        """Получить график по имени и ID дашборда."""
        pass

    @abc.abstractmethod
    def get_graphs_by_dashboard(self, dashboard_id: UUID) -> list[GraphRead]:
        """Получить графики по ID дашборда."""
        pass

    @abc.abstractmethod
    def update_graph(self, graph_id: UUID, name: str | None, type_: str | None, config: dict[str, Any] | None, dimensions: dict[str, Any] | None, metrics: dict[str, Any] | None) -> GraphRead | None:
        """Обновить график."""
        pass

    @abc.abstractmethod
    def delete_graph(self, graph_id: UUID) -> bool:
        """Удалить график."""
        pass


class IFilterService(abc.ABC):
    """Интерфейс сервиса фильтров."""

    @abc.abstractmethod
    def create_filter(self, name: str, type_: str, config: dict[str, Any]) -> FilterRead:
        """Создать новый фильтр."""
        pass

    @abc.abstractmethod
    def get_filter_by_id(self, filter_id: UUID) -> FilterRead | None:
        """Получить фильтр по ID."""
        pass

    @abc.abstractmethod
    def get_filter_by_name(self, name: str) -> FilterRead | None:
        """Получить фильтр по имени."""
        pass

    @abc.abstractmethod
    def update_filter(self, filter_id: UUID, name: str | None, type_: str | None, config: dict[str, Any] | None) -> FilterRead | None:
        """Обновить фильтр."""
        pass

    @abc.abstractmethod
    def delete_filter(self, filter_id: UUID) -> bool:
        """Удалить фильтр."""
        pass

    @abc.abstractmethod
    def get_all_filters(self) -> list[FilterRead]:
        """Получить все фильтры."""
        pass


class IDataService(abc.ABC):
    """Интерфейс сервиса данных."""

    @abc.abstractmethod
    def process_upload(self, file_content: bytes, dashboard_id: UUID) -> bool:
        """Обработать загруженный файл и сохранить агрегаты."""
        pass

    @abc.abstractmethod
    def get_aggregated_data(self, dashboard_id: UUID, graph_id: UUID) -> list[dict[str, Any]]:
        """Получить агрегированные данные для графика."""
        pass

    @abc.abstractmethod
    def get_available_metrics(self, dashboard_id: UUID) -> list[str]:
        """Получить список доступных метрик для дашборда."""
        pass

    @abc.abstractmethod
    def get_available_dimensions(self, dashboard_id: UUID) -> list[str]:
        """Получить список доступных измерений для дашборда."""
        pass


class IProcessingConfigService(abc.ABC):
    """Интерфейс сервиса настроек обработки."""

    @abc.abstractmethod
    def create_processing_config(self, dashboard_id: UUID, settings: dict[str, Any]) -> ProcessingConfigRead:
        """Создать настройки обработки для дашборда."""
        pass

    @abc.abstractmethod
    def get_processing_config_by_dashboard(self, dashboard_id: UUID) -> ProcessingConfigRead | None:
        """Получить настройки обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    def update_processing_config(self, dashboard_id: UUID, settings: dict[str, Any]) -> ProcessingConfigRead | None:
        """Обновить настройки обработки."""
        pass

    @abc.abstractmethod
    def delete_processing_config(self, dashboard_id: UUID) -> bool:
        """Удалить настройки обработки."""
        pass


class IProcessingLogService(abc.ABC):
    """Интерфейс сервиса логов обработки."""

    @abc.abstractmethod
    def create_processing_log(self, dashboard_id: UUID, status: str, message: str | None = None) -> ProcessingLogRead:
        """Создать запись лога обработки."""
        pass

    @abc.abstractmethod
    def get_processing_logs_by_dashboard(self, dashboard_id: UUID) -> list[ProcessingLogRead]:
        """Получить логи обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    def get_processing_logs_by_status(self, status: str) -> list[ProcessingLogRead]:
        """Получить логи обработки по статусу."""
        pass

    @abc.abstractmethod
    def update_processing_log(self, log_id: UUID, status: str | None, message: str | None, finished_at: Any | None) -> ProcessingLogRead | None:
        """Обновить запись лога обработки."""
        pass

    @abc.abstractmethod
    def delete_processing_log(self, log_id: UUID) -> bool:
        """Удалить запись лога обработки."""
        pass