"""Abstract interfaces for services.

Defines contracts for all services in the system.
"""

import abc
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.models.dashboard import DashboardRead
from mkobi.models.data import ProcessingResultData, UploadResponse
from mkobi.models.enums import UserRole
from mkobi.models.filters import FilterRead
from mkobi.models.graph import GraphRead
from mkobi.models.processing_configs import ProcessingConfigRead
from mkobi.models.processing_logs import ProcessingLogRead
from mkobi.models.types import (
    FilterConfigDict,
    ProcessingSettingsDict,
)
from mkobi.models.user import UserRead


class IAuthService(abc.ABC):
    """Authentication service interface."""

    @abc.abstractmethod
    async def register_user(
        self, email: str, password: str, role: str, db: AsyncSession | None = None
    ) -> UserRead:
        """Register new user."""
        pass

    @abc.abstractmethod
    async def authenticate_user(
        self, email: str, password: str, db: AsyncSession | None = None
    ) -> UserRead | None:
        """Authenticate user and return data."""
        pass

    @abc.abstractmethod
    async def login_user(
        self, email: str, password: str, db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Perform login and return JWT token."""
        pass

    @abc.abstractmethod
    async def refresh_token(
        self, user_id: UUID, email: str, role: str, db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Refresh JWT token."""
        pass

    @abc.abstractmethod
    def create_access_token(self, user_id: UUID, role: str) -> str:
        """Create access token for user."""
        pass

    @abc.abstractmethod
    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify JWT token and return data."""
        pass

    @abc.abstractmethod
    async def register_request(
        self, email: str, ip: str | None, db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Create registration request."""
        pass

    @abc.abstractmethod
    async def get_user_by_id(
        self, user_id: UUID, db: AsyncSession | None = None
    ) -> UserRead | None:
        """Get user by ID."""
        pass

    @abc.abstractmethod
    async def get_user_by_email(
        self, email: str, db: AsyncSession | None = None
    ) -> UserRead | None:
        """Get user by email."""
        pass


class IUserService(abc.ABC):
    """User service interface."""

    @abc.abstractmethod
    async def create_user(
        self, email: str, password: str, role: UserRole, db: AsyncSession
    ) -> UserRead:
        """Create new user."""
        pass

    @abc.abstractmethod
    async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> UserRead | None:
        """Get user by ID."""
        pass

    @abc.abstractmethod
    async def get_user_by_email(self, email: str, db: AsyncSession) -> UserRead | None:
        """Get user by email."""
        pass

    @abc.abstractmethod
    async def update_user_role(
        self, user_id: UUID, role: UserRole, db: AsyncSession
    ) -> UserRead | None:
        """Update user role."""
        pass

    @abc.abstractmethod
    async def delete_user(self, user_id: UUID, db: AsyncSession) -> bool:
        """Delete user."""
        pass

    @abc.abstractmethod
    async def get_all_users(self, db: AsyncSession) -> list[UserRead]:
        """Get all users."""
        pass


class IDashboardService(abc.ABC):
    """Dashboard service interface."""

    @abc.abstractmethod
    async def create_dashboard(
        self,
        name: str,
        config: dict[str, Any],
        owner_id: UUID,
        db: AsyncSession | None = None,
    ) -> DashboardRead:
        """Create new dashboard."""
        pass

    @abc.abstractmethod
    async def get_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> DashboardRead | None:
        """Get dashboard by ID with access check."""
        pass

    @abc.abstractmethod
    async def get_dashboard_by_name(
        self,
        name: str,
        db: AsyncSession | None = None,
    ) -> DashboardRead | None:
        """Get dashboard by name."""
        pass

    @abc.abstractmethod
    async def get_user_dashboards(
        self,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[DashboardRead]:
        """Get user dashboards."""
        pass

    @abc.abstractmethod
    async def update_dashboard(
        self,
        dashboard_id: UUID,
        update_data: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> DashboardRead | None:
        """Update dashboard."""
        pass

    @abc.abstractmethod
    async def delete_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete dashboard."""
        pass

    @abc.abstractmethod
    async def get_all_dashboards(
        self,
        db: AsyncSession | None = None,
    ) -> list[DashboardRead]:
        """Get all dashboards."""
        pass

    @abc.abstractmethod
    async def grant_access(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        permission: str,
        db: AsyncSession | None = None,
    ) -> bool:
        """Grant access to dashboard."""
        pass

    @abc.abstractmethod
    async def revoke_access(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Revoke access to dashboard."""
        pass

    @abc.abstractmethod
    async def get_dashboard_access_list(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """Get access list for dashboard."""
        pass


class IGraphService(abc.ABC):
    """Graph service interface."""

    @abc.abstractmethod
    async def create_graph(
        self,
        dashboard_id: UUID,
        name: str,
        type_: str,
        config: dict[str, Any],
        dimensions: list[str],
        metrics: list[str],
        db: AsyncSession | None = None,
    ) -> GraphRead:
        """Create new graph."""
        pass

    @abc.abstractmethod
    async def get_graph_by_id(
        self,
        graph_id: UUID,
        db: AsyncSession | None = None,
    ) -> GraphRead | None:
        """Get graph by ID."""
        pass

    @abc.abstractmethod
    async def get_graph_by_name_and_dashboard(
        self,
        name: str,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> GraphRead | None:
        """Get graph by name and dashboard ID."""
        pass

    @abc.abstractmethod
    async def get_graphs_by_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[GraphRead]:
        """Get graphs by dashboard ID."""
        pass

    @abc.abstractmethod
    async def update_graph(
        self,
        graph_id: UUID,
        name: str | None,
        type_: str | None,
        config: dict[str, Any] | None,
        dimensions: list[str] | None,
        metrics: list[str] | None,
        db: AsyncSession | None = None,
    ) -> GraphRead | None:
        """Update graph."""
        pass

    @abc.abstractmethod
    async def delete_graph(
        self,
        graph_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete graph."""
        pass


class IFilterService(abc.ABC):
    """Filter service interface."""

    @abc.abstractmethod
    async def create_filter(
        self,
        name: str,
        type_: str,
        config: FilterConfigDict,
        db: AsyncSession | None = None,
    ) -> FilterRead:
        """Create new filter."""
        pass

    @abc.abstractmethod
    async def get_filter_by_id(
        self,
        filter_id: UUID,
        db: AsyncSession | None = None,
    ) -> FilterRead | None:
        """Get filter by ID."""
        pass

    @abc.abstractmethod
    async def get_filter_by_name(
        self,
        name: str,
        db: AsyncSession | None = None,
    ) -> FilterRead | None:
        """Get filter by name."""
        pass

    @abc.abstractmethod
    async def update_filter(
        self,
        filter_id: UUID,
        name: str | None,
        type_: str | None,
        config: FilterConfigDict | None,
        db: AsyncSession | None = None,
    ) -> FilterRead | None:
        """Update filter."""
        pass

    @abc.abstractmethod
    async def delete_filter(
        self,
        filter_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete filter."""
        pass

    @abc.abstractmethod
    async def get_all_filters(
        self,
        db: AsyncSession | None = None,
    ) -> list[FilterRead]:
        """Get all filters."""
        pass


class IDataService(abc.ABC):
    """Data service interface."""

    @abc.abstractmethod
    async def process_upload(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        db: AsyncSession | None = None,
    ) -> UploadResponse:
        """Process uploaded file and save aggregates."""
        pass

    @abc.abstractmethod
    async def get_aggregated_data(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[ProcessingResultData]:
        """Get aggregated data for graph."""
        pass

    @abc.abstractmethod
    async def get_available_metrics(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[str]:
        """Get available metrics for dashboard."""
        pass

    @abc.abstractmethod
    async def get_available_dimensions(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[str]:
        """Get available dimensions for dashboard."""
        pass


class IProcessingConfigService(abc.ABC):
    """Processing config service interface."""

    @abc.abstractmethod
    async def create_processing_config(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
        db: AsyncSession | None = None,
    ) -> ProcessingConfigRead:
        """Create processing config for dashboard."""
        pass

    @abc.abstractmethod
    async def get_processing_config_by_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> ProcessingConfigRead | None:
        """Get processing config by dashboard ID."""
        pass

    @abc.abstractmethod
    async def update_processing_config(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
        db: AsyncSession | None = None,
    ) -> ProcessingConfigRead | None:
        """Update processing config."""
        pass

    @abc.abstractmethod
    async def delete_processing_config(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete processing config."""
        pass


class IProcessingLogService(abc.ABC):
    """Processing log service interface."""

    @abc.abstractmethod
    async def create_processing_log(
        self,
        dashboard_id: UUID,
        status: str,
        message: str | None = None,
        db: AsyncSession | None = None,
    ) -> ProcessingLogRead:
        """Create processing log entry."""
        pass

    @abc.abstractmethod
    async def get_processing_logs_by_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[ProcessingLogRead]:
        """Get processing logs by dashboard ID."""
        pass

    @abc.abstractmethod
    async def get_processing_logs_by_status(
        self,
        status: str,
        db: AsyncSession | None = None,
    ) -> list[ProcessingLogRead]:
        """Get processing logs by status."""
        pass

    @abc.abstractmethod
    async def update_processing_log(
        self,
        log_id: UUID,
        status: str | None,
        message: str | None,
        finished_at: str | None,
        db: AsyncSession | None = None,
    ) -> ProcessingLogRead | None:
        """Update processing log entry."""
        pass

    @abc.abstractmethod
    async def delete_processing_log(
        self,
        log_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete processing log entry."""
        pass
