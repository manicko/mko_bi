"""Access control and permission checking module.

Provides functions and dependencies for checking user access rights
to dashboards and operations in the BI Dashboard system.

Role hierarchy:
    admin > editor > viewer

Where admin has all rights, editor can read and write,
viewer can only read.
"""

import logging
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.core.security import decode_token
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.db.session import get_session
from mkobi.models.enums import DashboardPermission, UserRole
from mkobi.models.user import UserDB


class RolePermissions:
    """Class for checking access rights based on roles.

    Determines which roles have access to certain operations.
    """

    CAN_CREATE_DASHBOARDS: list[UserRole] = [UserRole.ADMIN]
    CAN_EDIT_DASHBOARDS: list[UserRole] = [UserRole.ADMIN, UserRole.EDITOR]
    CAN_VIEW_DASHBOARDS: list[UserRole] = [
        UserRole.ADMIN,
        UserRole.EDITOR,
        UserRole.VIEWER,
    ]
    CAN_MANAGE_USERS: list[UserRole] = [UserRole.ADMIN]
    CAN_UPLOAD_DATA: list[UserRole] = [UserRole.ADMIN, UserRole.EDITOR]

    @classmethod
    def can_create_dashboards(cls, user_role: UserRole) -> bool:
        """Check if user can create dashboards."""
        return user_role in cls.CAN_CREATE_DASHBOARDS

    @classmethod
    def can_edit_dashboards(cls, user_role: UserRole) -> bool:
        """Check if user can edit dashboards."""
        return user_role in cls.CAN_EDIT_DASHBOARDS

    @classmethod
    def can_view_dashboards(cls, user_role: UserRole) -> bool:
        """Check if user can view dashboards."""
        return user_role in cls.CAN_VIEW_DASHBOARDS

    @classmethod
    def can_manage_users(cls, user_role: UserRole) -> bool:
        """Check if user can manage users."""
        return user_role in cls.CAN_MANAGE_USERS

    @classmethod
    def can_upload_data(cls, user_role: UserRole) -> bool:
        """Check if user can upload data."""
        return user_role in cls.CAN_UPLOAD_DATA


def check_permission(user_role: UserRole, required: list[UserRole]) -> bool:
    """Check if user has required permissions.

    Args:
        user_role: User's role.
        required: List of roles that have access.

    Returns:
        bool: True if user has access, False otherwise.
    """
    result = user_role in required
    logger.debug(
        "Permission check: user_role=%s, required=%s -> %s",
        user_role,
        [r.value for r in required],
        result,
    )
    return result


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database session.

    Creates a new async session for each request and closes it after completion.

    Yields:
        AsyncSession: Async SQLAlchemy session.
    """
    async with get_session() as db:
        try:
            yield db
        finally:
            # Explicit close for guarantee
            await db.close()


logger = logging.getLogger(__name__)


# --- Constants ---


# Role hierarchy (from junior to senior)
ROLE_HIERARCHY: list[UserRole] = [UserRole.VIEWER, UserRole.EDITOR, UserRole.ADMIN]

# Access levels - use DashboardPermission
PERMISSION_LEVELS: dict[DashboardPermission, int] = {
    DashboardPermission.VIEW: 1,
    DashboardPermission.EDIT: 2,
    DashboardPermission.ADMIN: 3,
}
# For backward compatibility also accept "read" as "view" and "write" as "edit"


# --- Exceptions ---


class PermissionError(Exception):
    """Exception raised when access rights are insufficient."""

    pass


class AuthenticationError(Exception):
    """Exception raised on authentication error."""

    pass


# --- Helper functions ---


def _get_role_level(role: UserRole) -> int:
    """Get role index in hierarchy.

    Args:
        role: User role (UserRole).

    Returns:
        int: Role index in hierarchy (higher = more rights).

    Raises:
        ValueError: If role is unknown.
    """
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError as err:
        logger.error("Unknown role: %s", role)
        raise ValueError(f"Unknown role: '{role}'") from err


# --- Main permission check functions ---


def check_role(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if user role is sufficient for the operation.

    Compares user role level with required level.
    Uses hierarchy: admin > editor > viewer.

    Args:
        user_role: User's role (UserRole).
        required_role: Minimum required role (UserRole).

    Returns:
        bool: True if user role is sufficient, False otherwise.

    Example:
        >>> check_role(UserRole.ADMIN, UserRole.VIEWER)
        True
        >>> check_role(UserRole.EDITOR, UserRole.ADMIN)
        False
        >>> check_role(UserRole.VIEWER, UserRole.VIEWER)
        True
    """
    try:
        user_level = _get_role_level(user_role)
        required_level = _get_role_level(required_role)
        has_access = user_level >= required_level
        logger.debug(
            "Role check: user_role=%s (level %d), required_role=%s (level %d) -> %s",
            user_role,
            user_level,
            required_role,
            required_level,
            has_access,
        )
        return has_access
    except ValueError as e:
        logger.error("Error checking role: %s", e)
        return False


