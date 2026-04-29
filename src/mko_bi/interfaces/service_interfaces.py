"""Абстрактные интерфейсы для сервисов.

Определяет контракты для всех сервисов в системе.
Используются для внедрения зависимостей и разрыва циклических импортов.
"""

import abc
from typing import Any
from uuid import UUID

from mko_bi.models.user_roles import UserRoleEnum


class IAuthService(abc.ABC):
    """Интерфейс сервиса аутентификации."""

    @abc.abstractmethod
    def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Аутентифицировать пользователя по email и паролю."""
        pass

    @abc.abstractmethod
    def create_access_token(self, user_id: UUID, role: UserRoleEnum) -> str:
        """Создать токен доступа для пользователя."""
        pass

    @abc.abstractmethod
    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Проверить токен и вернуть данные пользователя."""
        pass


class IUserService(abc.ABC):
    """Интерфейс сервиса пользователей."""

    @abc.abstractmethod
    def get_user_by_id(self, user_id: UUID) -> dict[str, Any] | None:
        """Получить пользователя по ID."""
        pass

    @abc.abstractmethod
    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Получить пользователя по email."""
        pass

    @abc.abstractmethod
    def create_user(self, email: str, password: str, role: UserRoleEnum) -> dict[str, Any]:
        """Создать нового пользователя."""
        pass

    @abc.abstractmethod
    def update_user_role(self, user_id: UUID, role: UserRoleEnum) -> bool:
        """Обновить роль пользователя."""
        pass

    @abc.abstractmethod
    def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя."""
        pass

    @abc.abstractmethod
    def list_users(self) -> list[dict[str, Any]]:
        """Получить список всех пользователей."""
        pass


class IDashboardService(abc.ABC):
    """Интерфейс сервиса дашбордов."""

    @abc.abstractmethod
    def create_dashboard(self, name: str, user_id: UUID) -> dict[str, Any]:
        """Создать новый дашборд."""
        pass

    @abc.abstractmethod
    def get_dashboard_by_id(self, dashboard_id: UUID) -> dict[str, Any] | None:
        """Получить дашборд по ID."""
        pass

    @abc.abstractmethod
    def get_dashboard_by_name(self, name: str) -> dict[str, Any] | None:
        """Получить дашборд по имени."""
        pass

    @abc.abstractmethod
    def get_dashboards_by_user(self, user_id: UUID) -> list[dict[str, Any]]:
        """Получить все дашборды пользователя."""
        pass

    @abc.abstractmethod
    def update_dashboard(self, dashboard_id: UUID, name: str) -> bool:
        """Обновить дашборд."""
        pass

    @abc.abstractmethod
    def delete_dashboard(self, dashboard_id: UUID) -> bool:
        """Удалить дашборд."""
        pass


class IFilterService(abc.ABC):
    """Интерфейс сервиса фильтров."""

    @abc.abstractmethod
    def create_filter(
        self,
        name: str,
        dashboard_id: UUID,
        filter_type: str,
        config: dict[str, Any]
    ) -> dict[str, Any]:
        """Создать новый фильтр."""
        pass

    @abc.abstractmethod
    def get_filter_by_id(self, filter_id: UUID) -> dict[str, Any] | None:
        """Получить фильтр по ID."""
        pass

    @abc.abstractmethod
    def get_filter_by_name(self, name: str) -> dict[str, Any] | None:
        """Получить фильтр по имени."""
        pass

    @abc.abstractmethod
    def get_filters_by_dashboard(self, dashboard_id: UUID) -> list[dict[str, Any]]:
        """Получить все фильтры дашборда."""
        pass

    @abc.abstractmethod
    def update_filter(self, filter_id: UUID, config: dict[str, Any]) -> bool:
        """Обновить фильтр."""
        pass

    @abc.abstractmethod
    def delete_filter(self, filter_id: UUID) -> bool:
        """Удалить фильтр."""
        pass


class IDataService(abc.ABC):
    """Интерфейс сервиса данных."""

    @abc.abstractmethod
    def aggregate_data(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        dims: dict[str, Any],
        metrics: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Агрегировать данные по измерениям и метрикам."""
        pass

    @abc.abstractmethod
    def get_aggregated_data_by_dashboard(self, dashboard_id: UUID) -> list[dict[str, Any]]:
        """Получить агрегированные данные по ID дашборда."""
        pass

    @abc.abstractmethod
    def get_aggregated_data_by_graph(self, graph_id: UUID) -> list[dict[str, Any]]:
        """Получить агрегированные данные по ID графика."""
        pass


class IProcessingConfigService(abc.ABC):
    """Интерфейс сервиса настроек обработки."""

    @abc.abstractmethod
    def get_processing_config(self, dashboard_id: UUID) -> dict[str, Any] | None:
        """Получить настройки обработки дашборда."""
        pass

    @abc.abstractmethod
    def update_processing_config(
        self,
        dashboard_id: UUID,
        config: dict[str, Any]
    ) -> bool:
        """Обновить настройки обработки дашборда."""
        pass


class IProcessingLogService(abc.ABC):
    """Интерфейс сервиса логов обработки."""

    @abc.abstractmethod
    def get_processing_logs_by_dashboard(self, dashboard_id: UUID) -> list[dict[str, Any]]:
        """Получить логи обработки по ID дашборда."""
        pass

    @abc.abstractmethod
    def get_processing_logs_by_status(self, status: str) -> list[dict[str, Any]]:
        """Получить логи обработки по статусу."""
        pass

    @abc.abstractmethod
    def create_processing_log(
        self,
        dashboard_id: UUID,
        status: str,
        message: str
    ) -> dict[str, Any]:
        """Создать запись лога обработки."""
        pass