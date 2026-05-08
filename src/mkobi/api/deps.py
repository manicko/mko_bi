"""FastAPI dependencies for API routes.

This module provides ready-to-use FastAPI dependencies for use in API routes,
including authentication, authorization and access checks.

Typical usage scenarios:
    - Protect endpoints with authentication
    - Check user roles
    - Check dashboard access
    - Get current user
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.core.permissions import (
    get_current_user,
    check_dashboard_access,
    check_role,
    AuthenticationError,
)
from mkobi.db.session import get_db, get_session  # noqa: F401 - re-exported for backwards compatibility
from mkobi.models.enums import UserRole
from mkobi.models.user import UserRead

logger = logging.getLogger(__name__)


# --- Base dependencies ---


security = HTTPBearer()


async def get_db_dependency() -> AsyncSession:
    """Database session dependency for FastAPI routes.

    Creates a new session for each request and closes it after completion.

    Yields:
        AsyncSession: SQLAlchemy async session.

    Example:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db_dependency)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with get_session() as db:
        yield db


# --- Dependency Injection for repositories ---


def get_user_repository():
    """DI factory for user repository.

    Args:
        db: Async database session.

    Returns:
        IUserRepository: User repository implementation.
    """
    from mkobi.db.repositories.user_repo import UserRepository
    return UserRepository()


def get_dashboard_repository():
    """DI factory for dashboard repository.

    Returns:
        DashboardRepository: Dashboard repository implementation.
    """
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    return DashboardRepository()


def get_access_repository():
    """DI factory for access repository.

    Returns:
        AccessRepository: Access repository implementation.
    """
    from mkobi.db.repositories.access_repo import AccessRepository
    return AccessRepository()


def get_aggregated_data_repository():
    """DI factory for aggregated data repository.

    Returns:
        AggregatedDataRepository: Aggregated data repository implementation.
    """
    from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
    return AggregatedDataRepository()


def get_filter_repository():
    """DI factory for filter repository.

    Returns:
        FilterRepository: Filter repository implementation.
    """
    from mkobi.db.repositories.filter_repo import FilterRepository
    return FilterRepository()


def get_processing_config_repository():
    """DI factory for processing config repository.

    Returns:
        ProcessingConfigRepository: Processing config repository implementation.
    """
    from mkobi.db.repositories.processing_config_repo import ProcessingConfigRepository
    return ProcessingConfigRepository()


def get_processing_log_repository():
    """DI factory for processing log repository.

    Returns:
        ProcessingLogRepository: Processing log repository implementation.
    """
    from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
    return ProcessingLogRepository()


def get_graph_repository():
    """DI factory for graph repository.

    Returns:
        GraphRepository: Graph repository implementation.
    """
    from mkobi.db.repositories.graph_repo import GraphRepository
    return GraphRepository()


# --- Dependency Injection for services ---


def get_auth_service():
    """DI factory for authentication service.

    Returns:
        AuthService: Authentication service implementation.
    """
    from mkobi.services.auth_service import AuthService
    return AuthService()


def get_user_service(
    user_repo=Depends(get_user_repository),
):
    """DI factory for user service.

    Args:
        user_repo: Injected user repository.

    Returns:
        UserService: User service implementation.
    """
    from mkobi.services.user_service import UserService
    return UserService(user_repo)


def get_dashboard_service(
    dashboard_repo=Depends(get_dashboard_repository),
    access_repo=Depends(get_access_repository),
):
    """DI factory for dashboard service.

    Args:
        dashboard_repo: Injected dashboard repository.
        access_repo: Injected access repository.

    Returns:
        DashboardService: Dashboard service implementation.
    """
    from mkobi.services.dashboard_service import DashboardService
    return DashboardService(dashboard_repo, access_repo)


def get_filter_service():
    """DI factory for filter service.

    Returns:
        FilterService: Filter service implementation.
    """
    from mkobi.services.filter_service import FilterService
    return FilterService()


