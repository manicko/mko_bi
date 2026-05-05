from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID

from mko_bi.models.user_roles import UserRole, UserRoleEnum


class LoginRequest(BaseModel):
    """Модель запроса на вход."""

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
    """Модель запроса на регистрацию (заявка)."""

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
    """Модель ответа на создание заявки на регистрацию."""

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
    """Модель запроса на регистрацию."""

    email: EmailStr
    password: str
    role: UserRoleEnum = UserRoleEnum.VIEWER

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "secure_password123",
                "role": UserRoleEnum.VIEWER,
            }
        },
    )


class Token(BaseModel):
    """Модель токена доступа."""

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
    """Модель данных токена."""

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
    """Модель запроса на обновление токена."""

    refresh_token: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        },
    )
