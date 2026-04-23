from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from mko_bi.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    delete_dashboard,
    list_dashboards,
)
from mko_bi.core.permissions import check_access

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


class DashboardResponse(BaseModel):
    id: int
    name: str
    config: Dict[str, Any]


class DashboardCreateRequest(BaseModel):
    name: str
    config: Dict[str, Any]


class DashboardCreateResponse(BaseModel):
    id: int
    name: str


@router.get("", response_model=List[DashboardResponse])
async def list_dashboards_endpoint(user_id: int = 1) -> List[DashboardResponse]:
    """List all dashboards accessible to the current user.

    Args:
        user_id: Current user ID (from JWT)

    Returns:
        List of accessible dashboards
    """
    dashboards = list_dashboards(user_id)
    return [
        DashboardResponse(id=d.id, name=d.name, config=d.config) for d in dashboards
    ]


@router.post(
    "", response_model=DashboardCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_dashboard_endpoint(
    request: DashboardCreateRequest,
    user_id: int = 1,
) -> DashboardCreateResponse:
    """Create a new dashboard.

    Args:
        request: Dashboard creation request
        user_id: Current user ID

    Returns:
        Created dashboard information

    Raises:
        HTTPException: 400 if dashboard creation fails
    """
    try:
        dashboard = create_dashboard(
            name=request.name,
            config=request.config,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DashboardCreateResponse(id=dashboard.id, name=dashboard.name)


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard_endpoint(
    dashboard_id: int,
    user_id: int = 1,
) -> DashboardResponse:
    """Get a specific dashboard.

    Args:
        dashboard_id: Dashboard ID to retrieve
        user_id: Current user ID

    Returns:
        Dashboard information

    Raises:
        HTTPException: 404 if dashboard not found or no access
    """
    dashboard = get_dashboard(dashboard_id, user_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found or access denied",
        )

    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        config=dashboard.config,
    )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard_endpoint(
    dashboard_id: int,
    user_id: int = 1,
) -> None:
    """Delete a dashboard (admin only).

    Args:
        dashboard_id: Dashboard ID to delete
        user_id: Current user ID

    Raises:
        HTTPException: 403 if not authorized
    """
    try:
        delete_dashboard(dashboard_id, user_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this dashboard",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )
