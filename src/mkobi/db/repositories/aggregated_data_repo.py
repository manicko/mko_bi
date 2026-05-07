"""Repository for aggregated data operations.

Provides methods for managing dashboard aggregated data.
All methods use contextual session management and handle errors.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import delete, insert, select, distinct
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.models import aggregated_data as aggregated_data_model
from mkobi.interfaces.repository_interfaces import IAggregatedDataRepository

logger = logging.getLogger(__name__)


class AggregatedDataRepository(IAggregatedDataRepository):
    """Repository for aggregated data operations.

    Provides methods for saving, reading and deleting
    aggregated data. All operations are performed within a
    separate database session with automatic transaction management.
    Implements IAggregatedDataRepository interface.
    """
    async def bulk_insert(
        cls,
        db: AsyncSession,
        dashboard_id: UUID,
        records: list[dict[str, Any]],
        clear_old: bool = True,
    ) -> int:
        """Perform batch insert of aggregated data.

        Operation is performed in transaction:
        1. If clear_old=True, old data is deleted by dashboard_id
        2. Batch insert of new data is performed
        3. Transaction is rolled back on error

        Args:
            db: Async database session.
            dashboard_id: Dashboard identifier.
            records: List of aggregated data for insertion.
                Each item must contain:
                - graph_id: UUID of the graph
                - dims: dict of dimension values (JSON)
                - metrics: dict of metric values (JSON)
            clear_old: Whether to delete old data (default True).

        Returns:
            Number of inserted records.
        """
        try:
            if clear_old:
                await db.execute(
                    delete(aggregated_data_model.AggregatedData).where(
                        aggregated_data_model.AggregatedData.dashboard_id == dashboard_id
                    )
                )

            if not records:
                logger.info("No data to insert: dashboard_id=%s", dashboard_id)
                return 0

            # Prepare data for insertion
            insert_data = []
            for item in records:
                insert_data.append({
                    "dashboard_id": dashboard_id,
                    "graph_id": item["graph_id"],
                    "dims": item["dims"],
                    "metrics": item["metrics"],
                })

            await db.execute(
                insert(aggregated_data_model.AggregatedData),
                insert_data,
            )

            count = len(insert_data)
            logger.info(
                "Data inserted: dashboard_id=%s, count=%s",
                dashboard_id,
                count,
            )
            return count
        except SQLAlchemyError as e:
            logger.error(
                "Error inserting data dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    async def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> list[aggregated_data_model.AggregatedData]:
        """Get aggregated data for dashboard.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.

        Returns:
            List of aggregated data for dashboard.
        """
        try:
            result = await db.execute(
                select(aggregated_data_model.AggregatedData)
                .where(aggregated_data_model.AggregatedData.dashboard_id == dashboard_id)
            )
            data = list(result.scalars().all())
            logger.info(
                "Data retrieved for dashboard_id=%s, count=%s",
                dashboard_id,
                len(data),
            )
            return data
        except SQLAlchemyError as e:
            logger.error(
                "Error getting data dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    async def get_by_graph_id(
        cls,
        graph_id: UUID,
        db: AsyncSession,
        filters: dict[str, Any] | None = None,
    ) -> list[aggregated_data_model.AggregatedData]:
        """Get aggregated data for graph.

        Args:
            graph_id: Graph identifier (UUID).
            db: Async database session.
            filters: Optional dictionary of filters for JSONB field dims.

        Returns:
            List of data points for graph.
        """
        try:
            query = select(aggregated_data_model.AggregatedData).where(
                aggregated_data_model.AggregatedData.graph_id == graph_id
            )

            # Apply filters to JSONB field dims
            if filters:
                for key, value in filters.items():
                    query = query.where(
                        aggregated_data_model.AggregatedData.dims[key].astext == str(value)
                    )

            result = await db.execute(query)
            data = list(result.scalars().all())
            logger.info(
                "Data retrieved for graph_id=%s, count=%s",
                graph_id,
                len(data),
            )
            return data
        except SQLAlchemyError as e:
            logger.error(
                "Error getting data graph_id=%s: %s",
                graph_id,
                e,
            )
            raise
    async def delete_by_graph_id(
        cls,
        graph_id: UUID,
        db: AsyncSession,
    ) -> int:
        """Delete aggregated data for graph.

        Args:
            graph_id: Graph identifier.
            db: Async database session.

        Returns:
            Number of deleted records.
        """
        try:
            result = await db.execute(
                delete(aggregated_data_model.AggregatedData)
                .where(aggregated_data_model.AggregatedData.graph_id == graph_id)
            )
            count = result.rowcount if hasattr(result, 'rowcount') else 0
            logger.info(
                "Data deleted: graph_id=%s, count=%s",
                graph_id,
                count,
            )
            return count
        except SQLAlchemyError as e:
            logger.error(
                "Error deleting data graph_id=%s: %s",
                graph_id,
                e,
            )
            raise
    async def delete_by_dashboard_id(
        cls,
        dashboard_id: UUID,
        db: AsyncSession,
    ) -> int:
        """Delete all aggregated data for dashboard.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.

        Returns:
            Number of deleted records.
        """
        try:
            result = await db.execute(
                delete(aggregated_data_model.AggregatedData)
                .where(aggregated_data_model.AggregatedData.dashboard_id == dashboard_id)
            )
            count = result.rowcount if hasattr(result, 'rowcount') else 0
            logger.info(
                "Data deleted: dashboard_id=%s, count=%s",
                dashboard_id,
                count,
            )
            return count
        except SQLAlchemyError as e:
            logger.error(
                "Error deleting data dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    async def get_dims_values(
        cls,
        graph_id: UUID,
        dim_name: str,
        db: AsyncSession,
    ) -> list[str]:
        """Get unique dimension values for graph.

        Used to get filter value lists.
        Extracts unique values from JSONB field dims.

        Args:
            graph_id: Graph identifier.
            dim_name: Dimension name (field in JSONB dims).
            db: Async database session.

        Returns:
            List of unique dimension values.
        """
        try:
            # Extract dim_name values from JSONB field dims
            result = await db.execute(
                select(distinct(
                    aggregated_data_model.AggregatedData.dims[dim_name].astext
                )).where(
                    aggregated_data_model.AggregatedData.graph_id == graph_id
                )
            )
            values = [row[0] for row in result if row[0] is not None]
            logger.info(
                "Dimension values retrieved: graph_id=%s, dim_name=%s, count=%s",
                graph_id,
                dim_name,
                len(values),
            )
            return values
        except SQLAlchemyError as e:
            logger.error(
                "Error getting dimension values graph_id=%s: %s",
                graph_id,
                e,
            )
            raise
