from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from typing import Literal
from uuid import UUID


class DashboardConfig(BaseModel):
    """Модель конфигурации дашборда."""

    graph_types: list[Literal["bar", "line", "pie", "table"]]
    filters: list[dict[str, Any]] | None = None
    aggregations: list[dict[str, Any]] | None = None
    charts: list[dict[str, Any]] | None = None
    title: str | None = None
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "graph_types": ["bar", "line"],
                "filters": [
                    {"field": "year", "type": "select"},
                    {"field": "category", "type": "multi_select"},
                ],
                "aggregations": [
                    {"type": "sum", "field": "revenue"},
                    {"type": "avg", "field": "sales"},
                ],
                "charts": [
                    {
                        "type": "bar",
                        "x": "category",
                        "y": "revenue",
                        "title": "Revenue by Category",
                    }
                ],
                "title": "Sales Dashboard",
                "description": "Overview of sales performance",
            }
        },
    )


class DashboardCreate(BaseModel):
    """Модель для создания нового дашборда."""

    name: str
    description: str | None = None
    config: DashboardConfig

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Sales Dashboard",
                "description": "Overview of sales performance",
                "config": {
                    "graph_types": ["bar", "line"],
                    "filters": [{"field": "year", "type": "select"}],
                    "charts": [
                        {
                            "type": "bar",
                            "x": "category",
                            "y": "revenue",
                        }
                    ],
                },
            }
        },
    )


class DashboardRead(BaseModel):
    """Модель для чтения данных дашборда."""

    id: UUID
    name: str
    description: str | None
    config: DashboardConfig
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sales Dashboard",
                "description": "Overview of sales performance",
                "config": {
                    "graph_types": ["bar", "line"],
                    "filters": [{"field": "year", "type": "select"}],
                },
                "created_at": "2026-04-24T16:02:46+03:00",
                "updated_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class DashboardUpdate(BaseModel):
    """Модель для обновления дашборда."""

    name: str | None = None
    description: str | None = None
    config: DashboardConfig | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Updated Sales Dashboard",
                "description": "Updated description",
                "config": {
                    "graph_types": ["bar", "line", "pie"],
                    "filters": [{"field": "year", "type": "select"}],
                },
            }
        },
    )
