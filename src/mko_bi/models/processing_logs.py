from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mko_bi.models.user_roles import ProcessingStatusEnum


class ProcessingLogBase(BaseModel):
    """Базовая модель для логов обработки."""

    dashboard_id: UUID | None = None
    status: ProcessingStatusEnum
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "success",
                "message": "Processing completed successfully",
                "started_at": "2026-04-24T16:02:46+03:00",
                "finished_at": "2026-04-24T16:03:15+03:00",
            }
        },
    )


class ProcessingLogCreate(ProcessingLogBase):
    """Модель для создания лога обработки."""

    pass


class ProcessingLogUpdate(BaseModel):
    """Модель для обновления лога обработки."""

    status: ProcessingStatusEnum | None = None
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "status": "failed",
                "message": "Processing failed due to error",
                "finished_at": "2026-04-24T16:03:15+03:00",
            }
        },
    )


class ProcessingLogRead(ProcessingLogBase):
    """Модель для чтения данных лога обработки."""

    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "success",
                "message": "Processing completed successfully",
                "started_at": "2026-04-24T16:02:46+03:00",
                "finished_at": "2026-04-24T16:03:15+03:00",
            }
        },
    )
