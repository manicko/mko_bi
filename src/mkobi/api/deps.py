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
from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

if TYPE_CHECKING:
    from mkobi.services.data_service import DataService
    from mkobi.services.filter_service import FilterService
    from mkobi.services.graph_service import GraphService
    from mkobi.services.layout_service import LayoutService
    from mkobi.services.processing_config_service import ProcessingConfigService
    from mkobi.services.processing_log_service import ProcessingLogService
    from mkobi.services.user_service import UserService

from mkobi.core.permissions import (
    check_dashboard_access,
    check_role,
    AuthenticationError,
)
from mkobi.core.security import decode_token
from mkobi.db.repositories.user_repo import UserRepository
# DEPRECATED: get_session is kept for backwards compatibility only.
# External code may import it from here. Remove in v2.0.
from mkobi.db.session import get_db, get_session  # noqa: F401
from mkobi.models.enums import UserRole
from mkobi.models.user import UserRead
from mkobi.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Explicitly define exports for mypy
__all__ = [
    "get_db",
    "get_session",
    "get_current_user_dependency",
    "get_db_dependency",
    "require_admin_role",
    "require_editor_role",
    "require_viewer_role",
    "get_dashboard_service",
    "CurrentUser",
    "AdminUser",
    "EditorUser",
    "ViewerUser",
    "get_dashboard_permissions",
    "get_user_repository",
    "get_dashboard_repository",
    "get_access_repository",
    "get_aggregated_data_repository",
    "get_layout_repository",
    "get_filter_repository",
    "get_dashboard_filter_repository",
    "get_processing_config_repository",
    "get_processing_log_repository",
    "get_graph_repository",
    "get_auth_service",
    "get_user_service",
    "get_dashboard_service",
    "get_filter_service",
    "get_layout_service",
    "get_data_service",
    "get_processing_config_service",
    "get_processing_log_service",
    "get_token_from_header",
]


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


def get_user_repository() -> UserRepository:
    """DI factory for user repository.

    Args:
        db: Async database session.

    Returns:
        IUserRepository: User repository implementation.
    """
    from mkobi.db.repositories.user_repo import UserRepository
    return UserRepository()


def get_dashboard_repository() -> Any:
    """DI factory for dashboard repository.

    Returns:
        DashboardRepository: Dashboard repository implementation.
    """
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    return DashboardRepository()


def get_access_repository() -> Any:
    """DI factory for access repository.

    Returns:
        AccessRepository: Access repository implementation.
    """
    from mkobi.db.repositories.access_repo import AccessRepository
    return AccessRepository()


def get_aggregated_data_repository() -> Any:
    """DI factory for aggregated data repository.

    Returns:
        AggregatedDataRepository: Aggregated data repository implementation.
    """
    from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
    return AggregatedDataRepository()


def get_layout_repository() -> Any:
    """DI factory for layout repository.

    Returns:
        LayoutRepository: Layout repository implementation.
    """
    from mkobi.db.repositories.layout_repo import LayoutRepository
    return LayoutRepository()


def get_filter_repository() -> Any:
    """DI factory for filter repository.

    Returns:
        FilterRepository: Filter repository implementation.
    """
    from mkobi.db.repositories.filter_repo import FilterRepository
    return FilterRepository()


def get_dashboard_filter_repository() -> Any:
    """DI factory for dashboard filter repository.

    Returns:
        DashboardFilterRepository: Dashboard filter repository implementation.
    """
    from mkobi.db.repositories.dashboard_filter_repo import DashboardFilterRepository
    return DashboardFilterRepository()


def get_processing_config_repository() -> Any:
    """DI factory for processing config repository.

    Returns:
        ProcessingConfigRepository: Processing config repository implementation.
    """
    from mkobi.db.repositories.processing_config_repo import ProcessingConfigRepository
    return ProcessingConfigRepository()


def get_processing_log_repository() -> Any:
    """DI factory for processing log repository.

    Returns:
        ProcessingLogRepository: Processing log repository implementation.
    """
    from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
    return ProcessingLogRepository()


def get_registration_request_repository() -> Any:
    """DI factory for registration request repository.

    Returns:
        RegistrationRequestRepository: Registration request repository implementation.
    """
    from mkobi.db.repositories.registration_request_repo import RegistrationRequestRepository
    return RegistrationRequestRepository()


def get_graph_repository() -> Any:
    """DI factory for graph repository.

    Returns:
        GraphRepository: Graph repository implementation.
    """
    from mkobi.db.repositories.graph_repo import GraphRepository
    return GraphRepository()


# --- Dependency Injection for services ---


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    reg_request_repo: Any = Depends(get_registration_request_repository),
) -> AuthService:
    """DI factory for authentication service.

    Args:
        user_repo: Injected user repository.
        reg_request_repo: Injected registration request repository.

    Returns:
        AuthService: Authentication service implementation.
    """
    from mkobi.services.auth_service import AuthService
    return AuthService(user_repo, reg_request_repo)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """DI factory for user service.

    Args:
        user_repo: Injected user repository.

    Returns:
        UserService: User service implementation.
    """
    from mkobi.services.user_service import UserService

    return UserService(user_repo)