async def check_dashboard_access(
    user_id: UUID,
    dashboard_id: UUID,
    required_permission: str = "view",
    db: AsyncSession | None = None,
) -> bool:
    """Check if user has access to dashboard.

    Args:
        user_id: User identifier.
        dashboard_id: Dashboard identifier.
        required_permission: Required access level (view/edit/admin).
        db: Async database session. If not provided, a new one is created.

    Returns:
        True if access exists, False otherwise.
    """
    logger.info(
        "Checking access: user_id=%s, dashboard_id=%s, required=%s",
        user_id,
        dashboard_id,
        required_permission,
    )

    # Validate required permission
    if required_permission not in [e.value for e in DashboardPermission]:
        raise ValueError(f"Allowed values: {[e.value for e in DashboardPermission]}")

    # If session is not provided, create a new one via context manager
    if db is None:
        async with get_session() as session:
            return await _check_access_with_session(
                user_id, dashboard_id, required_permission, session
            )
    else:
        return await _check_access_with_session(
            user_id, dashboard_id, required_permission, db
        )


async def _check_access_with_session(
    user_id: UUID,
    dashboard_id: UUID,
    required_permission: str,
    db: AsyncSession,
) -> bool:
    """Internal function to check access using session.

    Args:
        user_id: User identifier.
        dashboard_id: Dashboard identifier.
        required_permission: Required access level.
        db: Async database session.

    Returns:
        True if access exists, False otherwise.
    """
    try:
        # Get user access level
        permission = await AccessRepository.check_access(
            user_id=user_id,
            dashboard_id=dashboard_id,
            db=db,
        )

        if permission is None:
            logger.warning(
                "Access not found: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return False

        # Permission hierarchy: admin > edit > view
        # Normalize names for compatibility (read->view, write->edit)
        perm_map = {
            DashboardPermission.VIEW.value: DashboardPermission.VIEW.value,
            DashboardPermission.EDIT.value: DashboardPermission.EDIT.value,
            DashboardPermission.ADMIN.value: DashboardPermission.ADMIN.value,
            "read": DashboardPermission.VIEW.value,
            "write": DashboardPermission.EDIT.value,
        }
        permission_normalized = perm_map.get(permission, permission)
        required_normalized = perm_map.get(required_permission, required_permission)

        permission_levels = {
            DashboardPermission.VIEW.value: 1,
            DashboardPermission.EDIT.value: 2,
            DashboardPermission.ADMIN.value: 3,
        }
        has_access = (
            permission_levels[permission_normalized]
            >= permission_levels[required_normalized]
        )

        logger.info(
            "Access check: user_id=%s, dashboard_id=%s, "
            "permission=%s, required=%s -> %s",
            user_id,
            dashboard_id,
            permission,
            required_permission,
            has_access,
        )

        return has_access

    except Exception as e:
        logger.error(
            "Error checking access user_id=%s, dashboard_id=%s: %s",
            user_id,
            dashboard_id,
            e,
        )
        return False


@lru_cache(maxsize=128)
def _decode_token_cached(token: str) -> dict[str, Any] | None:
    """Cached token decoding.

    Args:
        token: JWT token.

    Returns:
        dict[str, Any] | None: Decoded token data or None.
    """
    result = decode_token(token)
    if result is None:
        return None
    return result


async def get_current_user(
    token: str,
    db: AsyncSession | None = None,
) -> UserDB:
    """Get current user by token.

    Decodes JWT token, extracts user_id and gets
    user data from database.

    Args:
        token: JWT access token.
        db: Async database session. If not provided, a new one is created.

    Returns:
        UserDB: User model with data from database.

    Raises:
        AuthenticationError: If token is invalid or user not found.
    """
    # If session is not provided, create a new one via context manager
    if db is None:
        async with get_session() as session:
            return await _get_current_user_with_session(token, session)
    else:
        return await _get_current_user_with_session(token, db)


async def _get_current_user_with_session(
    token: str,
    db: AsyncSession,
) -> UserDB:
    """Internal function to get user using session.

    Args:
        token: JWT access token.
        db: Async database session.

    Returns:
        UserDB: User model.

    Raises:
        AuthenticationError: If token is invalid or user not found.
    """
    try:
        # Decode token (with caching)
        payload = _decode_token_cached(token)
        if payload is None:
            logger.warning("Invalid token")
            raise AuthenticationError("Invalid token")

        user_id_raw = payload.get("user_id")
        if user_id_raw is None:
            logger.warning("Token missing user_id")
            raise AuthenticationError("Invalid token")

        user_id: UUID = UUID(str(user_id_raw))

        # Get user from database
        repo = UserRepository()
        user = await repo.get(id=user_id, db=db)
        if user is None:
            logger.warning("User not found: user_id=%s", user_id)
            raise AuthenticationError("User not found")

        logger.info("User authenticated: user_id=%s", user_id)
        return UserDB.model_validate(user)

    except JWTError as e:
        logger.error("JWT decode error: %s", e)
        raise AuthenticationError("Token decode error") from e
    except Exception as e:
        if not isinstance(e, AuthenticationError):
            logger.error("Error getting user: %s", e)
        raise


# --- FastAPI dependencies ---


security = HTTPBearer()


async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserDB:
    """FastAPI dependency for getting current user.

    Extracts token from Authorization header, decodes it
    and returns user data.

    Args:
        credentials: Credentials from Authorization header.
        db: Database session.

    Returns:
        UserDB: Authenticated user model.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    try:
        user = await get_current_user(credentials.credentials, db)
        # Save user in request state for later use
        # (will be available via request.state.user)
        return user
    except AuthenticationError as e:
        logger.warning("Authentication error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error("Unexpected authentication error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


def require_role(required_roles: list[UserRole]):
    """Create FastAPI dependency for checking user role.

    Args:
        required_roles: List of roles that have access.

    Returns:
        Callable: FastAPI dependency.

    Raises:
        HTTPException: If user has insufficient rights.

    Example:
        @app.get("/admin")
        async def admin_route(
            user: UserDB = Depends(get_current_user_dependency),
            _: None = Depends(require_role([UserRole.ADMIN])),
        ):
            return {"message": "Admin area"}
    """

    def role_checker(user: UserDB = Depends(get_current_user_dependency)) -> UserDB:
        """Check user role and return it on success."""
        if not check_permission(user.role, required_roles):
            logger.warning(
                "Insufficient permissions: user_id=%s, user_role=%s, required_roles=%s",
                user.id,
                user.role,
                [r.value for r in required_roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {[r.value for r in required_roles]}",
            )
        return user

    return role_checker


def require_dashboard_access(
    required_permission: str = "read",
):
    """Create FastAPI dependency for checking dashboard access.

    Checks if user has access to specified dashboard
    with required permission level.

    Args:
        required_permission: Required access level (read/write/admin).
            Default is "read".

    Returns:
        Callable: FastAPI dependency.

    Raises:
        HTTPException: If user has no access.

    Example:
        @app.get("/dashboards/{dashboard_id}")
        async def get_dashboard(
            dashboard_id: int,
            user: UserDB = Depends(get_current_user_dependency),
            _: None = Depends(require_dashboard_access("read")),
        ):
            return {"message": "Dashboard data"}
    """

    async def access_checker(
        dashboard_id: UUID,
        user: UserDB = Depends(get_current_user_dependency),
        db: AsyncSession = Depends(get_db),
    ) -> UserDB:
        """Check user access to dashboard."""
        if not await check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission=required_permission,
            db=db,
        ):
            logger.warning(
                "Access denied: user_id=%s, dashboard_id=%s, required=%s",
                user.id,
                dashboard_id,
                required_permission,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this dashboard",
            )
        return user

    return access_checker
