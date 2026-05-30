"""Dashboard CRUD routes.

This module provides endpoints for create, read, update, delete operations on dashboards.
Access to most operations is restricted and requires authentication.
Create, update and delete operations are available only to owners.
"""

import logging
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
from mkobi.models.dashboard import (
    DashboardAdmin,
    DashboardRead,
    DashboardCreate,
    DashboardUpdate,
)
from mkobi.services.dashboard_service import DashboardService
from mkobi.utils.exceptions import PermissionDeniedException

logger = logging.getLogger(__name__)

# No prefix - this router is mounted under /dashboards
router = APIRouter(tags=["dashboards"])


@router.get(
    "/",
    response_model=list[DashboardAdmin],
    status_code=status.HTTP_200_OK,
    summary="List all dashboards (admin)",
    description="Returns list of all dashboards. Available only to admins.",
    dependencies=[Depends(require_admin_role)],
)
async def get_dashboards_admin_endpoint(
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> list[DashboardAdmin]:
    """Get all dashboards for admin panel.

    Args:
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        list[DashboardAdmin]: List of dashboards without full config.
    """
    logger.info("Admin: getting all dashboards")
    try:
        dashboards = await dashboard_service.get_all_dashboards(db=db)
        return [
            DashboardAdmin(
                id=d.id,
                name=d.name,
                description=d.description,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in dashboards
        ]
    except Exception as e:
        logger.error("Error getting all dashboards: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting dashboards",
        ) from e


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
    logger.info(
        "Creating dashboard: name=%s, owner_id=%s",
        dashboard_data.name,
        current_user.id,
    )

    try:
        result = await dashboard_service.create_dashboard(
            name=dashboard_data.name,
            config=dashboard_data.config.model_dump(),
            owner_id=current_user.id,
            description=dashboard_data.description,
            layout_id=dashboard_data.layout_id,
            db=db,
        )
        await db.commit()

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
            "Error creating dashboard name=%s",
            dashboard_data.name,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating dashboard",
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
            user_id=current_user.id, user_role=current_user.role, db=db
        )
        logger.info(
            "Retrieved dashboards for user: user_id=%s, count=%s",
            current_user.id,
            len(dashboards),
        )
        return dashboards
    except Exception as e:
        logger.error(
            "Error getting user dashboards user_id=%s",
            current_user.id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting user dashboards",
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
            dashboard_id, user_id=current_user.id, user_role=current_user.role, db=db
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
    except PermissionDeniedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None
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