def get_dashboard_service(
    dashboard_repo: Any = Depends(get_dashboard_repository),
    access_repo: Any = Depends(get_access_repository),
) -> Any:
    """DI factory for dashboard service.

    Args:
        dashboard_repo: Injected dashboard repository.
        access_repo: Injected access repository.

    Returns:
        DashboardService: Dashboard service implementation.
    """
    from mkobi.services.dashboard_service import DashboardService
    return DashboardService(dashboard_repo, access_repo)


def get_filter_service(
    filter_repo: Any = Depends(get_filter_repository),
) -> FilterService:
    """DI factory for filter service.

    Args:
        filter_repo: Injected filter repository.

    Returns:
        FilterService: Filter service implementation.
    """
    from mkobi.services.filter_service import FilterService
    return FilterService(filter_repo)


def get_layout_service(
    layout_repo: Any = Depends(get_layout_repository),
) -> LayoutService:
    """DI factory for layout service.

    Args:
        layout_repo: Injected layout repository.

    Returns:
        LayoutService: Layout service implementation.
    """
    from mkobi.services.layout_service import LayoutService
    return LayoutService(layout_repo)


def get_data_service(
    agg_repo: Any = Depends(get_aggregated_data_repository),
    log_repo: Any = Depends(get_processing_log_repository),
    graph_repo: Any = Depends(get_graph_repository),
) -> DataService:
    """DI factory for data service.

    Args:
        agg_repo: Injected aggregated data repository.
        log_repo: Injected processing log repository.
        graph_repo: Injected graph repository.

    Returns:
        DataService: Data service implementation.
    """
    from mkobi.services.data_service import DataService
    return DataService(agg_repo, log_repo, graph_repo)


def get_graph_service(
    graph_repo: Any = Depends(get_graph_repository),
) -> GraphService:
    """DI factory for graph service.

    Args:
        graph_repo: Injected graph repository.

    Returns:
        GraphService: Graph service implementation.
    """
    from mkobi.services.graph_service import GraphService
    return GraphService(graph_repo)


def get_processing_config_service(
    config_repo: Any = Depends(get_processing_config_repository),
) -> ProcessingConfigService:
    """DI factory for processing config service.

    Args:
        config_repo: Injected processing config repository.

    Returns:
        ProcessingConfigService: Processing config service implementation.
    """
    from mkobi.services.processing_config_service import ProcessingConfigService
    return ProcessingConfigService(config_repo)


def get_processing_log_service(
    log_repo: Any = Depends(get_processing_log_repository),
) -> ProcessingLogService:
    """DI factory for processing log service.

    Args:
        log_repo: Injected processing log repository.

    Returns:
        ProcessingLogService: Processing log service implementation.
    """
    from mkobi.services.processing_log_service import ProcessingLogService
    return ProcessingLogService(log_repo)


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
    return str(credentials.credentials)


async def get_current_user_dependency(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserRead:
    """Get current authenticated user.

    Decodes JWT token, extracts user_id and retrieves user
    data from database.

    Args:
        token: JWT access token.
        db: Database session.

    Returns:
        UserRead: Current user data.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    try:
        payload = decode_token(token)
        if payload is None:
            logger.warning("Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_raw = payload.get("user_id")
        if user_id_raw is None:
            logger.warning("Token missing user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = UUID(str(user_id_raw))

        repo = UserRepository()
        user = await repo.get(id=user_id, db=db)
        if user is None:
            logger.warning("User not found: user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info("User authenticated: user_id=%s", user_id)
        return cast(UserRead, UserRead.model_validate(user))
    except ExpiredSignatureError as e:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except AuthenticationError as e:
        logger.warning("Authentication error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error("Error getting current user: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# --- Role checks ---


def require_admin_role(
    user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Require admin role.

    Args:
        user: Current authenticated user.

    Returns:
        UserRead: User if has admin role.

    Raises:
        HTTPException: If user is not admin.
    """
    if not check_role(user.role, UserRole.ADMIN):
        logger.warning(
            "Admin access denied: user_id=%s, role=%s",
            user.id,
            user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_editor_role(
    user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Require editor role or higher.

    Args:
        user: Current authenticated user.

    Returns:
        UserRead: User if has editor role or higher.

    Raises:
        HTTPException: If user has insufficient permissions.
    """
    if not check_role(user.role, UserRole.EDITOR):
        logger.warning(
            "Editor access denied: user_id=%s, role=%s",
            user.id,
            user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor access required",
        )
    return user


def require_viewer_role(
    user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Require viewer role or higher (any authenticated user).

    Args:
        user: Current authenticated user.

    Returns:
        UserRead: User if authenticated.

    Raises:
        HTTPException: If user is not authenticated.
    """
    # All authenticated users have at least viewer role
    return user


def require_role_dependency(
    required_role: UserRole,
) -> (AsyncSession | UserRead) | None:
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
            return {"message": "Access granted"}
    """

    async def role_checker(
        user: UserRead = Depends(get_current_user_dependency),
    ) -> UserRead:
        if not check_role(user.role, required_role):
            logger.warning(
                "Role check failed: user_id=%s, role=%s, required=%s",
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
    access_repo: Any = Depends(get_access_repository),
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
