from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID

from mkobi.models.enums import UserRole


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "secure_password123",
            }
        },
    )


class RegistrationRequestCreate(BaseModel):
    """Registration request model."""

    email: EmailStr

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
            }
        },
    )


class RegistrationRequestResponse(BaseModel):
    """Registration request response model."""

    id: UUID
    email: EmailStr
    status: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "status": "pending",
            }
        },
    )


class RegisterRequest(BaseModel):
    """Register request model."""

    email: EmailStr
    password: str
    role: UserRole = UserRole.VIEWER

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "secure_password123",
                "role": UserRole.VIEWER,
            }
        },
    )


class Token(BaseModel):
    """Access token model."""

    access_token: str
    token_type: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        },
    )


class TokenData(BaseModel):
    """Token data model."""

    email: EmailStr | None = None
    user_id: UUID | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        },
    )


class RefreshRequest(BaseModel):
    """Token refresh request model."""

    refresh_token: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        },
    )


class ChangePasswordRequest(BaseModel):
    """Password change request model."""

    current_password: str
    new_password: str
    confirm_password: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "current_password": "old_password123",
                "new_password": "new_secure_password456",
                "confirm_password": "new_secure_password456",
            }
        },
    )
