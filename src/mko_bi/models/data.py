from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime
from uuid import UUID

from mko_bi.models.user_roles import GraphTypeEnum


class DataUpload(BaseModel):
    """Модель для загрузки данных."""

    file: bytes
    filename: str
    dashboard_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "filename": "data.csv.gz",
                "dashboard_id": 1,
            }
        },
    )


class UploadResponse(BaseModel):
    """Модель ответа при загрузке файла."""

    task_id: UUID
    filename: str
    dashboard_id: int
    status: str
    message: str
    uploaded_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "data.csv.gz",
                "dashboard_id": 1,
                "status": "uploaded",
                "message": "File uploaded successfully",
                "uploaded_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class ProcessingStatus(BaseModel):
    """Модель статуса обработки."""

    task_id: UUID
    filename: str
    dashboard_id: int
    status: str
    progress: int = Field(0, ge=0, le=100)
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "data.csv.gz",
                "dashboard_id": 1,
                "status": "processing",
                "progress": 50,
                "message": "Processing data...",
                "started_at": "2026-04-24T16:02:46+03:00",
                "completed_at": None,
            }
        },
    )


class ProcessingConfig(BaseModel):
    """Модель конфигурации обработки данных."""

    transformations: list[dict[str, Any]] | None = None
    aggregations: list[dict[str, Any]] | None = None
    groupby: list[str] | None = None
    filters: list[dict[str, Any]] | None = None
    metrics: list[dict[str, Any]] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "transformations": [
                    {"type": "filter", "condition": {"year": {"$gte": 2020}}}
                ],
                "aggregations": [
                    {"type": "sum", "field": "revenue", "groupby": "category"},
                    {"type": "avg", "field": "sales", "groupby": "region"},
                ],
                "groupby": ["category", "region"],
                "filters": [{"field": "year", "operator": ">=", "value": 2020}],
                "metrics": [
                    {"name": "total_revenue", "type": "sum", "field": "revenue"},
                    {"name": "avg_sales", "type": "avg", "field": "sales"},
                ],
            }
        },
    )


class ProcessingResult(BaseModel):
    """Модель результата обработки данных."""

    success: bool
    task_id: UUID
    dashboard_id: int
    rows_processed: int
    message: str
    data: dict[str, Any] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "dashboard_id": 1,
                "rows_processed": 1000,
                "message": "Data processed successfully",
                "data": {"columns": ["category", "revenue"], "rows": 50},
            }
        },
    )


class AggregatedData(BaseModel):
    """Модель агрегированных данных для дашборда."""

    dashboard_id: int
    chart_type: GraphTypeEnum
    data: list[dict[str, Any]]
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": 1,
                "chart_type": "bar",
                "data": [
                    {"category": "A", "revenue": 1000},
                    {"category": "B", "revenue": 2000},
                ],
                "metadata": {"total": 3000, "count": 2},
            }
        },
    )
