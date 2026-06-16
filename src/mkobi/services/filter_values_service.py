"""Filter values service.

Provides business logic for retrieving dashboard filter values.
All operations are performed through injected repository.
"""

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.interfaces.repository_interfaces import IDashboardFilterValuesRepository

logger = logging.getLogger(__name__)


class FilterValuesService:
    """Service for filter values operations.

    Implements business logic for retrieving filter values from dashboards.
    Uses injected IDashboardFilterValuesRepository for data access.
    """

    def __init__(self, repo: IDashboardFilterValuesRepository) -> None:
        """Initialize service with injected repository.

        Args:
            repo: Dashboard filter values repository implementation.
        """
        self._repo = repo

    async def get_filter_values(
        self, dashboard_id: UUID, filter_name: str, db: AsyncSession
    ) -> list[str]:
        """Return distinct filter values for a dashboard filter.

        Args:
            dashboard_id: Dashboard identifier.
            filter_name: Name of the filter to get values for.
            db: Async database session.

        Returns:
            List of filter value strings.
        """
        logger.info(
            "Getting filter values: dashboard_id=%s, filter_name=%s",
            dashboard_id,
            filter_name,
        )
        values = await self._repo.get_filter_values(dashboard_id, filter_name, db)
        return values

    async def ensure_indexes(self, db: AsyncSession) -> None:
        """Create indexes on dashboard_filter_values table if they do not exist.

        This method is called during application startup to ensure indexes
        exist for optimal query performance. It uses CREATE INDEX IF NOT EXISTS
        which is idempotent and safe to run on every startup.

        Args:
            db: Async database session.
        """
        # Get dialect to check if we're running on PostgreSQL
        dialect: Dialect = db.bind().dialect

        if dialect.name == "postgresql":
            # Create unique index for idempotent writes
            await db.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_dashboard_filter_values "
                    "ON dashboard_filter_values (dashboard_id, filter_name, filter_value)"
                ),
            )
            # Create index for dashboard_id + filter_name lookups
            # (used in get_filter_values queries)
            await db.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_dashboard_filter_values_lookup "
                    "ON dashboard_filter_values (dashboard_id, filter_name)"
                ),
            )
            await db.commit()
            logger.info("Ensured indexes on dashboard_filter_values table")