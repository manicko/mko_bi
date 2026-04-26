from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccessCheck(BaseModel):
    """Модель для проверки доступа к дашборду."""

    user_id: UUID
    dashboard_id: UUID
    required_permission: str = "view"

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440001",
                "required_permission": "view",
            }
        },
    )


class AccessGrant(BaseModel):
    """Модель для предоставления доступа к дашборду."""

    user_id: UUID
    dashboard_id: UUID
    permission_level: str = "view"

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440001",
                "permission_level": "edit",
            }
        },
    )