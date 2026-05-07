"""Graph management service.

Provides business logic for CRUD operations with graphs.

All operations are performed through IGraphRepository with validation and logging.
"""

import logging
from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.session import get_session
from mkobi.interfaces.repository_interfaces import IGraphRepository
from mkobi.interfaces.service_interfaces import IGraphService
from mkobi.models.graph import GraphCreate, GraphRead, GraphUpdate
from mkobi.models.enums import GraphType

logger = logging.getLogger(__name__)


class GraphService(IGraphService):
    """Graph service for working with graphs.

    Implements IGraphService interface and uses IGraphRepository
    for data access.
    """

    def __init__(self, repository_cls: type[IGraphRepository]):
        """Initialize service with repository class.

        Args:
            repository_cls: Graph repository class.
        """
        self._repository_cls = repository_cls
        logger.info(
            "GraphService initialized with repository: %s", repository_cls.__name__
        )

    async def _to_read_model(self, graph_obj) -> GraphRead:
        """Convert DB object to Pydantic model.

        Args:
            graph_obj: Graph object from DB.

        Returns:
            GraphRead model.
        """
        return cast(GraphRead, GraphRead.model_validate(graph_obj))

    async def _validate_graph_data(self, data: GraphCreate) -> None:
        """Validate graph data.

        Args:
            data: Data to validate.

        Raises:
            ValueError: On incorrect data.
        """
        if not data.name or not data.name.strip():
            raise ValueError("Graph name cannot be empty")

        try:
            GraphType(data.type)
        except ValueError as e:
            logger.error("Invalid graph type: '%s'", data.type)
            raise ValueError(
                f"Invalid graph type: '{data.type}'. "
                f"Allowed values: {', '.join([e.value for e in GraphType])}"
            ) from e

    async def create(
        self, data: GraphCreate, db: AsyncSession | None = None
    ) -> GraphRead:
        """Create new graph.

        Args:
            data: Graph creation data.
            db: Optional async session.

        Returns:
            GraphRead: Created graph model.

        Raises:
            ValueError: On incorrect data.
        """
        logger.info(
            "Creating graph: name=%s, dashboard_id=%s", data.name, data.dashboard_id
        )
        await self._validate_graph_data(data)

        if db is None:
            async with get_session() as db:
                return await self.create(data, db=db)

        repo = self._repository_cls(db)
        graph_obj = await repo.create(
            name=data.name,
            type=data.type,
            dashboard_id=data.dashboard_id,
            config=data.config,
            dimensions=data.dimensions,
            metrics=data.metrics,
        )
        await db.commit()
        logger.info("Graph created: id=%s, name=%s", graph_obj.id, graph_obj.name)
        return await self._to_read_model(graph_obj)

    async def get(
        self, graph_id: UUID, db: AsyncSession | None = None
    ) -> GraphRead | None:
        """Get graph by ID.

        Args:
            graph_id: Graph identifier.
            db: Optional async session.

        Returns:
            GraphRead or None if not found.
        """
        logger.info("Getting graph: id=%s", graph_id)

        if db is None:
            async with get_session() as db:
                return await self.get(graph_id, db=db)

        repo = self._repository_cls(db)
        graph_obj = await repo.get(graph_id)
        if graph_obj is None:
            logger.warning("Graph not found: id=%s", graph_id)
            return None
        return await self._to_read_model(graph_obj)

    async def update(
        self, graph_id: UUID, data: GraphUpdate, db: AsyncSession | None = None
    ) -> GraphRead | None:
        """Update graph.

        Args:
            graph_id: Graph identifier.
            data: Update data.
            db: Optional async session.

        Returns:
            GraphRead or None if not found.
        """
        logger.info("Updating graph: id=%s", graph_id)

        if db is None:
            async with get_session() as db:
                return await self.update(graph_id, data, db=db)

        repo = self._repository_cls(db)
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.type is not None:
            update_data["type"] = data.type
        if data.config is not None:
            update_data["config"] = data.config
        if data.dimensions is not None:
            update_data["dimensions"] = data.dimensions
        if data.metrics is not None:
            update_data["metrics"] = data.metrics

        graph_obj = await repo.update(graph_id, **update_data)
        if graph_obj is None:
            logger.warning("Graph not found for update: id=%s", graph_id)
            return None
        await db.commit()
        logger.info("Graph updated: id=%s", graph_id)
        return await self._to_read_model(graph_obj)

    async def delete(self, graph_id: UUID, db: AsyncSession | None = None) -> bool:
        """Delete graph.

        Args:
            graph_id: Graph identifier.
            db: Optional async session.

        Returns:
            True if deletion successful, False if not found.
        """
        logger.info("Deleting graph: id=%s", graph_id)

        if db is None:
            async with get_session() as db:
                return await self.delete(graph_id, db=db)

        repo = self._repository_cls(db)
        result: bool = await repo.delete(graph_id)
        if result:
            await db.commit()
            logger.info("Graph deleted: id=%s", graph_id)
        else:
            logger.warning("Graph not found for deletion: id=%s", graph_id)
        return result

    async def list_by_dashboard(
        self, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> list[GraphRead]:
        """Get graphs by dashboard ID.

        Args:
            dashboard_id: Dashboard identifier.
            db: Optional async session.

        Returns:
            List of graphs for the dashboard.
        """
        logger.info("Getting graphs for dashboard: dashboard_id=%s", dashboard_id)

        if db is None:
            async with get_session() as db:
                return await self.list_by_dashboard(dashboard_id, db=db)

        repo = self._repository_cls(db)
        graph_objs = await repo.get_by_dashboard_id(dashboard_id)
        return [await self._to_read_model(g) for g in graph_objs]

    # Implementation of IGraphService interface methods
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
        """Create new graph (IgraphService interface method)."""
        data = GraphCreate(
            name=name,
            type=type_,
            dashboard_id=dashboard_id,
            config=config,
            dimensions=dimensions,
            metrics=metrics,
        )
        return await self.create(data, db=db)

    async def get_graph_by_id(
        self, graph_id: UUID, db: AsyncSession | None = None
    ) -> GraphRead | None:
        """Get graph by ID (IgraphService interface method)."""
        return await self.get(graph_id, db=db)

    async def get_graph_by_name_and_dashboard(
        self, name: str, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> GraphRead | None:
        """Get graph by name and dashboard ID (IgraphService interface method)."""
        logger.info("Getting graph: name=%s, dashboard_id=%s", name, dashboard_id)

        if db is None:
            async with get_session() as db:
                return await self.get_graph_by_name_and_dashboard(
                    name, dashboard_id, db=db
                )

        repo = self._repository_cls(db)
        graph_obj = await repo.get_by_name_and_dashboard(name, dashboard_id)
        if graph_obj is None:
            logger.warning(
                "Graph not found: name=%s, dashboard_id=%s", name, dashboard_id
            )
            return None
        return await self._to_read_model(graph_obj)

    async def get_graphs_by_dashboard(
        self, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> list[GraphRead]:
        """Get graphs by dashboard ID (IgraphService interface method)."""
        return await self.list_by_dashboard(dashboard_id, db=db)

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
        """Update graph (IgraphService interface method)."""
        data = GraphUpdate(
            name=name,
            type=type_,
            config=config,
            dimensions=dimensions,
            metrics=metrics,
        )
        return await self.update(graph_id, data, db=db)

    async def delete_graph(
        self, graph_id: UUID, db: AsyncSession | None = None
    ) -> bool:
        """Delete graph (IgraphService interface method)."""
        return await self.delete(graph_id, db=db)