def get_data_service():
    """DI factory for data service.

    Returns:
        DataService: Data service implementation.
    """
    from mkobi.services.data_service import DataService
    return DataService()


def get_processing_config_service():
    """DI factory for processing config service.

    Returns:
        ProcessingConfigService: Processing config service implementation.
    """
    from mkobi.services.processing_config_service import ProcessingConfigService
    return ProcessingConfigService()


def get_processing_log_service():
    """DI factory for processing log service.

    Returns:
        ProcessingLogService: Processing log service implementation.
    """
    from mkobi.services.processing_log_service import ProcessingLogService
    return ProcessingLogService()


# --- Authentication ---


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract token from Authorization header.

    Args:
        credentials: Credentials from header.

    Returns:
        str: JWT token.

    Raises:
        HTTPException: If header is missing or incorrect.
    """
    if credentials.scheme.lower() != "bearer":
        logger.warning("Invalid authentication scheme: %s", credentials.scheme)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user_dependency(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserRead:
    """Get current authenticated user.

    Decodes JWT token, extracts user_id and retrieves user
    data from database.

    Args:
        token: JWT access token.
        db: Async database session.

    Returns:
        UserRead: Authenticated user model (without password hash).

    Raises:
        HTTPException: If token is invalid, expired or user not found.

    Example:
        @app.get("/users/me")
        async def read_users_me(user: UserRead = Depends(get_current_user_dependency)):
            return user
    """
    try:
        user = await get_current_user(token, db)
        logger.debug("User authenticated: user_id=%s", user.id)
        return user
    except ExpiredSignatureError:
        logger.warning("Expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except AuthenticationError:
        # AuthenticationError already logged in get_current_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not authenticate user",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception as e:
        logger.error("Unexpected authentication error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# --- Authorization (role checks) ---


def require_admin_role(
    user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Require admin role.

    Args:
        user: User (obtained via get_current_user_dependency).

    Returns:
        UserRead: User if has admin role.

    Raises:
        HTTPException: If user does not have admin role.

    Example:
        @app.post("/users/")
        async def create_user(
            user_data: UserCreate,
            _: UserRead = Depends(require_admin_role),
        ):
            return create_user(user_data)
    """
    if not check_role(user.role, UserRole.ADMIN):
        logger.warning(
            "Admin role required for user: user_id=%s, role=%s",
            user.id,
            user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


def require_editor_role(
    user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Require editor role or higher (editor, admin).

    Args:
        user: User (obtained via get_current_user_dependency).

    Returns:
        UserRead: User if has editor or admin role.

    Raises:
        HTTPException: If user has insufficient permissions.

    Example:
        @app.post("/upload/")
        async def upload_file(
            _: UserRead = Depends(require_editor_role),
        ):
            return {"message": "Upload allowed"}
    """
    if not check_role(user.role, UserRole.EDITOR):
        logger.warning(
            "Editor role or higher required for user: user_id=%s, role=%s",
            user.id,
            user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor role or higher required",
        )
    return user


def require_viewer_role(
    user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Require viewer role or higher (viewer, editor, admin).

    Essentially checks that user is authenticated,
    since viewer is the minimum role.

    Args:
        user: User (obtained via get_current_user_dependency).

    Returns:
        UserRead: User.

    Example:
        @app.get("/dashboards/")
        async def list_dashboards(
            user: UserRead = Depends(require_viewer_role),
        ):
            return {"message": "Access granted"}
    """
    # All authenticated users have at least viewer role
    return user


def require_role_dependency(required_role: str):
    """Create dependency for checking specific role.

    Universal dependency for checking any role.

    Args:
        required_role: Required role (viewer, editor, admin).

    Returns:
        Callable: FastAPI dependency function.

    Raises:
        HTTPException: If user has insufficient permissions.

    Example:
        @app.get("/admin-only")
        async def admin_only(
            user: UserRead = Depends(require_role_dependency(UserRole.ADMIN)),
        ):
            return {"message": "Admin area"}
    """

    def role_checker(
        user: UserRead = Depends(get_current_user_dependency),
    ) -> UserRead:
        if not check_role(user.role, required_role):
            logger.warning(
                "Insufficient permissions: user_id=%s, user_role=%s, required_role=%s",
                user.id,
                user.role,
                required_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} or higher required",
            )
        return user

    return role_checker


# --- Dashboard access checks ---


async def require_dashboard_read_access(
    dashboard_id: UUID,
    user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserRead:
    """Require read access to dashboard.

    Args:
        dashboard_id: Dashboard ID (from path).
        user: User (obtained via get_current_user_dependency).
        db: Async database session.

    Returns:
        UserRead: User if has access.

    Raises:
        HTTPException: If user has no read access.

    Example:
        @app.get("/dashboards/{dashboard_id}")
        async def get_dashboard(
            dashboard_id: UUID,
            user: UserRead = Depends(require_dashboard_read_access),
        ):
            return {"message": "Dashboard data"}
    """
    if not await check_dashboard_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    ):
        logger.warning(
            "Read access denied: user_id=%s, dashboard_id=%s",
            user.id,
            dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have read access to this dashboard",
        )
    return user


async def require_dashboard_write_access(
    dashboard_id: UUID,
    user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserRead:
    """Require write (edit) access to dashboard.

    Args:
        dashboard_id: Dashboard ID (from path).
        user: User (obtained via get_current_user_dependency).
        db: Async database session.

    Returns:
        UserRead: User if has write access.

    Raises:
        HTTPException: If user has no write access.

    Example:
        @app.put("/dashboards/{dashboard_id}")
        async def update_dashboard(
            dashboard_id: UUID,
            user: UserRead = Depends(require_dashboard_write_access),
        ):
            return {"message": "Update allowed"}
    """
    if not await check_dashboard_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    ):
        logger.warning(
            "Write access denied: user_id=%s, dashboard_id=%s",
            user.id,
            dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have write access to this dashboard",
        )
    return user


async def require_dashboard_admin_access(
    dashboard_id: UUID,
    user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserRead:
    """Require admin access to dashboard.

    Args:
        dashboard_id: Dashboard ID (from path).
        user: User (obtained via get_current_user_dependency).
        db: Async database session.

    Returns:
        UserRead: User if has admin access.

    Raises:
        HTTPException: If user has no admin access.

    Example:
        @app.delete("/dashboards/{dashboard_id}")
        async def delete_dashboard(
            dashboard_id: UUID,
            user: UserRead = Depends(require_dashboard_admin_access),
        ):
            return {"message": "Delete allowed"}
    """
    if not await check_dashboard_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        required_permission="admin",
        db=db,
    ):
        logger.warning(
            "Admin access denied: user_id=%s, dashboard_id=%s",
            user.id,
            dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have admin access to this dashboard",
        )
    return user


# --- Combined dependencies ---

# Typed aliases for convenience
CurrentUser = Annotated[UserRead, Depends(get_current_user_dependency)]
AdminUser = Annotated[UserRead, Depends(require_admin_role)]
EditorUser = Annotated[UserRead, Depends(require_editor_role)]
ViewerUser = Annotated[UserRead, Depends(require_viewer_role)]


async def get_dashboard_permissions(
    dashboard_id: UUID,
    user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
    access_repo=Depends(get_access_repository),
) -> dict[str, Any]:
    """Get user's access permissions for dashboard.

    Args:
        dashboard_id: Dashboard ID.
        user: User.
        db: Async database session.
        access_repo: Access repository.

    Returns:
        dict: Dictionary with access permission info.
    """
    permission = await access_repo.check_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        db=db,
    )

    return {
        "user_id": user.id,
        "dashboard_id": dashboard_id,
        "permission": permission,
        "can_read": await check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission="view",
            db=db,
        ),
        "can_write": await check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission="edit",
            db=db,
        ),
        "can_admin": await check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission="admin",
            db=db,
        ),
    }
