from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional

from mko_bi.services.dashboard_service import list_dashboards
from mko_bi.services.user_service import create_user
from mko_bi.core.permissions import check_access, grant_access, revoke_access
from mko_bi.models.user import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    email: str
    role: str


class UserCreateRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "viewer"


class UserCreateResponse(BaseModel):
    id: int
    email: str
    role: str


@router.get("", response_model=List[UserResponse])
async def list_users() -> List[UserResponse]:
    """List all users (admin only).

    Returns:
        List of all users
    """
    # In a real implementation, this would check admin role
    # For now, returning empty list as user listing requires admin
    return []


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(request: UserCreateRequest) -> UserCreateResponse:
    """Create a new user (admin only).

    Args:
        request: User creation request

    Returns:
        Created user information

    Raises:
        HTTPException: 400 if user creation fails
    """
    try:
        user = create_user(request.email, request.password, request.role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return UserCreateResponse(id=user.id, email=user.email, role=user.role)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int) -> None:
    """Delete a user (admin only).

    Args:
        user_id: User ID to delete

    Raises:
        HTTPException: 403 if not authorized
    """
    # Admin check would happen here
    # For now, just raise if not implemented
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User deletion not yet implemented",
    )


@router.get("/{user_id}/dashboards", response_model=List[dict])
async def get_user_dashboards(user_id: int) -> List[dict]:
    """Get dashboards accessible to a user.

    Args:
        user_id: User ID to get dashboards for

    Returns:
        List of accessible dashboards
    """
    # This would use the dashboard service in a real implementation
    return []
