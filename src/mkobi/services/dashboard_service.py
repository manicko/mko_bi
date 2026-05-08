"""Dashboard management service.

Provides business logic for CRUD operations with dashboards.

All operations are performed through injected repositories with validation,
permission checking, and logging.

Implements IDashboardService interface for dependency injection.
"""

import json
import logging
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.models import dashboard as dashboard_model
from mkobi.db.models import access as access_model
from mkobi.db.session import get_session
from mkobi.interfaces.service_interfaces import IDashboardService
from mkobi.interfaces.repository_interfaces import (
    IDashboardRepository,
    IAccessRepository,
)
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.models.dashboard import (
    DashboardConfig,
    DashboardRead,
    DashboardUpdate,
)
from mkobi.models.enums import DashboardPermission, GraphType
from mkobi.models.layout import LayoutRead

logger = logging.getLogger(__name__)


class DashboardService(IDashboardService):
    """Dashboard service class."""

    def __init__(
        self,
        dashboard_repo: IDashboardRepository,
        access_repo: IAccessRepository | None = None,
    ) -> None:
        """Initialize service with injected repositories.

        Args:
            dashboard_repo: Dashboard repository instance.
            access_repo: Access repository instance (optional).
        """
        self.dashboard_repo = dashboard_repo
        self.access_repo = access_repo
        logger.debug("DashboardService initialized with injected repositories")

    async def create_dashboard(
        self,
        name: str,
        config: dict[str, Any],
        owner_id: UUID,
        db: AsyncSession | None = None,
    ) -> DashboardRead:
        """Create new dashboard.

        Args:
            name: Dashboard name.
            config: Dashboard configuration in JSON-compatible dict format.
            owner_id: Owner user identifier.
            db: Async database session.

        Returns:
            DashboardRead: Created dashboard model.

        Raises:
            ValueError: If configuration is incorrect.
            SQLAlchemyError: On database error.
        """
        if db is None:
            async with get_session() as db:
                return await self.create_dashboard(name, config, owner_id, db)

        config_obj = DashboardConfig(**config)
        self._validate_config(config_obj)

        try:
            # Create dashboard through repository
            dashboard_obj = await self.dashboard_repo.create(
                db=db,
                name=name,
                config=json.dumps(config_obj.model_dump()),
                created_by=owner_id,
            )

            if dashboard_obj is None:
                raise ValueError("Failed to create dashboard")

            logger.info(
                "Dashboard created: id=%s, name=%s",
                dashboard_obj.id,
                dashboard_obj.name,
            )

            # Grant admin permission to owner if access_repo is available
            if self.access_repo is not None:
                await self.access_repo.grant_access(
                    db=db,
                    user_id=owner_id,
                    dashboard_id=dashboard_obj.id,
                    permission=DashboardPermission.ADMIN,
                )

            logger.info(
                "Admin access granted: user_id=%s, dashboard_id=%s",
                owner_id,
                dashboard_obj.id,
            )

            # Commit the transaction
            await db.commit()
            logger.info("Transaction committed for dashboard id=%s", dashboard_obj.id)

            # Convert to Pydantic model with layout data
            return await self._dashboard_to_read(dashboard_obj, db)

        except ValueError:
            # Validation errors don't require rollback (transaction not started)
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Error creating dashboard name=%s, owner_id=%s: %s",
                name,
                owner_id,
                e,
            )
            raise

    async def get_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> DashboardRead | None:
        """Get dashboard by ID with access check.

        Args:
            dashboard_id: Dashboard ID.
            user_id: User ID requesting access.
            db: Async database session.

        Returns:
            DashboardRead if access allowed, else None.
        """
        if db is None:
            async with get_session() as db:
                return await self.get_dashboard(dashboard_id, user_id, db)
        
        # Check dashboard existence
        dashboard_obj = await self.dashboard_repo.get(dashboard_id, db)
        if dashboard_obj is None:
            logger.warning("Dashboard not found: id=%s", dashboard_id)
            return None

        # Check user access if access_repo is available
        permission = None
        if self.access_repo is not None:
            permission = await self.access_repo.check_access(user_id, dashboard_id, db)
        
        if permission is None:
            logger.warning(
                "Access denied: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return None

        logger.info(
            "Dashboard accessed: id=%s, user_id=%s, permission=%s",
            dashboard_id,
            user_id,
            permission,
        )

        # Convert to Pydantic model with layout data
        return await self._dashboard_to_read(dashboard_obj, db)

    async def get_dashboard_by_name(
        self,
        name: str,
        db: AsyncSession | None = None,
    ) -> DashboardRead | None:
        """Get dashboard by name.

        Args:
            name: Dashboard name.
            db: Async database session.

        Returns:
            DashboardRead or None if not found.
        """
        if db is None:
            async with get_session() as db:
                return await self.get_dashboard_by_name(name, db)
        
        dashboard = await self.dashboard_repo.get_by_name(name, db)
        if dashboard is None:
            return None
        return await self._dashboard_to_read(dashboard, db)

    async def get_user_dashboards(
        self,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[DashboardRead]:
        """Get user dashboards.

        Args:
            user_id: User ID.
            db: Async database session.

        Returns:
            list[DashboardRead]: List of user dashboards.
        """
        if db is None:
            async with get_session() as db:
                return await self.get_user_dashboards(user_id, db)
        
        dashboards = await self.dashboard_repo.get_by_user(user_id, db)
        result = []
        for dashboard in dashboards:
            result.append(await self._dashboard_to_read(dashboard, db))
        return result

    async def update_dashboard(
        self,
        dashboard_id: UUID,
        update_data: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> DashboardRead | None:
        """Update dashboard.

        Args:
            dashboard_id: Dashboard ID.
            update_data: Data for update (config, layout_id, etc.).
            config: Configuration (optional, for backward compatibility).
            db: Async database session.

        Returns:
            DashboardRead or None if not found.
        """
        if db is None:
            async with get_session() as db:
                return await self.update_dashboard(dashboard_id, update_data, config, db)
        
        # Handle config parameter if provided
        if config is not None:
            if update_data is None:
                update_data = {"config": config}
            elif isinstance(update_data, dict):
                update_data["config"] = config
            else:
                update_data = update_data.model_dump(exclude_unset=True)
                update_data["config"] = config

        if not update_data:
            logger.warning(
                "No data for dashboard update: dashboard_id=%s", dashboard_id
            )
            return None

        # Validate configuration if provided
        config_to_validate = None
        if update_data:
            if isinstance(update_data, dict):
                config_to_validate = update_data.get("config")
            else:
                config_to_validate = update_data.config

        if config_to_validate:
            if isinstance(config_to_validate, dict):
                config_to_validate = DashboardConfig(**config_to_validate)
            self._validate_config(config_to_validate)

        updated = await self.dashboard_repo.update(
            dashboard_id,
            db,
            **update_data,
        )
        if updated is None:
            return None
        await db.commit()

        return await self._dashboard_to_read(updated, db)

    async def delete_dashboard(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete dashboard.

        Args:
            dashboard_id: Dashboard ID.
            db: Async database session.

        Returns:
            bool: True if deletion successful.
        """
        if db is None:
            async with get_session() as db:
                return await self.delete_dashboard(dashboard_id, db)
        
        result = await self.dashboard_repo.delete(dashboard_id, db)
        await db.commit()
        return bool(result)

    async def get_all_dashboards(
        self,
        db: AsyncSession | None = None,
    ) -> list[DashboardRead]:
        """Get all dashboards.

        Args:
            db: Async database session.

        Returns:
            list[DashboardRead]: List of all dashboards.
        """
        if db is None:
            async with get_session() as db:
                return await self.get_all_dashboards(db)
        
        dashboards = await self.dashboard_repo.get_all(db)
        result = []
        for dashboard in dashboards:
            result.append(await self._dashboard_to_read(dashboard, db))
        return result

    async def grant_access(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        permission: str,
        db: AsyncSession | None = None,
    ) -> bool:
        """Grant user access to dashboard.

        Args:
            dashboard_id: Dashboard ID.
            user_id: User ID.
            permission: Access level.
            db: Async database session.

        Returns:
            bool: True if access granted.
        """
        if db is None:
            async with get_session() as db:
                return await self.grant_access(dashboard_id, user_id, permission, db)
        
        self._validate_permission(permission)

        # Check dashboard existence
        dashboard_obj = await self.dashboard_repo.get(dashboard_id, db)
        if dashboard_obj is None:
            raise ValueError(f"Dashboard with id={dashboard_id} not found")

        if self.access_repo is None:
            raise ValueError("access_repo is required for grant_access")

        # Grant access through repository
        await self.access_repo.grant_access(
            db=db,
            user_id=user_id,
            dashboard_id=dashboard_id,
            permission=permission,
        )

        await db.commit()

        logger.info(
            "Access granted: user_id=%s, dashboard_id=%s, permission=%s",
            user_id,
            dashboard_id,
            permission,
        )

        return True

    async def revoke_access(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Revoke user access to dashboard.

        Args:
            dashboard_id: Dashboard ID.
            user_id: User ID.
            db: Async database session.

        Returns:
            True if access was revoked, False if record not found.
        """
        if db is None:
            async with get_session() as db:
                return await self.revoke_access(dashboard_id, user_id, db)
        
        if self.access_repo is None:
            raise ValueError("access_repo is required for revoke_access")

        result = await self.access_repo.revoke_access(
            user_id=user_id, dashboard_id=dashboard_id, db=db
        )

        if result:
            await db.commit()
            logger.info(
                "Access revoked: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
        else:
            logger.warning(
                "Access record not found for revocation: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )

        return bool(result)

    async def get_dashboard_access_list(
        self,
        dashboard_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """Get all access records for a dashboard.

        Args:
            dashboard_id: Dashboard ID.
            db: Database session.

        Returns:
            List of access records as dictionaries.
        """
        if db is None:
            async with get_session() as db:
                return await self.get_dashboard_access_list(dashboard_id, db)
        
        try:
            result = await db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.dashboard_id == dashboard_id
                )
            )
            access_records = list(result.scalars().all())

            return [
                {
                    "user_id": str(record.user_id),
                    "dashboard_id": str(record.dashboard_id),
                    "permission": record.permission,
                }
                for record in access_records
            ]
        except Exception as e:
            logger.error(
                "Error getting access list for dashboard id=%s: %s",
                dashboard_id,
                e,
            )
            raise

    # --- Helper methods ---

    def _validate_permission(self, permission: str) -> None:
        """Validate that access level is allowed."""
        normalized = permission
        if permission == "read":
            normalized = "view"
        elif permission == "write":
            normalized = "edit"

        try:
            DashboardPermission(normalized)
        except ValueError as err:
            logger.error(
                "Invalid access level: '%s'. Allowed: %s",
                permission,
                sorted([e.value for e in DashboardPermission]),
            )
            raise ValueError(
                f"Invalid access level: '{permission}'. "
                f"Allowed values: {', '.join(sorted([e.value for e in DashboardPermission]))}"
            ) from err

    def _validate_config(self, config: DashboardConfig) -> None:
        """Validate dashboard configuration."""
        if not config.graph_types:
            logger.error("Dashboard configuration missing graph types")
            raise ValueError(
                "Dashboard configuration must contain at least one graph type"
            )

        for graph_type in config.graph_types:
            try:
                GraphType(graph_type)
            except ValueError as err:
                logger.error("Invalid graph type: '%s'", graph_type)
                raise ValueError(
                    f"Invalid graph type: '{graph_type}'. "
                    f"Allowed values: {', '.join([e.value for e in GraphType])}"
                ) from err

    async def _dashboard_to_read(
        self, dashboard_obj: dashboard_model.Dashboard, db: AsyncSession
    ) -> DashboardRead:
        """Convert dashboard model to Pydantic DashboardRead model."""
        # Handle config which might be None or a JSON string
        config_data = getattr(dashboard_obj, "config", None)
        if config_data is None:
            config = DashboardConfig(graph_types=[], metrics=[], dimensions=[])
        elif isinstance(config_data, dict):
            config = DashboardConfig(**config_data)
        else:
            # Assume it's a JSON string
            config = DashboardConfig(**json.loads(config_data))

        dashboard_dict = {
            "id": dashboard_obj.id,
            "name": dashboard_obj.name,
            "description": getattr(dashboard_obj, "description", None),
            "config": config,
            "layout_id": getattr(dashboard_obj, "layout_id", None),
            "created_at": dashboard_obj.created_at,
            "updated_at": getattr(dashboard_obj, "updated_at", None),
        }
        # Add layout if present
        if getattr(dashboard_obj, "layout", None):
            dashboard_dict["layout"] = LayoutRead.model_validate(dashboard_obj.layout)
        return cast(DashboardRead, DashboardRead.model_validate(dashboard_dict))


# --- Backward compatibility functions ---


async def create_dashboard(
    name: str,
    config: dict[str, Any],
    owner_id: UUID,
    db: AsyncSession,
) -> DashboardRead:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.access_repo import AccessRepository

    service = DashboardService(DashboardRepository(), AccessRepository())
    return await service.create_dashboard(name, config, owner_id, db)


async def get_dashboard(
    dashboard_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> DashboardRead | None:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.access_repo import AccessRepository

    service = DashboardService(DashboardRepository(), AccessRepository())
    return await service.get_dashboard(dashboard_id, user_id, db)


async def get_dashboard_by_name(
    name: str,
    db: AsyncSession,
) -> DashboardRead | None:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository

    service = DashboardService(DashboardRepository(), None)
    return await service.get_dashboard_by_name(name, db)


async def get_user_dashboards(
    user_id: UUID,
    db: AsyncSession,
) -> list[DashboardRead]:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository

    service = DashboardService(DashboardRepository(), None)
    return await service.get_user_dashboards(user_id, db)


async def update_dashboard(
    dashboard_id: UUID,
    update_data: dict[str, Any] | DashboardUpdate | None = None,
    config: dict[str, Any] | None = None,
    db: AsyncSession | None = None,
) -> DashboardRead | None:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.access_repo import AccessRepository

    service = DashboardService(DashboardRepository(), AccessRepository())
    return await service.update_dashboard(dashboard_id, update_data, config, db)


async def delete_dashboard(
    dashboard_id: UUID,
    db: AsyncSession,
) -> bool:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository

    service = DashboardService(DashboardRepository(), None)
    return await service.delete_dashboard(dashboard_id, db)


async def get_all_dashboards(
    db: AsyncSession,
) -> list[DashboardRead]:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository

    service = DashboardService(DashboardRepository(), None)
    return await service.get_all_dashboards(db)


async def grant_access(
    dashboard_id: UUID,
    user_id: UUID,
    permission: str,
    db: AsyncSession,
) -> bool:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.access_repo import AccessRepository

    service = DashboardService(DashboardRepository(), AccessRepository())
    return await service.grant_access(dashboard_id, user_id, permission, db)


async def revoke_access(
    dashboard_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> bool:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.access_repo import AccessRepository

    service = DashboardService(DashboardRepository(), AccessRepository())
    return await service.revoke_access(dashboard_id, user_id, db)


async def get_dashboard_access_list(
    dashboard_id: UUID,
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Backward compatibility wrapper."""
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.access_repo import AccessRepository

    service = DashboardService(DashboardRepository(), AccessRepository())
    return await service.get_dashboard_access_list(dashboard_id, db)
