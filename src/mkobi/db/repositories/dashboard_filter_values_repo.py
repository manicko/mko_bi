"""Repository for dashboard filter values operations.

Provides CRUD methods for DashboardFilterValue model.
All methods use contextual session management and handle errors.
"""

import logging
from typing import cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.models.dashboard_filter_values import DashboardFilterValue
from mkobi.interfaces.repository_interfaces import IDashboardFilterValuesRepository

logger = logging.getLogger(__name__)


class DashboardFilterValuesRepository(IDashboardFilterValuesRepository):
    """Repository for dashboard filter values operations.

    Provides methods for retrieving, saving and clearing filter values
    in the database. All operations are performed within a separate session
    with automatic transaction management.
    Implements IDashboardFilterValuesRepository interface.
    """

    async def get_filter_values(
        self, dashboard_id: UUID, filter_name: str, db: AsyncSession
    ) -> list[str]:
        """Get filter values by dashboard ID and filter name.

        Args:
            dashboard_id: Dashboard identifier (UUID).
            filter_name: Name of the filter.
            db: Async database session.

        Returns:
            List of filter_value strings, ordered by filter_value.
        """
        try:
            result = await db.execute(
                select(DashboardFilterValue.filter_value)
                .where(
                    DashboardFilterValue.dashboard_id == dashboard_id,
                    DashboardFilterValue.filter_name == filter_name,
                )
                .order_by(DashboardFilterValue.filter_value)
            )
            values = cast(list[str], result.scalars().all())
            logger.info(
                "Filter values retrieved: dashboard_id=%s, filter_name=%s, count=%s",
                dashboard_id,
                filter_name,
                len(values),
            )
            return values
        except SQLAlchemyError as e:
            logger.error(
                "Error getting filter values: dashboard_id=%s, filter_name=%s: %s",
                dashboard_id,
                filter_name,
                e,
            )
            raise

    async def save_filter_values(
        self, dashboard_id: UUID, filter_name: str, values: list[str], db: AsyncSession
    ) -> int:
        """Save filter values (clear-then-insert for idempotency).

        Args:
            dashboard_id: Dashboard identifier (UUID).
            filter_name: Name of the filter.
            values: List of filter values to save.
            db: Async database session.

        Returns:
            Count of inserted values.
        """
        try:
            # Clear existing values for this (dashboard_id, filter_name) combination
            await self._clear_filter_values(
                dashboard_id, filter_name, db
            )

            # Bulk insert new values
            for value in values:
                db.add(
                    DashboardFilterValue(
                        dashboard_id=dashboard_id,
                        filter_name=filter_name,
                        filter_value=value,
                    )
                )

            await db.flush()
            logger.info(
                "Filter values saved: dashboard_id=%s, filter_name=%s, count=%s",
                dashboard_id,
                filter_name,
                len(values),
            )
            return len(values)
        except SQLAlchemyError as e:
            logger.error(
                "Error saving filter values: dashboard_id=%s, filter_name=%s: %s",
                dashboard_id,
                filter_name,
                e,
            )
            raise

    async def _clear_filter_values(
        self, dashboard_id: UUID, filter_name: str, db: AsyncSession
    ) -> int:
        """Clear filter values for specific filter.

        Args:
            dashboard_id: Dashboard identifier (UUID).
            filter_name: Name of the filter.
            db: Async database session.

        Returns:
            Count of deleted rows.
        """
        result = await db.execute(
            delete(DashboardFilterValue).where(
                DashboardFilterValue.dashboard_id == dashboard_id,
                DashboardFilterValue.filter_name == filter_name,
            )
        )
        return result.rowcount or 0

    async def clear_dashboard_values(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> int:
        """Clear all filter values for a dashboard.

        Args:
            dashboard_id: Dashboard identifier (UUID).
            db: Async database session.

        Returns:
            Count of deleted rows.
        """
        try:
            result = await db.execute(
                delete(DashboardFilterValue).where(
                    DashboardFilterValue.dashboard_id == dashboard_id
                )
            )
            deleted_count = result.rowcount or 0
            logger.info(
                "Dashboard filter values cleared: dashboard_id=%s, count=%s",
                dashboard_id,
                deleted_count,
            )
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(
                "Error clearing dashboard filter values: dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise