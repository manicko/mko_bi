"""Repository for access control operations.

Provides methods for managing user access to dashboards.
All methods use contextual session management and handle errors.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.models import access as access_model
from mkobi.db.models import dashboard as dashboard_model
from mkobi.interfaces.repository_interfaces import IAccessRepository

logger = logging.getLogger(__name__)


class AccessRepository(IAccessRepository):
    """Repository for access control operations.

    Provides methods for managing user access to dashboards.
    All operations are performed within a separate database session
    with automatic transaction management.
    Implements IAccessRepository interface.
    """

    @classmethod
    async def grant_access(
        cls,
        db: AsyncSession,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> access_model.DashboardAccess | None:
        """Grant user access to dashboard.

        Args:
            user_id: User identifier (UUID).
            dashboard_id: Dashboard identifier (UUID).
            permission: Access level (view/edit/admin).
            db: Async database session.

        Returns:
            Access model or None on error.
        """
        try:
            result = await db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.user_id == user_id,
                    access_model.DashboardAccess.dashboard_id == dashboard_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.warning(
                    "Access already exists: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                return existing

            access_obj = access_model.DashboardAccess(
                user_id=user_id,
                dashboard_id=dashboard_id,
                permission=permission,
            )
            db.add(access_obj)
            await db.flush()
            await db.refresh(access_obj)
            logger.info(
                "Access granted: user_id=%s, dashboard_id=%s, permission=%s",
                user_id,
                dashboard_id,
                permission,
            )
            return access_obj
        except SQLAlchemyError as e:
            logger.error(
                "Error granting access user_id=%s, dashboard_id=%s: %s",
                user_id,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    async def revoke_access(cls, user_id: UUID, dashboard_id: UUID, db: AsyncSession) -> bool:
        """Revoke user access to dashboard.

        Args:
            user_id: User identifier (UUID).
            dashboard_id: Dashboard identifier (UUID).
            db: Async database session.

        Returns:
            True if access revoked, False if not found.
        """
        try:
            result = await db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.user_id == user_id,
                    access_model.DashboardAccess.dashboard_id == dashboard_id,
                )
            )
            access_obj = result.scalar_one_or_none()
            if not access_obj:
                logger.warning(
                    "Access not found for revocation: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                return False
            await db.delete(access_obj)
            await db.flush()
            logger.info(
                "Access revoked: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return True
        except SQLAlchemyError as e:
            logger.error(
                "Error revoking access user_id=%s, dashboard_id=%s: %s",
                user_id,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    async def check_access(
        cls, user_id: UUID, dashboard_id: UUID, db: AsyncSession
    ) -> str | None:
        """Check user access level to dashboard.

        Args:
            user_id: User identifier (UUID).
            dashboard_id: Dashboard identifier (UUID).
            db: Async database session.

        Returns:
            Access level (view/edit/admin) or None if no access.
        """
        try:
            result = await db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.user_id == user_id,
                    access_model.DashboardAccess.dashboard_id == dashboard_id,
                )
            )
            access_obj = result.scalar_one_or_none()
            if access_obj:
                permission: str = access_obj.permission
                logger.info(
                    "Access checked: user_id=%s, dashboard_id=%s, permission=%s",
                    user_id,
                    dashboard_id,
                    permission,
                )
                return permission
            logger.warning(
                "No access: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Error checking access user_id=%s, dashboard_id=%s: %s",
                user_id,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    async def get_user_dashboards(
        cls, user_id: UUID, db: AsyncSession
    ) -> list[dashboard_model.Dashboard]:
        """Get all dashboards available to user.

        Args:
            user_id: User identifier (UUID).
            db: Async database session.

        Returns:
            List of dashboards available to user.
        """
        try:
            result = await db.execute(
                select(dashboard_model.Dashboard)
                .join(access_model.DashboardAccess)
                .where(access_model.DashboardAccess.user_id == user_id)
            )
            dashboards = list(result.scalars().all())
            logger.info(
                "Dashboards retrieved for user id=%s, count: %s",
                user_id,
                len(dashboards),
            )
            return dashboards
        except SQLAlchemyError as e:
            logger.error(
                "Error getting dashboards for user id=%s: %s",
                user_id,
                e,
            )
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[access_model.DashboardAccess]:
        """Get all access records.

        Args:
            db: Async database session.

        Returns:
            List of all access records.
        """
        try:
            result = await db.execute(select(access_model.DashboardAccess))
            access_list = list(result.scalars().all())
            logger.info("Access list retrieved, count: %s", len(access_list))
            return access_list
        except SQLAlchemyError as e:
            logger.error("Error getting access list: %s", e)
            raise
