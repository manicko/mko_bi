from pydantic import BaseModel, ConfigDict, EmailStr


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


class RegisterRequest(BaseModel):
    """Модель запроса на регистрацию."""

    email: EmailStr
    password: str
    role: str = "viewer"

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
    user_id: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "user_id": 1,
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


class AccessCheck(BaseModel):
    """Модель проверки доступа."""

    user_id: int
    dashboard_id: int
    required_permission: str | None = "read"

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "dashboard_id": 1,
                "required_permission": "read",
            }
        },
    )


class AccessGrant(BaseModel):
    """Модель предоставления доступа."""

    user_id: int
    dashboard_id: int
    permission_level: str = "read"

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "dashboard_id": 1,
                "permission_level": "read",
            }
        },
    )
