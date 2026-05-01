from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mko_bi.models.types import ProcessingSettingsDict


class ProcessingConfigBase(BaseModel):
    """Базовая модель для настроек обработки."""

    settings: ProcessingSettingsDict

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "settings": {
                    "loader": "sales_loader",
                    "date_column": "event_date",
                    "timezone": "UTC",
                }
            }
        },
    )


class ProcessingConfigCreate(ProcessingConfigBase):
    """Модель для создания настроек обработки."""

    pass


class ProcessingConfigUpdate(BaseModel):
    """Модель для обновления настроек обработки."""

    settings: ProcessingSettingsDict | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "settings": {
                    "loader": "updated_loader",
                    "date_column": "updated_date",
                    "timezone": "Europe/Moscow",
                }
            }
        },
    )


class ProcessingConfigRead(ProcessingConfigBase):
    """Модель для чтения данных настроек обработки."""

    dashboard_id: UUID
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "settings": {
                    "loader": "sales_loader",
                    "date_column": "event_date",
                    "timezone": "UTC",
                },
                "updated_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )
