from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Literal
from uuid import UUID


class UserBase(BaseModel):
    """Базовая модель пользователя."""

    email: EmailStr
    role: Literal["admin", "editor", "viewer"]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "role": "viewer",
            }
        },
    )


class UserCreate(UserBase):
    """Модель для создания нового пользователя."""

    password: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "secure_password123",
                "role": "viewer",
            }
        },
    )


class UserRead(UserBase):
    """Модель для чтения данных пользователя (без пароля)."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "role": "viewer",
                "created_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class UserDB(UserBase):
    """Модель пользователя для базы данных (с хэшем пароля)."""

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
                "role": "viewer",
                "created_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class UserUpdate(BaseModel):
    """Модель для обновления пользователя."""

    email: EmailStr | None = None
    role: Literal["admin", "editor", "viewer"] | None = None
    password: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "role": "editor",
                "password": "new_secure_password",
            }
        },
    )
