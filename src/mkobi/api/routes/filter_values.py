"""Dashboard filter values routes.

This module provides endpoints for retrieving filter values for dashboards.
Read operations use dashboard access control (require_dashboard_read_access).
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_db_dependency,
    require_dashboard_read_access,
    get_filter_values_service,
)
from mkobi.models.user import UserRead
from mkobi.services.filter_values_service import FilterValuesService

logger = logging.getLogger(__name__)

# No prefix - this router is mounted under /dashboards
router = APIRouter(tags=["dashboards"])


@router.get(
    "/{dashboard_id}/filter-values",
    status_code=status.HTTP_200_OK,
    summary="Get filter values for a dashboard",
    description="Returns distinct filter values for a specified filter/dimension name.",
)
async def get_filter_values_endpoint(
    dashboard_id: UUID,
    filter_name: str = Query(..., description="Filter/dimension name"),
    current_user: UserRead = Depends(require_dashboard_read_access),
    db: AsyncSession = Depends(get_db_dependency),
    filter_values_service: FilterValuesService = Depends(get_filter_values_service),
) -> dict[str, Any]:
    """Get filter values for a dashboard.

    Args:
        dashboard_id: Dashboard identifier.
        filter_name: Name of the filter to get values for.
        current_user: Current authenticated user with read access.
        db: Database session.
        filter_values_service: Injected filter values service.

    Returns:
        dict with filter_name and values list.

    Raises:
        HTTPException 500: On database error.
    """
    logger.info(
        "Getting filter values for dashboard: dashboard_id=%s, filter_name=%s",
        dashboard_id,
        filter_name,
    )
    try:
        values = await filter_values_service.get_filter_values(
            dashboard_id=dashboard_id, filter_name=filter_name, db=db
        )
        return {"filter_name": filter_name, "values": values}
    except Exception:
        logger.error(
            "Error getting filter values: dashboard_id=%s, filter_name=%s",
            dashboard_id,
            filter_name,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting filter values",
        ) from None