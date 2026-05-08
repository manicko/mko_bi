"""Authentication and registration routes.

This module provides endpoints for:
- Registering new users
- User login (authentication)
- JWT token refresh
- Creating registration requests

All endpoints return standardized JSON responses.
"""

from ipaddress import ip_address
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from mkobi.api.deps import get_auth_service, get_current_user_dependency, require_admin_role
from mkobi.core.logging_config import get_logger
from mkobi.core import redis_client
from mkobi.core.security import AsyncRateLimiter
from mkobi.models.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegistrationRequestCreate,
    Token,
)
from mkobi.models.user import UserRead

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _handle_login(
    email: str,
    password: str,
    auth_service,
) -> Token:
    """Common login logic and error handling."""
    # Apply rate limiting for login attempts
    rate_limiter = AsyncRateLimiter(redis_client.get_async_redis_client())
    if not await rate_limiter.check_rate_limit(
        f"login:{email}", max_attempts=5, ttl=300
    ):
        logger.warning("Login rate limit exceeded", extra={"email": email})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    logger.info("Login attempt", extra={"email": email})

    token_data = await auth_service.login_user(email, password)

    if token_data is None:
        logger.warning("Login failed", extra={"email": email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Login successful", extra={"email": email})
    return Token(access_token=token_data["access_token"], token_type="bearer")


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticates user by email and password, returns JWT token.",
)
async def login(
    login_data: LoginRequest,
    auth_service=Depends(get_auth_service),
) -> Token:
    """User login endpoint."""
    return await _handle_login(
        email=login_data.email,
        password=login_data.password,
        auth_service=auth_service,
    )


@router.post(
    "/login/form",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login (form)",
    description="Authentication via OAuth2 form. Calls common /login logic.",
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service=Depends(get_auth_service),
) -> Token:
    """Login endpoint via OAuth2 form."""
    return await _handle_login(
        email=form_data.username,
        password=form_data.password,
        auth_service=auth_service,
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="User registration (admin-only, deprecated for public)",
    description="Creates new user directly. Admin only. Public users should use /register-request instead.",
)
async def register(
    register_data: RegisterRequest,
    auth_service=Depends(get_auth_service),
    admin_user: UserRead = Depends(require_admin_role),
) -> Token:
    """Admin-only user registration endpoint (deprecated for public use).

    Creates user directly and returns JWT access token.
    For public registration, use /auth/register-request instead.

    Args:
        register_data: Model with registration data.
        auth_service: Authentication service.
        admin_user: Current admin user (injected dependency).

    Returns:
        Token: Model with access_token and token_type.

    Raises:
        HTTPException 403: If user is not admin.
        HTTPException 422: Data validation error.
        HTTPException 500: Registration or token creation error.
    """
    logger.warning(
        "Deprecated /auth/register endpoint called. Use /auth/register-request for public registration.",
        extra={"email": register_data.email, "admin_user": admin_user.email},
    )

    try:
        user = await auth_service.register_user(
            email=register_data.email,
            password=register_data.password,
            role=register_data.role,
        )
    except ValueError as e:
        logger.warning(
            "Validation error during registration",
            extra={"email": register_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Registration error",
            extra={"email": register_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration error",
        ) from e

    try:
        access_token = auth_service.create_access_token(user.id, user.role)
    except Exception as e:
        logger.error(
            "Token creation error after registration",
            extra={"email": register_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation error",
        ) from e

    logger.info("User registered successfully by admin", extra={"email": register_data.email, "admin": admin_user.email})
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh token",
    description="Refreshes expired JWT access token.",
)
async def refresh(
    refresh_data: RefreshRequest,
    auth_service=Depends(get_auth_service),
) -> Token:
    """Token refresh endpoint.

    Accepts refresh token (in current implementation - same JWT),
    decodes it and issues new access token.

    Args:
        refresh_data: Model with refresh token.
        auth_service: Authentication service.

    Returns:
        Token: Model with new access_token and token_type.

    Raises:
        HTTPException 401: Invalid or expired token.
        HTTPException 422: Data validation error.
    """
    logger.info("Token refresh attempt")

    payload = auth_service.verify_token(refresh_data.refresh_token)
    if payload is None:
        logger.warning("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    email = payload.get("email")
    role = payload.get("role")

    if user_id is None or email is None or role is None:
        logger.warning("Token missing required data")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = await auth_service.refresh_token(user_id, email, role)
    except ValueError as e:
        logger.warning(
            "User not found during token refresh", extra={"user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error(
            "Token refresh error",
            extra={"user_id": user_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation error",
        ) from e

    logger.info("Token refreshed successfully", extra={"user_id": user_id})
    return Token(access_token=token_data["access_token"], token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user data",
    description="Returns data of the currently authenticated user.",
)
async def get_current_user_info(
    current_user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Endpoint to get current user information.

    Requires valid JWT token in Authorization header.

    Args:
        current_user: Currently authenticated user.

    Returns:
        UserRead: User model without password.

    Raises:
        HTTPException 401: Invalid or missing token.
    """
    logger.info("Current user data request", extra={"email": current_user.email})
    return current_user


@router.post(
    "/register-request",
    status_code=status.HTTP_201_CREATED,
    summary="Registration request",
    description="Creates registration request. Admin must approve the request.",
)
async def register_request(
    request_data: RegistrationRequestCreate,
    request: Request,
    auth_service=Depends(get_auth_service),
) -> dict[str, Any]:
    """Registration request creation endpoint.

    Saves request to database with PENDING status.
    Admin must approve or reject the request.

    Args:
        request_data: Request data (email).
        request: Request object to get IP.
        auth_service: Authentication service.

    Returns:
        dict: Success message.

    Raises:
        HTTPException 422: Request already exists.
    """
    # Get client IP address
    client_ip: str | None = None
    if request.client:
        client_ip = str(ip_address(request.client.host))

    # Apply rate limiting for registration requests
    rate_limiter = AsyncRateLimiter(redis_client.get_async_redis_client())
    rate_limit_key = f"register-request:{client_ip}" if client_ip else f"register-request:{request_data.email}"
    if not await rate_limiter.check_rate_limit(
        rate_limit_key, max_attempts=3, ttl=3600
    ):
        logger.warning(
            "Registration request rate limit exceeded",
            extra={"email": request_data.email, "ip": client_ip},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration requests. Try again later.",
        )

    logger.info(
        "Registration request attempt",
        extra={"email": request_data.email, "ip": client_ip},
    )

    try:
        result = await auth_service.register_request(
            email=request_data.email,
            ip=client_ip,
        )
    except ValueError as e:
        logger.warning(
            "Validation error creating registration request",
            extra={"email": request_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Error creating registration request",
            extra={"email": request_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration request error",
        ) from e

    logger.info(
        "Registration request created",
        extra={"email": request_data.email, "id": str(result["id"])},
    )
    return {"message": "Request submitted", "id": result["id"]}
