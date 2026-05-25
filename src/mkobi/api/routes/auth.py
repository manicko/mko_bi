"""Authentication and registration routes.

This module provides endpoints for:
- Registering new users
- User login (authentication)
- JWT token refresh
- User logout
- Creating registration requests

All endpoints return standardized JSON responses.
"""

from ipaddress import ip_address
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_auth_service,
    get_current_user_dependency,
    require_admin_role,
    get_db_dependency,
)
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.config import get_config
from mkobi.core.logging_config import get_logger
from mkobi.core import redis_client
from mkobi.core.security import (
    AsyncRateLimiter,
    COOKIE_NAME,
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    delete_secure_cookie,
    set_secure_cookie,
)
from mkobi.models.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    RegistrationRequestCreate,
    SuccessResponse,
    Token,
    TokenWithUser,
)
from mkobi.models.user import UserRead

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"], redirect_slashes=False)


async def _handle_login(
    email: str,
    password: str,
    auth_service,
    request: Request,
    response: Response,
    db: AsyncSession,
) -> TokenWithUser:
    """Common login logic and error handling."""
    # Apply rate limiting for login attempts based on client IP
    # IP-based rate limiting prevents email enumeration via rate limit side-channel
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = auth_service._rate_limiter
    if not await rate_limiter.check_rate_limit(
        f"login:{client_ip}", max_attempts=5, ttl=300
    ):
        logger.warning("Login rate limit exceeded", extra={"ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    logger.info("Login attempt", extra={"email": email})

    token_data = await auth_service.login_user(email, password, db=db)

    if token_data is None:
        logger.warning("Login failed", extra={"email": email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Login successful", extra={"email": email})

    # Create refresh token and set as httpOnly cookie
    user = token_data["user"]
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    set_secure_cookie(
        response=response,
        key=COOKIE_NAME,
        value=refresh_token,
        max_age=get_config().jwt.refresh_token_expire_minutes * 60,
    )

    return TokenWithUser(
        access_token=token_data["access_token"],
        token_type="bearer",
        user=token_data["user"],
    )


@router.post(
    "/login",
    response_model=TokenWithUser,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticates user by email and password, returns JWT token with user data.",
)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    auth_service=Depends(get_auth_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> TokenWithUser:
    """User login endpoint."""
    return await _handle_login(
        email=login_data.email,
        password=login_data.password,
        auth_service=auth_service,
        request=request,
        response=response,
        db=db,
    )


@router.post(
    "/login/form",
    response_model=TokenWithUser,
    status_code=status.HTTP_200_OK,
    summary="User login (form)",
    description="Authentication via OAuth2 form. Calls common /login logic.",
)
async def login_form(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service=Depends(get_auth_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> TokenWithUser:
    """Login endpoint via OAuth2 form."""
    return await _handle_login(
        email=form_data.username,
        password=form_data.password,
        auth_service=auth_service,
        request=request,
        response=response,
        db=db,
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
    db: AsyncSession = Depends(get_db_dependency),
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
            db=db,
            role=register_data.role.value,
        )
    except ValueError as e:
        logger.warning(
            "Validation error during registration",
            extra={"email": register_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    description="Refreshes expired JWT access token using httpOnly refresh token cookie.",
)
async def refresh(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> Token:
    """Token refresh endpoint.

    Accepts refresh token from httpOnly cookie,
    decodes it and issues new access token.

    Args:
        request: Request object to access cookies.
        session: Async database session.

    Returns:
        Token: Model with new access_token and token_type.

    Raises:
        HTTPException 401: Invalid or expired token.
    """
    refresh_token_value = request.cookies.get(COOKIE_NAME)
    if not refresh_token_value:
        logger.warning("No refresh token in cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Token refresh attempt")

    payload = validate_refresh_token(refresh_token_value)
    if payload is None:
        logger.warning("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Token missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserRepository().get(UUID(user_id), session)
    if user is None:
        logger.warning("User not found during refresh", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"user_id": str(user.id), "email": user.email, "role": user.role}
    )

    logger.info("Token refreshed successfully", extra={"user_id": user_id})
    return Token(access_token=access_token, token_type="bearer")


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
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout current user by clearing refresh token cookie.",
)
async def logout(
    response: Response,
    current_user: Annotated[UserRead, Depends(get_current_user_dependency)],
) -> SuccessResponse:
    """Logout endpoint.

    Clears the refresh token cookie and logs the user out.

    Args:
        response: FastAPI Response object to set/delete cookies.
        current_user: Currently authenticated user.

    Returns:
        SuccessResponse: Success message.
    """
    logger.info("User logging out", extra={"email": current_user.email})
    delete_secure_cookie(response, COOKIE_NAME)
    return SuccessResponse(message="Logged out successfully")


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change current user password. Requires current password verification.",
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserRead = Depends(get_current_user_dependency),
    auth_service=Depends(get_auth_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Password change endpoint.

    Validates new password confirmation and current password,
    then updates the password in the database.

    Args:
        password_data: Password change request data.
        current_user: Currently authenticated user.
        auth_service: Authentication service.

    Returns:
        dict: Success message.

    Raises:
        HTTPException 400: If password confirmation does not match.
        HTTPException 401: If current password is incorrect.
    """
    # Validate password confirmation matches
    if password_data.new_password != password_data.confirm_password:
        logger.warning(
            "Password change failed: confirmation mismatch",
            extra={"user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match",
        )

    try:
        await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            db=db,
        )
    except ValueError as e:
        logger.warning(
            "Password change failed",
            extra={"user_id": str(current_user.id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Password change error",
            extra={"user_id": str(current_user.id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change error",
        ) from e

    logger.info("Password changed successfully", extra={"user_id": str(current_user.id)})
    return {"message": "Password changed successfully"}


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
    db: AsyncSession = Depends(get_db_dependency),
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
    rate_limiter = AsyncRateLimiter(
        redis_client.get_async_redis_client(),
        fail_closed=get_config().rate_limiter_fail_closed,
    )
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
            db=db,
            ip=client_ip,
        )
    except ValueError as e:
        logger.warning(
            "Validation error creating registration request",
            extra={"email": request_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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