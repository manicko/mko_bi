"""Pydantic models for data transformation configuration.

This module contains models for typing settings
for filtering, aggregation, YoY calculation, share calculation and custom metrics.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from mkobi.models.enums import AggregationFunctionEnum, FilterOperatorEnum


class FilterConfig(BaseModel):
    """Data filter configuration."""

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
    """Data aggregation configuration."""

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
    """Year-over-Year calculation configuration."""

    year_column: str
    value_column: str
    group_cols: list[str] | None = Field(
        default=None,
        description="Columns to group by (dimensions/dims)",
    )
    month_column: str | None = Field(
        default=None,
        description="Column containing month (for 12-month shift)",
    )
    alias: str = Field(default="yoy", description="Name of previous value column")
    percent_alias: str = Field(
        default="yoy_percent",
        description="Name of percentage change column",
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
    """Share calculation configuration."""

    value_column: str
    group_cols: list[str] | None = Field(
        default=None,
        description="Columns to group by when calculating shares",
    )
    alias: str = Field(default="share", description="Name of share column")

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
    """Custom metric configuration."""

    name: str
    expr: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "profit_margin",
                "expr": "profit / revenue * 100",
            }
        },
    )


class TransformationConfig(BaseModel):
    """Full transformation configuration."""

    filters: list[FilterConfig] | None = None
    computed_fields: list[CustomMetricConfig] | None = None
    rename: dict[str, str] | None = None
    dtype: dict[str, str] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "filters": [{"column": "year", "operator": ">=", "value": 2020}],
                "computed_fields": [{"name": "profit_margin", "formula": "profit / revenue * 100"}],
                "rename": {"revenue": "total_revenue"},
                "dtype": {"year": "INTEGER", "revenue": "FLOAT"},
            }
        },
    )
