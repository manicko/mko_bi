"""Pydantic models for layouts.

Provides models for layout data validation
during creation, update and reading from API.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LayoutBase(BaseModel):
    """Base layout model."""

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
    """Model for creating a new layout."""

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
    """Model for updating a layout."""

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
    """Model for reading layout data."""

    id: UUID
    created_at: datetime
    updated_at: datetime

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
                "updated_at": "2026-05-04T18:00:00+03:00",
            }
        },
    )
