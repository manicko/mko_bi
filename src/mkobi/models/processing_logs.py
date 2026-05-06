from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mkobi.models.enums import ProcessingStatusEnum


class ProcessingLogFilter(BaseModel):
    """Модель для фильтрации логов обработки."""

    dashboard_id: UUID | None = None
    status: ProcessingStatusEnum | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    skip: int = 0
    limit: int = 100

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "failed",
                "date_from": "2026-04-01T00:00:00+03:00",
                "date_to": "2026-04-30T23:59:59+03:00",
                "skip": 0,
                "limit": 100,
            }
        },
    )


class ProcessingLogCreate(BaseModel):
    """Модель для создания лога обработки."""

    dashboard_id: UUID | None = None
    status: ProcessingStatusEnum
    message: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "started",
                "message": "Processing started",
            }
        },
    )


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


class ProcessingLogRead(BaseModel):
    """Модель для чтения данных лога обработки."""

    id: UUID
    dashboard_id: UUID | None = None
    status: ProcessingStatusEnum
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

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
