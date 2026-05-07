"""Admin routes for user management and registration requests."""

import logging
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    get_db_dependency,
    get_user_service,
    require_admin_role,
)
from mkobi.db.repositories.registration_request_repo import (
    RegistrationRequestRepository,
)
from mkobi.models.enums import RegistrationStatus, UserRole
from mkobi.models.user import UserRead
from mkobi.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# --- User Management ---


@router.get(
    "/users",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List all users (admin)",
    description="Returns list of all users. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def get_users_admin_endpoint(
    user_service=Depends(get_user_service),
) -> list[UserRead]:
    """Get all users (admin endpoint)."""
    logger.info("Admin: getting all users")
    try:
        users_data = await user_service.get_all_users()
        return [UserRead(**user) for user in users_data]
    except Exception as e:
        logger.error("Error getting users: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting users",
        ) from e


@router.patch(
    "/users/{user_id}/role",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update user role (admin)",
    description="Updates user role. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def update_user_role_admin_endpoint(
    user_id: UUID,
    new_role: UserRole,
    user_service=Depends(get_user_service),
) -> UserRead:
    """Update user role (admin endpoint)."""
    logger.info("Admin: updating user role: id=%s, new_role=%s", user_id, new_role)
    try:
        updated = await user_service.update_user_role(user_id=user_id, role=new_role)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error updating user role: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user role",
        ) from e


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (admin)",
    description="Deletes a user. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_user_admin_endpoint(
    user_id: UUID,
    user_service=Depends(get_user_service),
) -> None:
    """Delete user (admin endpoint)."""
    logger.info("Admin: deleting user: id=%s", user_id)
    try:
        result = await user_service.delete_user(user_id=user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error deleting user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user",
        ) from e


# --- Registration Requests ---


@router.get(
    "/registration-requests",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List registration requests (admin)",
    description="Returns list of all registration requests. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def get_registration_requests_admin_endpoint(
    db: AsyncSession = Depends(get_db_dependency),
) -> list[dict[str, Any]]:
    """Get all registration requests (admin endpoint)."""
    logger.info("Admin: getting registration requests")
    try:
        repo = RegistrationRequestRepository(db)
        requests = await repo.get_all()
        return cast(list[dict[str, Any]], requests)
    except Exception as e:
        logger.error("Error getting registration requests: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting registration requests",
        ) from e


@router.post(
    "/registration-requests/{request_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve registration request (admin)",
    description="Approves a registration request and creates user. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def approve_registration_request_admin_endpoint(
    request_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Approve registration request (admin endpoint)."""
    logger.info("Admin: approving registration request: id=%s", request_id)
    try:
        # Get the request
        repo = RegistrationRequestRepository(db)
        req = await repo.get_by_id(request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration request not found",
            )

        if req["status"] != RegistrationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request already {req['status']}",
            )

        # Create user
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email=req["email"],
            password="temppass123",  # TODO: generate random password and send email
            role=UserRole.VIEWER,
        )

        # Update request status
        await repo.update_status(
            request_id=request_id,
            status=RegistrationStatus.APPROVED,
            reviewed_by=current_user.id,
        )
        await db.commit()

        return {"message": "Registration request approved", "user_id": str(user.id)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error approving registration request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error approving registration request",
        ) from e


@router.post(
    "/registration-requests/{request_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject registration request (admin)",
    description="Rejects a registration request. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def reject_registration_request_admin_endpoint(
    request_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Reject registration request (admin endpoint)."""
    logger.info("Admin: rejecting registration request: id=%s", request_id)
    try:
        repo = RegistrationRequestRepository(db)
        req = await repo.get_by_id(request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration request not found",
            )

        if req["status"] != RegistrationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request already {req['status']}",
            )

        # Update request status
        await repo.update_status(
            request_id=request_id,
            status=RegistrationStatus.REJECTED,
            reviewed_by=current_user.id,
        )
        await db.commit()

        return {"message": "Registration request rejected"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error rejecting registration request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rejecting registration request",
        ) from e
