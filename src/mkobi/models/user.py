from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID

from mkobi.models.enums import UserRole


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    role: UserRole

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "role": UserRole.VIEWER,
            }
        },
    )


class UserCreate(UserBase):
    """Model for creating new user."""

    password: str

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


class UserRead(UserBase):
    """Model for reading user data (without password)."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "role": UserRole.VIEWER,
                "created_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class UserDB(UserBase):
    """User model for database (with password hash)."""

    id: UUID
    password_hash: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "password_hash": "$2b$12$examplehash",
                "role": UserRole.VIEWER,
                "created_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class UserUpdate(BaseModel):
    """Model for updating user."""

    email: EmailStr | None = None
    role: UserRole | None = None
    password: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "role": UserRole.EDITOR,
                "password": "new_secure_password",
            }
        },
    )
