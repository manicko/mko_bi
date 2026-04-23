from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Literal


class ChartConfig(BaseModel):
    type: Literal["bar", "line", "pie", "table"]
    x: str
    y: str | List[str]

    class Config:
        from_attributes = True


class DashboardConfig(BaseModel):
    charts: List[ChartConfig]
    filters: List[str]

    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    name: str
    config: Dict[str, Any]

    class Config:
        from_attributes = True


class DashboardRead(BaseModel):
    id: int
    name: str
    config: Dict[str, Any]

    class Config:
        from_attributes = True
