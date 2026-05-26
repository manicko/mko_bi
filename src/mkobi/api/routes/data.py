"""Routes for getting dashboard aggregated data.

This module provides endpoints for:
- Getting aggregated data for dashboards
- Getting data for specific charts
- Applying filters to data

All operations require authentication and appropriate permissions.
"""

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    require_viewer_role,
    get_data_service,
    get_db_dependency,
)
from mkobi.core.permissions import check_dashboard_access
from mkobi.models.data import ProcessingResultData
from mkobi.services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"], redirect_slashes=False)


@router.get(
    "/aggregated",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get dashboard aggregated data",
    description="Returns data for all dashboard charts with applied filters.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_aggregated_data_endpoint(
    current_user: CurrentUser,
    data_service: DataService = Depends(get_data_service),
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_id: UUID = Query(..., description="Dashboard ID"),
    graph_id: UUID = Query(..., description="Graph ID"),
    filters: str | None = Query(default=None, description="JSON string with filters"),
) -> dict[str, Any]:
    """Get aggregated data for dashboard.

    Applies filters to JSONB field dims and groups data by graph_id.
    Response format: {"graphs": [{"graph_id": "...", "data": [...]}]}

    Args:
        dashboard_id: Dashboard ID.
        filters: JSON string with filters (optional).
        current_user: Current authenticated user.
        data_service: Data service (dependency injection).

    Returns:
        dict: Data for charts in React (Plotly.js) format.

    Raises:
        HTTPException 403: If user has no read access to dashboard.
        HTTPException 404: If dashboard not found.
        HTTPException 500: On server error.
    """
    logger.info(
        "Aggregated data request: dashboard_id=%s, user_id=%s, filters=%s",
        dashboard_id,
        current_user.id,
        filters,
    )

    # Check that user has access to the dashboard
    if not await check_dashboard_access(
        user_id=current_user.id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    ):
        logger.warning(
            "Access denied to dashboard: dashboard_id=%s, user_id=%s",
            dashboard_id,
            current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this dashboard",
        )

    try:
        # Parse filters from JSON string
        parsed_filters: dict[str, Any] | None = None
        if filters:
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid JSON in filters: {e}",
                ) from e

        # Get data through service
        result: list[ProcessingResultData] = await data_service.get_aggregated_data(
            dashboard_id=dashboard_id,
            graph_id=graph_id,
            db=db,
            filters=parsed_filters,
        )

        logger.info(
            "Aggregated data retrieved: dashboard_id=%s, graph_id=%s, records_count=%d",
            dashboard_id,
            graph_id,
            len(result),
        )
        return {"graphs": [{"graph_id": str(graph_id), "data": result}]}

    except ValueError as e:
        logger.warning("Error getting data: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Access denied: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Error getting aggregated data for dashboard id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting data",
        ) from e