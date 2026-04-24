from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional

from mko_bi.services.user_service import create_user
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.models.user import UserDB
from mko_bi.api.deps import get_admin_user

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
async def list_users(
    admin_user: UserDB = Depends(get_admin_user),
) -> List[UserResponse]:
    """List all users (admin only).

    Returns:
        List of all users
    """
    users = UserRepository.get_all()
    return [
        UserResponse(id=user.id, email=user.email, role=user.role) for user in users
    ]


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    request: UserCreateRequest, admin_user: UserDB = Depends(get_admin_user)
) -> UserCreateResponse:
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
async def delete_user(
    user_id: int, admin_user: UserDB = Depends(get_admin_user)
) -> None:
    """Delete a user (admin only).

    Args:
        user_id: User ID to delete

    Raises:
        HTTPException: 403 if not authorized or trying to delete self
        HTTPException: 404 if user not found
    """
    # Prevent self-deletion
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete yourself",
        )

    # Check if user exists
    user_to_delete = UserRepository.get(user_id)
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Delete user
    UserRepository.delete(user_id)
