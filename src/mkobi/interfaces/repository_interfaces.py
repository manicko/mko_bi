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

    @classmethod
    @abc.abstractmethod
    async def get(cls, id: UUID, db: AsyncSession) -> Any | None:
        """Get object by ID."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_all(cls, db: AsyncSession) -> list[Any]:
        """Get all objects."""
        pass

    @classmethod
    @abc.abstractmethod
    async def create(cls, db: AsyncSession, **kwargs) -> Any | None:
        """Create new object."""
        pass

    @classmethod
    @abc.abstractmethod
    async def update(cls, id: UUID, db: AsyncSession, **kwargs) -> Any | None:
        """Update object."""
        pass

    @classmethod
    @abc.abstractmethod
    async def delete(cls, id: UUID, db: AsyncSession) -> bool:
        """Delete object."""
        pass


class IUserRepository(IRepository):
    """User repository interface."""

    @classmethod
    @abc.abstractmethod
    async def get_by_email(cls, email: str, db: AsyncSession) -> Any | None:
        """Get user by email."""
        pass


class IDashboardRepository(IRepository):
    """Dashboard repository interface."""

    @classmethod
    @abc.abstractmethod
    async def get_by_user(cls, user_id: UUID, db: AsyncSession) -> list[Any]:
        """Get dashboards by user (dashboards available to user)."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_by_name(cls, name: str, db: AsyncSession) -> Any | None:
        """Get dashboard by name."""
        pass


class IAccessRepository(abc.ABC):
    """Access repository interface."""

    @classmethod
    @abc.abstractmethod
    async def grant_access(
        cls,
        db: AsyncSession,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> Any | None:
        """Grant user access to dashboard."""
        pass

    @classmethod
    @abc.abstractmethod
    async def revoke_access(
        cls, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> bool:
        """Revoke user access to dashboard."""
        pass

    @classmethod
    @abc.abstractmethod
    async def check_access(
        cls, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> str | None:
        """Check user access level to dashboard."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_user_dashboards(cls, user_id: UUID, db: AsyncSession) -> list[Any]:
        """Get all dashboards available to user."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_all(cls, db: AsyncSession) -> list[Any]:
        """Get all access records."""
        pass


class IAggregatedDataRepository(IRepository):
    """Aggregated data repository interface."""

    @classmethod
    @abc.abstractmethod
    async def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Get aggregated data by dashboard ID."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_by_graph_id(cls, graph_id: UUID, db: AsyncSession) -> list[Any]:
        """Get aggregated data by graph ID."""
        pass


class IFilterRepository(IRepository):
    """Filter repository interface."""

    @classmethod
    @abc.abstractmethod
    async def get_by_name(cls, name: str, db: AsyncSession) -> Any | None:
        """Get filter by name."""
        pass


class IGraphRepository(IRepository):
    """Graph repository interface."""

    @classmethod
    @abc.abstractmethod
    async def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> list[Any]:
        """Get graphs by dashboard ID."""
        pass


class IProcessingConfigRepository(IRepository):
    """Processing config repository interface."""

    # Inherits get(id, db), get_all(db), create(db, **kwargs), update(id, db, **kwargs), delete(id, db)
    # Processing configs are retrieved via get(id) where id is dashboard_id


class IProcessingLogRepository(abc.ABC):
    """Processing log repository interface."""

    @classmethod
    @abc.abstractmethod
    async def create_log(
        cls,
        dashboard_id: UUID | None,
        status: Any,
        message: str | None,
        db: AsyncSession,
    ) -> Any:
        """Create new processing log."""
        pass

    @classmethod
    @abc.abstractmethod
    async def update_status(
        cls,
        log_id: UUID,
        status: Any,
        message: str | None,
        db: AsyncSession,
    ) -> None:
        """Update processing log status."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_by_dashboard(
        cls,
        dashboard_id: UUID | None,
        db: AsyncSession,
    ) -> list[Any]:
        """Get all processing logs for dashboard."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_filtered(
        cls,
        filters: Any,
        db: AsyncSession,
    ) -> list[Any]:
        """Get processing logs with filtering."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_latest_by_dashboard(
        cls,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> Any | None:
        """Get latest processing log for dashboard."""
        pass

    @classmethod
    @abc.abstractmethod
    async def get_by_id(
        cls,
        log_id: UUID,
        db: AsyncSession,
    ) -> Any | None:
        """Get log by ID."""
        pass
