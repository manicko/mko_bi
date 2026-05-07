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

from mkobi.api.deps import (
    CurrentUser,
    require_viewer_role,
    get_data_service,
)
from mkobi.services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


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
    dashboard_id: UUID = Query(..., description="Dashboard ID"),
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

    try:
        # Parse filters from JSON string
        filters_dict: dict[str, Any] = {}
        if filters:
            try:
                filters_dict = json.loads(filters)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid JSON in filters: {e}",
                ) from e

        # Get data through service with applied filters
        result: dict[str, Any] = await data_service.get_filtered_data(
            dashboard_id=dashboard_id,
            filters=filters_dict,
        )

        logger.info(
            "Aggregated data retrieved: dashboard_id=%s, charts_count=%d",
            dashboard_id,
            len(result.get("graphs", [])),
        )
        return result

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
