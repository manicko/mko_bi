"""Dashboard management routes.

This module provides endpoints for CRUD operations with dashboards.

Access to most operations is restricted and requires authentication.
Create, update and delete operations are available only to owners.
"""

import logging
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    get_db_dependency,
    require_admin_role,
    require_viewer_role,
    get_dashboard_service,
)
from mkobi.db.repositories.dashboard_filter_repo import DashboardFilterRepository
from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.db.repositories.graph_repo import GraphRepository
from mkobi.models.access import AccessGrant
from mkobi.models.dashboard import (
    DashboardCreate,
    DashboardRead,
    DashboardUpdate,
)
from mkobi.models.graph import GraphCreate, GraphRead
from mkobi.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

# Initialize repository
_graph_repo = GraphRepository()


router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post(
    "/",
    response_model=DashboardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create dashboard",
    description="Creates new dashboard. Available only to admins.",
    dependencies=[Depends(require_admin_role)],
)
async def create_dashboard_endpoint(
    dashboard_data: DashboardCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardRead:
    """Create new dashboard.

    Current authenticated user automatically becomes
    the owner (admin) of the created dashboard.

    Args:
        dashboard: Dashboard creation data model.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        DashboardRead: Model of the created dashboard.

    Raises:
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    dashboard = DashboardCreate(
        name=dashboard_data.name,
        description=dashboard_data.description,
        config=dashboard_data.config,
    )

    logger.info(
        "Creating dashboard: name=%s, owner_id=%s",
        dashboard.name,
        current_user.id,
    )

    try:
        result = await dashboard_service.create_dashboard(
            name=dashboard.name,
            config=dashboard.config.model_dump(),
            owner_id=current_user.id,
            db=db,
        )

        logger.info(
            "Dashboard created successfully: id=%s, name=%s",
            result.id,
            result.name,
        )
        return result
    except ValueError as e:
        logger.warning("Validation error creating dashboard: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Error creating dashboard name=%s: %s",
            dashboard.name,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard creation error: {str(e)}",
        ) from e


@router.get(
    "/my",
    response_model=list[DashboardRead],
    status_code=status.HTTP_200_OK,
    summary="Get user dashboards",
    description="Returns list of dashboards available to current user.",
)
async def get_my_dashboards_endpoint(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> list[DashboardRead]:
    """Get user dashboards.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        list[DashboardRead]: List of dashboards available to user.

    Raises:
        HTTPException 500: On database error.
    """
    logger.info("Getting user dashboards: user_id=%s", current_user.id)

    try:
        dashboards = await dashboard_service.get_user_dashboards(
            user_id=current_user.id, db=db
        )
        logger.info(
            "Retrieved dashboards for user: user_id=%s, count=%s",
            current_user.id,
            len(dashboards),
        )
        return dashboards
    except Exception as e:
        logger.error(
            "Error getting user dashboards user_id=%s: %s",
            current_user.id,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user dashboards: {str(e)}",
        ) from e


@router.get(
    "/{dashboard_id}",
    response_model=DashboardRead,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard by ID",
    description="Returns dashboard data by its ID with access check.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_dashboard_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardRead:
    """Get dashboard by ID with access check.

    Args:
        dashboard_id: Dashboard ID.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        DashboardRead: Dashboard model.

    Raises:
        HTTPException 403: If user has no access.
        HTTPException 404: If dashboard not found.
        HTTPException 500: On database error.
    """
    logger.info(
        "Dashboard request: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        dashboard = await dashboard_service.get_dashboard(
            dashboard_id, user_id=current_user.id, db=db
        )
        if dashboard is None:
            logger.warning(
                "Dashboard not found: dashboard_id=%s",
                dashboard_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )

        logger.info(
            "Dashboard retrieved: id=%s, name=%s",
            dashboard.id,
            dashboard.name,
        )
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting dashboard dashboard_id=%s: %s",
            dashboard_id,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting dashboard",
        ) from e


@router.put(
    "/{dashboard_id}",
    response_model=DashboardRead,
    status_code=status.HTTP_200_OK,
    summary="Update dashboard",
    description="Updates dashboard configuration. Available only to admins.",
    dependencies=[Depends(require_admin_role)],
)
async def update_dashboard_endpoint(
    dashboard_id: UUID,
    dashboard_update: DashboardUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardRead:
    """Update dashboard.

    Available only to dashboard owner (user with admin permission).

    Args:
        dashboard_id: Dashboard ID to update.
        dashboard_update: Model with new data.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        DashboardRead: Updated dashboard model.

    Raises:
        HTTPException 403: If user has no update rights.
        HTTPException 404: If dashboard not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Updating dashboard: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        updated = await dashboard_service.update_dashboard(
            dashboard_id=dashboard_id,
            update_data=dashboard_update.model_dump(exclude_unset=True),
            db=db,
        )
        if updated is None:
            logger.warning("Dashboard not found for update: id=%s", dashboard_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )
        return updated
    except ValueError as e:
        logger.warning("Validation error updating dashboard: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating dashboard id=%s: %s", dashboard_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard update error",
        ) from e


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dashboard",
    description="Deletes dashboard. Available only to admins.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_dashboard_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> None:
    """Delete dashboard.

    Available only to dashboard owner (user with admin permission).

    Args:
        dashboard_id: Dashboard ID to delete.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Raises:
        HTTPException 403: If user has no deletion rights.
        HTTPException 404: If dashboard not found.
        HTTPException 500: On database error.
    """
    logger.info(
        "Deleting dashboard: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        result = await dashboard_service.delete_dashboard(
            dashboard_id=dashboard_id, db=db
        )
        if not result:
            logger.warning("Dashboard not found for deletion: id=%s", dashboard_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting dashboard id=%s: %s", dashboard_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard deletion error",
        ) from e


@router.post(
    "/{dashboard_id}/access",
    status_code=status.HTTP_200_OK,
    summary="Grant dashboard access",
    description="Grants user access to dashboard. Available only to owners.",
    dependencies=[Depends(require_viewer_role)],
)
async def grant_dashboard_access_endpoint(
    dashboard_id: UUID,
    access_grant: AccessGrant,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, Any]:
    """Grant user access to dashboard.

    Available only to dashboard owner (user with admin permission).

    Args:
        dashboard_id: Dashboard ID.
        access_grant: Model with access grant data.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        dict: Success message.

    Raises:
        HTTPException 403: If user has no access management rights.
        HTTPException 404: If dashboard not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Granting access: dashboard_id=%s, user_id=%s, permission=%s",
        dashboard_id,
        access_grant.user_id,
        access_grant.permission_level,
    )

    try:
        # Check that dashboard_id from path matches body
        if str(access_grant.dashboard_id) != str(dashboard_id):
            logger.warning(
                "Mismatch dashboard_id: path=%s, body=%s",
                dashboard_id,
                access_grant.dashboard_id,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="dashboard_id in body doesn't match URL",
            )

        result = await dashboard_service.grant_access(
            dashboard_id=dashboard_id,
            user_id=access_grant.user_id,
            permission=access_grant.permission_level,
            db=db,
        )

        if result:
            logger.info(
                "Access granted: dashboard_id=%s, user_id=%s, permission=%s",
                dashboard_id,
                access_grant.user_id,
                access_grant.permission_level,
            )
            return {
                "message": "Access granted",
                "dashboard_id": str(dashboard_id),
                "user_id": str(access_grant.user_id),
                "permission": access_grant.permission_level,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )
    except ValueError as e:
        logger.warning("Validation error granting access: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error granting access to dashboard id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Access grant error",
        ) from e


# --- Dashboard-Filter binding endpoints ---


@router.post(
    "/{dashboard_id}/filters",
    status_code=status.HTTP_200_OK,
    summary="Bind filter to dashboard",
    description="Binds a filter to a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def bind_filter_endpoint(
    dashboard_id: UUID,
    filter_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Bind a filter to a dashboard."""
    logger.info(
        "Binding filter to dashboard: dashboard_id=%s, filter_id=%s",
        dashboard_id,
        filter_id,
    )
    try:
        filter_repo = FilterRepository()
        filter_obj = await filter_repo.get(filter_id, db)
        if not filter_obj:
            raise HTTPException(status_code=404, detail="Filter not found")

        dashboard_filter_repo = DashboardFilterRepository()
        result = await dashboard_filter_repo.bind_filter(
            dashboard_id=dashboard_id, filter_id=filter_id, db=db
        )
        await db.commit()
        return {"message": "Filter bound to dashboard", "bound": result}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/{dashboard_id}/filters/{filter_id}",
    status_code=status.HTTP_200_OK,
    summary="Unbind filter from dashboard",
    description="Unbinds a filter from a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def unbind_filter_endpoint(
    dashboard_id: UUID,
    filter_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Unbind a filter from a dashboard."""
    logger.info(
        "Unbinding filter from dashboard: dashboard_id=%s, filter_id=%s",
        dashboard_id,
        filter_id,
    )
    try:
        dashboard_filter_repo = DashboardFilterRepository()
        result = await dashboard_filter_repo.unbind_filter(
            dashboard_id=dashboard_id, filter_id=filter_id, db=db
        )
        await db.commit()
        if result:
            return {"message": "Filter unbound from dashboard"}
        else:
            raise HTTPException(
                status_code=404, detail="Filter not bound to this dashboard"
            )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/{dashboard_id}/filters",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List dashboard filters",
    description="Returns all filters bound to a dashboard.",
)
async def get_dashboard_filters_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[dict[str, Any]]:
    """Get all filters bound to a dashboard."""
    logger.info("Getting filters for dashboard: dashboard_id=%s", dashboard_id)
    try:
        dashboard_filter_repo = DashboardFilterRepository()
        filter_ids = await dashboard_filter_repo.get_dashboard_filters(
            dashboard_id=dashboard_id, db=db
        )
        return [{"filter_id": str(fid)} for fid in filter_ids]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Dashboard Access management endpoints ---


@router.get(
    "/{dashboard_id}/access",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List dashboard access",
    description="Returns all access records for a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def get_dashboard_access_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> list[dict[str, Any]]:
    """Get all access records for a dashboard."""
    logger.info("Getting access list for dashboard: dashboard_id=%s", dashboard_id)
    try:
        access_list = await dashboard_service.get_dashboard_access_list(
            dashboard_id=dashboard_id, db=db
        )
        return access_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/{dashboard_id}/access/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke dashboard access",
    description="Revokes user's access to a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def revoke_dashboard_access_endpoint(
    dashboard_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, Any]:
    """Revoke a user's access to a dashboard."""
    logger.info("Revoking access: dashboard_id=%s, user_id=%s", dashboard_id, user_id)
    try:
        result = await dashboard_service.revoke_access(
            dashboard_id=dashboard_id, user_id=user_id, db=db
        )
        await db.commit()
        if result:
            return {"message": "Access revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="Access record not found")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Dashboard graph endpoints ---


@router.post(
    "/{dashboard_id}/graphs",
    response_model=GraphRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new graph for a dashboard",
    description="Creates a new graph for a specific dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def create_dashboard_graph_endpoint(
    dashboard_id: UUID,
    graph: GraphCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> GraphRead:
    """Create a new graph for a dashboard.

    Args:
        dashboard_id: Dashboard ID.
        graph: Model with graph data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        GraphRead: Model of the created graph.

    Raises:
        HTTPException 404: If dashboard not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Creating graph for dashboard: name=%s, dashboard_id=%s, user_id=%s",
        graph.name,
        dashboard_id,
        current_user.id,
    )

    try:
        result = await _graph_repo.create(
            db=db,
            name=graph.name,
            type=graph.type,
            dashboard_id=dashboard_id,
            config=graph.config,
            dimensions=graph.dimensions,
            metrics=graph.metrics,
        )
        await db.commit()
        return cast(GraphRead, GraphRead.model_validate(result))
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
    "/{dashboard_id}/graphs",
    response_model=list[GraphRead],
    status_code=status.HTTP_200_OK,
    summary="List graphs for a dashboard",
    description="Returns a list of all graphs for a specific dashboard.",
)
async def get_dashboard_graphs_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[GraphRead]:
    """Get all graphs for a dashboard.

    Args:
        dashboard_id: Dashboard ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        list[GraphRead]: List of graph models.

    Raises:
        HTTPException 500: On database error.
    """
    logger.info("Getting graphs for dashboard: dashboard_id=%s", dashboard_id)

    try:
        graphs = await _graph_repo.get_by_dashboard_id(
            dashboard_id=dashboard_id, db=db
        )
        return [GraphRead.model_validate(g) for g in graphs]
    except Exception as e:
        logger.error("Error getting graphs for dashboard %s: %s", dashboard_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting graphs",
        ) from e
