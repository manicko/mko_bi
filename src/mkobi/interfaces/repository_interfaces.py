"""Abstract interfaces for repositories.

Defines contracts for all repositories in the system.
Used for dependency injection and breaking cyclic imports.
"""

import abc
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class IRepository(abc.ABC):
    """Base repository interface."""

    @abc.abstractmethod
    async def get(self, id: UUID, db: AsyncSession) -> Any | None:
        """Get object by ID."""
        pass

    @abc.abstractmethod
    async def get_all(self, db: AsyncSession) -> list[Any]:
        """Get all objects."""
        pass

    @abc.abstractmethod
    async def create(self, db: AsyncSession, **kwargs) -> Any | None:
        """Create new object."""
        pass

    @abc.abstractmethod
    async def update(self, id: UUID, db: AsyncSession, **kwargs) -> Any | None:
        """Update object."""
        pass

    @abc.abstractmethod
    async def delete(self, id: UUID, db: AsyncSession) -> bool:
        """Delete object."""
        pass


class IUserRepository(IRepository):
    """User repository interface."""

    @abc.abstractmethod
    async def get_by_email(self, email: str, db: AsyncSession) -> Any | None:
        """Get user by email."""
        pass

    @abc.abstractmethod
    async def get_by_email_with_hash(self, email: str, db: AsyncSession) -> Any | None:
        """Get user by email with password hash."""
        pass

    @abc.abstractmethod
    async def get_with_hash(self, id: UUID, db: AsyncSession) -> Any | None:
        """Get user by ID with password hash."""
        pass


class IDashboardRepository(IRepository):
    """Dashboard repository interface."""

    @abc.abstractmethod
    async def get_by_user(self, user_id: UUID, db: AsyncSession) -> list[Any]:
        """Get dashboards by user (dashboards available to user)."""
        pass

    @abc.abstractmethod
    async def get_by_name(self, name: str, db: AsyncSession) -> Any | None:
        """Get dashboard by name."""
        pass


class IAccessRepository(abc.ABC):
    """Access repository interface."""

    @abc.abstractmethod
    async def grant_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> Any | None:
        """Grant user access to dashboard."""
        pass

    @abc.abstractmethod
    async def revoke_access(
        self, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> bool:
        """Revoke user access to dashboard."""
        pass

    @abc.abstractmethod
    async def check_access(
        self, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> str | None:
        """Check user access level to dashboard."""
        pass

    @abc.abstractmethod
    async def get_user_dashboards(self, user_id: UUID, db: AsyncSession) -> list[Any]:
        """Get all dashboards available to user."""
        pass

    @abc.abstractmethod
    async def get_all(self, db: AsyncSession) -> list[Any]:
        """Get all access records."""
        pass


class IRegistrationRequestRepository(abc.ABC):
    """Registration request repository interface."""

    @abc.abstractmethod
    async def create(
        self, email: str, ip: str | None, db: AsyncSession
    ) -> Any | None:
        """Create new registration request."""
        pass

    @abc.abstractmethod
    async def get_by_email(self, email: str, db: AsyncSession) -> Any | None:
        """Get registration request by email."""
        pass

    @abc.abstractmethod
    async def get_all(self, db: AsyncSession) -> list[Any]:
        """Get all registration requests."""
        pass

    @abc.abstractmethod
    async def update_status(
        self, request_id: UUID, status: str, db: AsyncSession
    ) -> Any | None:
        """Update registration request status."""
        pass

    @abc.abstractmethod
    async def delete(self, request_id: UUID, db: AsyncSession) -> bool:
        """Delete registration request."""
        pass


class IAggregatedDataRepository(abc.ABC):
    """Aggregated data repository interface."""

    @abc.abstractmethod
    async def bulk_insert(
        self,
        db: AsyncSession,
        dashboard_id: UUID,
        records: list[dict[str, Any]],
        clear_old: bool = True,
    ) -> int:
        """Perform batch insert of aggregated data."""
        pass

    @abc.abstractmethod
    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Get aggregated data for dashboard."""
        pass

    @abc.abstractmethod
    async def get_by_graph_id(
        self,
        graph_id: UUID,
        db: AsyncSession,
        filters: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Get aggregated data for graph."""
        pass

    @abc.abstractmethod
    async def delete_by_graph_id(
        self,
        graph_id: UUID,
        db: AsyncSession,
    ) -> int:
        """Delete aggregated data for graph."""
        pass

    @abc.abstractmethod
    async def delete_by_dashboard_id(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> int:
        """Delete all aggregated data for dashboard."""
        pass

    @abc.abstractmethod
    async def get_dims_values(
        self,
        graph_id: UUID,
        dim_name: str,
        db: AsyncSession,
    ) -> list[str]:
        """Get unique dimension values for graph."""
        pass


class ILayoutRepository(IRepository):
    """Layout repository interface."""

    @abc.abstractmethod
    async def get_by_name(self, name: str, db: AsyncSession) -> Any | None:
        """Get layout by name."""
        pass


class IFilterRepository(IRepository):
    """Filter repository interface."""

    @abc.abstractmethod
    async def get_by_name(self, name: str, db: AsyncSession) -> Any | None:
        """Get filter by name."""
        pass


class IGraphRepository(IRepository):
    """Graph repository interface."""

    @abc.abstractmethod
    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Get graphs by dashboard ID."""
        pass

    @abc.abstractmethod
    async def get_by_name_and_dashboard(
        self, name: str, dashboard_id: UUID, db: AsyncSession
    ) -> Any | None:
        """Get graph by name and dashboard ID."""
        pass


class IProcessingConfigRepository(IRepository):
    """Processing config repository interface."""

    # Inherits get(id, db), get_all(db), create(db, **kwargs), update(id, db, **kwargs), delete(id, db)
    # Processing configs are retrieved via get(id) where id is dashboard_id


class IProcessingLogRepository(abc.ABC):
    """Processing log repository interface."""

    @abc.abstractmethod
    async def create_log(
        self,
        dashboard_id: UUID | None,
        status: Any,
        message: str | None,
        db: AsyncSession,
    ) -> Any:
        """Create new processing log."""
        pass

    @abc.abstractmethod
    async def update_status(
        self,
        log_id: UUID,
        status: Any,
        message: str | None,
        db: AsyncSession,
    ) -> None:
        """Update processing log status."""
        pass

    @abc.abstractmethod
    async def get_by_dashboard(
        self,
        dashboard_id: UUID | None,
        db: AsyncSession,
    ) -> list[Any]:
        """Get all processing logs for dashboard."""
        pass

    @abc.abstractmethod
    async def get_filtered(
        self,
        filters: Any,
        db: AsyncSession,
    ) -> list[Any]:
        """Get processing logs with filtering."""
        pass

    @abc.abstractmethod
    async def get_latest_by_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> Any | None:
        """Get latest processing log for dashboard."""
        pass

    @abc.abstractmethod
    async def get_by_id(
        self,
        log_id: UUID,
        db: AsyncSession,
    ) -> Any | None:
        """Get log by ID."""
        pass

    @abc.abstractmethod
    async def delete(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """Delete processing logs by dashboard ID."""
        pass
