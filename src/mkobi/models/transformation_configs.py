"""Pydantic модели для конфигурации трансформаций данных.

Этот модуль содержит модели для типизации настроек
фильтрации, агрегации, расчета YoY, долей и кастомных метрик.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from mkobi.models.user_roles import AggregationFunctionEnum, FilterOperatorEnum


class FilterConfig(BaseModel):
    """Конфигурация фильтрации данных."""

    column: str
    operator: FilterOperatorEnum
    value: Any

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "column": "year",
                "operator": ">=",
                "value": 2020,
            }
        },
    )


class AggregationConfig(BaseModel):
    """Конфигурация агрегации данных."""

    column: str
    function: AggregationFunctionEnum
    alias: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "column": "revenue",
                "function": "sum",
                "alias": "total_revenue",
            }
        },
    )


class YoyConfig(BaseModel):
    """Конфигурация расчета Year-over-Year."""

    year_column: str
    value_column: str
    group_cols: list[str] | None = Field(
        default=None,
        description="Колонки для группировки (измерения/dims)",
    )
    month_column: str | None = Field(
        default=None,
        description="Колонка с месяцем (для сдвига на 12 месяцев)",
    )
    alias: str = Field(default="yoy", description="Имя колонки с предыдущим значением")
    percent_alias: str = Field(
        default="yoy_percent",
        description="Имя колонки с процентным изменением",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "year_column": "year",
                "value_column": "revenue_sum",
                "group_cols": ["category", "region"],
                "month_column": "month",
                "alias": "prev_year_value",
                "percent_alias": "yoy_percent",
            }
        },
    )


class ShareConfig(BaseModel):
    """Конфигурация расчета долей."""

    value_column: str
    group_cols: list[str] | None = Field(
        default=None,
        description="Колонки для группировки при расчете долей",
    )
    alias: str = Field(default="share", description="Имя колонки с долей")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "value_column": "revenue",
                "group_cols": ["year", "month"],
                "alias": "share",
            }
        },
    )


class CustomMetricConfig(BaseModel):
    """Конфигурация кастомной метрики."""

    name: str
    formula: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "profit_margin",
                "formula": "profit / revenue * 100",
            }
        },
    )
