"""Dashboard access management routes.

This module provides endpoints for granting, revoking, and listing dashboard access.
All operations require admin role.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    get_db_dependency,
    require_admin_role,
    get_dashboard_service,
)
from mkobi.models.access import AccessGrant
from mkobi.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

# No prefix - this router is mounted under /dashboards
router = APIRouter(tags=["dashboards"])


@router.post(
    "/{dashboard_id}/access",
    status_code=status.HTTP_200_OK,
    summary="Grant dashboard access",
    description="Grants user access to dashboard. Available only to owners.",
    dependencies=[Depends(require_admin_role)],
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
        access_grant.permission,
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
            permission=access_grant.permission,
            db=db,
        )

        if result:
            logger.info(
                "Access granted: dashboard_id=%s, user_id=%s, permission=%s",
                dashboard_id,
                access_grant.user_id,
                access_grant.permission,
            )
            return {
                "message": "Access granted",
                "dashboard_id": str(dashboard_id),
                "user_id": str(access_grant.user_id),
                "permission": access_grant.permission,
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
    """Get all access records for a dashboard.

    Args:
        dashboard_id: Dashboard ID.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        list[dict]: List of access records.
    """
    logger.info("Getting access list for dashboard: dashboard_id=%s", dashboard_id)
    try:
        access_list = await dashboard_service.get_dashboard_access_list(
            dashboard_id=dashboard_id, db=db
        )
        return access_list
    except Exception as e:
        logger.error(
            "Error getting access list for dashboard dashboard_id=%s: %s",
            dashboard_id,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting dashboard access",
        ) from e


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
    """Revoke a user's access to a dashboard.

    Args:
        dashboard_id: Dashboard ID.
        user_id: User ID to revoke access from.
        current_user: Current authenticated user.
        db: Database session.
        dashboard_service: Injected dashboard service.

    Returns:
        dict: Success message.
    """
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
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error revoking access dashboard_id=%s, user_id=%s: %s",
            dashboard_id,
            user_id,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error revoking access",
        ) from e