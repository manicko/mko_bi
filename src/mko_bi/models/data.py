from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from typing import Literal


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


class ProcessingConfig(BaseModel):
    """Модель конфигурации обработки данных."""

    transformations: Optional[List[Dict[str, Any]]] = None
    aggregations: Optional[List[Dict[str, Any]]] = None
    groupby: Optional[List[str]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[List[Dict[str, Any]]] = None

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
    dashboard_id: int
    rows_processed: int
    message: str
    data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
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
    chart_type: Literal["bar", "line", "pie", "table"]
    data: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

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
