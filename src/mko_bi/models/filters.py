from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mko_bi.models.user_roles import FilterTypeEnum
from mko_bi.models.types import FilterConfigDict


class FilterBase(BaseModel):
    """Базовая модель для фильтров."""

    name: str
    type: FilterTypeEnum
    config: FilterConfigDict

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Year Filter",
                "type": "select",
                "config": {"field": "year", "source": "dims", "multi": False},
            }
        },
    )


class FilterCreate(FilterBase):
    """Модель для создания фильтра."""

    pass


class FilterUpdate(BaseModel):
    """Модель для обновления фильтра."""

    name: str | None = None
    type: FilterTypeEnum | None = None
    config: FilterConfigDict | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Updated Year Filter",
                "type": "multiselect",
                "config": {"field": "year", "source": "dims", "multi": True},
            }
        },
    )


class FilterRead(FilterBase):
    """Модель для чтения данных фильтра."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Year Filter",
                "type": "select",
                "config": {"field": "year", "source": "dims", "multi": False},
                "created_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )
