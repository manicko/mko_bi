from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional

from mko_bi.services.user_service import create_user, get_user_by_email
from mko_bi.core.security import create_access_token, verify_password
from mko_bi.core.permissions import check_access

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "viewer"


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest) -> LoginResponse:
    """Login endpoint for user authentication.

    Args:
        request: Login request with email and password

    Returns:
        JWT access token

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    token = create_access_token({"user_id": user.id})

    return LoginResponse(access_token=token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest) -> LoginResponse:
    """Register endpoint for new users.

    Args:
        request: Registration request with email, password, and role

    Returns:
        JWT access token for the new user

    Raises:
        HTTPException: 400 if user already exists or validation fails
    """
    try:
        user = create_user(request.email, request.password, request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user",
        )

    token = create_access_token({"user_id": user.id})
    return LoginResponse(access_token=token)
