from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mkobi.models.enums import GraphType
from mkobi.models.types import GraphConfigDict


class GraphBase(BaseModel):
    """Базовая модель для графиков."""

    name: str
    type: GraphType
    dashboard_id: UUID
    config: GraphConfigDict
    dimensions: list[str]
    metrics: list[str]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Sales by Category",
                "type": "bar",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "config": {"xaxis": {"title": "Category"}, "yaxis": {"title": "Sales"}},
                "dimensions": ["category", "year"],
                "metrics": ["sales", "revenue"],
            }
        },
    )


class GraphCreate(GraphBase):
    """Модель для создания графика."""

    pass


class GraphUpdate(BaseModel):
    """Модель для обновления графика."""

    name: str | None = None
    type: GraphType | None = None
    config: GraphConfigDict | None = None
    dimensions: list[str] | None = None
    metrics: list[str] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Updated Sales by Category",
                "type": "line",
                "config": {"xaxis": {"title": "Category"}, "yaxis": {"title": "Revenue"}},
                "dimensions": ["category"],
                "metrics": ["revenue"],
            }
        },
    )


class GraphRead(GraphBase):
    """Модель для чтения данных графика."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sales by Category",
                "type": "bar",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "config": {"xaxis": {"title": "Category"}, "yaxis": {"title": "Sales"}},
                "dimensions": ["category", "year"],
                "metrics": ["sales", "revenue"],
                "created_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )
