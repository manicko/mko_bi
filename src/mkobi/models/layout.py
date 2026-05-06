"""Pydantic модели для layout-ов.

Предоставляет модели для валидации данных layout-ов
при создании, обновлении и чтении из API.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LayoutBase(BaseModel):
    """Базовая модель layout-а."""

    name: str
    definition: dict[str, Any]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "default_layout",
                "definition": {
                    "grid": [
                        {"columns": [{"graph_id": "g1", "width": 12}]},
                        {"columns": [
                            {"graph_id": "g2", "width": 6},
                            {"graph_id": "g3", "width": 6},
                        ]},
                    ],
                    "graphs": [
                        {"id": "g1", "type": "bar", "title": "Revenue by Category"},
                        {"id": "g2", "type": "line", "title": "Revenue Trend"},
                        {"id": "g3", "type": "pie", "title": "Revenue Share"},
                    ],
                    "filters": ["year", "category"],
                    "bindings": [
                        {"filter": "year", "graphs": ["g1", "g2", "g3"]},
                    ],
                },
            }
        },
    )


class LayoutCreate(LayoutBase):
    """Модель для создания нового layout-а."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "sales_layout",
                "definition": {
                    "grid": [
                        {"columns": [{"graph_id": "g1", "width": 12}]},
                    ],
                },
            }
        },
    )


class LayoutUpdate(BaseModel):
    """Модель для обновления layout-а."""

    name: str | None = None
    definition: dict[str, Any] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "updated_sales_layout",
                "definition": {
                    "grid": [
                        {"columns": [{"graph_id": "g1", "width": 6}, {"graph_id": "g2", "width": 6}]},
                    ],
                },
            }
        },
    )


class LayoutRead(LayoutBase):
    """Модель для чтения данных layout-а."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "sales_layout",
                "definition": {
                    "grid": [
                        {"columns": [{"graph_id": "g1", "width": 12}]},
                    ],
                },
                "created_at": "2026-05-04T18:00:00+03:00",
            }
        },
    )
