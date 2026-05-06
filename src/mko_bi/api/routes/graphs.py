"""Routes for managing dashboard graphs.

This module provides endpoints for CRUD operations on graphs.
Access to most operations is restricted and requires authentication.
Create, update, and delete operations are admin-only.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.api.deps import (
    get_db,
    require_admin_role,
    CurrentUser,
)
from mko_bi.models.graph import (
    GraphCreate,
    GraphRead,
    GraphUpdate,
)
from mko_bi.db.repositories.graph_repo import GraphRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graphs", tags=["graphs"])

# Initialize repository
_graph_repo = GraphRepository()


@router.post(
    "/",
    response_model=GraphRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new graph",
    description="Creates a new graph. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def create_graph_endpoint(
    graph: GraphCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> GraphRead:
    """Create a new graph.

    Args:
        graph: Model with data for creating the graph.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        GraphRead: Model of the created graph.

    Raises:
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Creating graph: name=%s, dashboard_id=%s, user_id=%s",
        graph.name,
        graph.dashboard_id,
        current_user.id,
    )

    try:
        result = await _graph_repo.create(
            db=db,
            name=graph.name,
            type=graph.type,
            dashboard_id=graph.dashboard_id,
            config=graph.config,
            dimensions=graph.dimensions,
            metrics=graph.metrics,
        )
        await db.commit()
        return GraphRead.model_validate(result)
    except ValueError as e:
        logger.warning("Validation error creating graph: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        await db.rollback()
        logger.error("Error creating graph name=%s: %s", graph.name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating graph",
        ) from e


@router.get(
    "/",
    response_model=list[GraphRead],
    status_code=status.HTTP_200_OK,
    summary="List all graphs",
    description="Returns a list of all graphs (global list).",
)
async def get_graphs_endpoint(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[GraphRead]:
    """Get all graphs.

    Args:
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        list[GraphRead]: List of graph models.

    Raises:
        HTTPException 500: On database error.
    """
    logger.info("Getting all graphs")

    try:
        graphs = await _graph_repo.get_all(db=db)
        return [GraphRead.model_validate(g) for g in graphs]
    except Exception as e:
        logger.error("Error getting graphs: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting graphs",
        ) from e


@router.get(
    "/{graph_id}",
    response_model=GraphRead,
    status_code=status.HTTP_200_OK,
    summary="Get graph by ID",
    description="Returns graph data by its ID.",
)
async def get_graph_endpoint(
    graph_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> GraphRead:
    """Get graph by ID.

    Args:
        graph_id: Graph ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        GraphRead: Graph model.

    Raises:
        HTTPException 404: If graph not found.
        HTTPException 500: On database error.
    """
    logger.info("Requesting graph: graph_id=%s", graph_id)

    try:
        graph = await _graph_repo.get(graph_id=graph_id, db=db)
        if graph is None:
            logger.warning("Graph not found: id=%s", graph_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found",
            )
        return GraphRead.model_validate(graph)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting graph id=%s: %s", graph_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting graph",
        ) from e


@router.put(
    "/{graph_id}",
    response_model=GraphRead,
    status_code=status.HTTP_200_OK,
    summary="Update graph",
    description="Updates graph data. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def update_graph_endpoint(
    graph_id: UUID,
    graph_update: GraphUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> GraphRead:
    """Update graph.

    Args:
        graph_id: Graph ID to update.
        graph_update: Model with new data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        GraphRead: Updated graph model.

    Raises:
        HTTPException 404: If graph not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Updating graph: graph_id=%s, user_id=%s",
        graph_id,
        current_user.id,
    )

    try:
        # Prepare update data
        update_data = {}
        if graph_update.name is not None:
            update_data["name"] = graph_update.name
        if graph_update.type is not None:
            update_data["type"] = graph_update.type
        if graph_update.config is not None:
            update_data["config"] = graph_update.config
        if graph_update.dimensions is not None:
            update_data["dimensions"] = graph_update.dimensions
        if graph_update.metrics is not None:
            update_data["metrics"] = graph_update.metrics

        result = await _graph_repo.update(
            graph_id=graph_id, db=db, **update_data
        )
        if result is None:
            logger.warning("Graph not found for update: id=%s", graph_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found",
            )
        await db.commit()
        return GraphRead.model_validate(result)
    except ValueError as e:
        logger.warning("Validation error updating graph: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error updating graph id=%s: %s", graph_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating graph",
        ) from e


@router.delete(
    "/{graph_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete graph",
    description="Deletes a graph. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_graph_endpoint(
    graph_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete graph.

    Args:
        graph_id: Graph ID to delete.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException 404: If graph not found.
        HTTPException 500: On database error.
    """
    logger.info(
        "Deleting graph: graph_id=%s, user_id=%s",
        graph_id,
        current_user.id,
    )

    try:
        result = await _graph_repo.delete(graph_id=graph_id, db=db)
        if not result:
            logger.warning("Graph not found for deletion: id=%s", graph_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found",
            )
        await db.commit()
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error deleting graph id=%s: %s", graph_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting graph",
        ) from e
