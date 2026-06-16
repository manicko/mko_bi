"""Concrete types to replace Any.

Contains TypedDict and Pydantic models for typing structures
that previously used dict[str, Any] or Any.
"""

from typing import Any, TypedDict

from pydantic import BaseModel, Field

from mkobi.models.enums import AggregationFunctionEnum, YoyModeEnum


# ==================== Aggregated Data Types ====================


class DimensionData(TypedDict, total=False):
    """Dimension data for aggregated records."""

    year: int
    month: int
    category: str
    brand: str
    region: str
    # Additional fields may be present
    # depending on dashboard configuration


class MetricData(TypedDict, total=False):
    """Metric data for aggregated records."""

    value: float
    sum: float
    avg: float
    count: int
    min: float
    max: float
    # Additional metrics


class AggregatedRecordModel(BaseModel):
    """Pydantic model for aggregated data record."""

    dims: dict[str, int | float | str] = Field(default_factory=dict)
    metrics: dict[str, int | float | str] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


# ==================== Filter Types ====================


class FilterCondition(TypedDict):
    """Data filter condition."""

    field: str
    operator: str  # ">=", "<=", "==", "!=", ">", "<"
    value: int | str | float


class ChartFilterConfig(TypedDict):
    """Filter configuration for chart."""

    year: int | None
    category: str | None
    brand: str | None
    region: str | None
    filters: dict[str, list[str | int]]  # Additional filters


# ==================== Transformation Types ====================


class TransformationConfig(TypedDict):
    """Data transformation configuration."""

    type: str  # "filter", "map", "derive", etc.
    condition: dict[str, dict[str, int | float | str]]  # Example: {"year": {"$gte": 2020}}


class AggregationConfig(TypedDict):
    """Aggregation configuration."""

    type: str  # "sum", "avg", "count", "min", "max"
    field: str


class ProcessingConfigData(TypedDict):
    """Data processing configuration."""

    transformations: list[TransformationConfig] | None
    aggregations: list[AggregationConfig] | None
    groupby: list[str] | None
    filters: list[FilterCondition] | None
    metrics: list[dict[str, str]] | None  # {"name": "...", "type": "...", "field": "..."}


# ==================== Graph Config Types ====================


class AxisConfig(TypedDict, total=False):
    """Chart axis configuration."""

    title: str
    label: str
    range: list[float] | None
    type: str | None  # "linear", "log", "date", etc.


class ChartLayoutConfig(TypedDict, total=False):
    """Chart layout configuration."""

    title: str
    xaxis: AxisConfig | None
    yaxis: AxisConfig | None
    showlegend: bool
    height: int
    width: int
    template: str | None


class YoYConfig(TypedDict, total=False):
    """Year-over-year comparison settings."""

    enabled: bool
    metric: str
    mode: YoyModeEnum  # YoyModeEnum.PERCENT or YoyModeEnum.ABSOLUTE
    year_field: str


class SortConfig(TypedDict, total=False):
    """Sorting configuration for chart axes."""

    by: str  # Dimension or metric column to sort by
    direction: str  # "asc" or "desc"


class GraphConfigDict(TypedDict, total=False):
    """Chart configuration (config field)."""

    x: str | None
    y: str | None
    color: str | None
    xaxis: AxisConfig | None
    yaxis: AxisConfig | None
    title: str | None
    layout: ChartLayoutConfig | None
    yoy: YoYConfig | None
    secondary_y: list[str] | None
    # Sorting configuration
    sort_x: SortConfig | None  # Sort x-axis values
    sort_color: SortConfig | None  # Sort color dimension values (by metric)


# ==================== Filter Config Types ====================


class FilterConfigDict(TypedDict, total=False):
    """Filter configuration (config field)."""

    field: str  # Field for filtering
    source: str  # "dims", "metrics", "custom"
    multi: bool  # Multiple selection
    type: str | None  # Input type ("select", "multiselect", "range", "date")
    options: list[str | int] | None  # Available options
    default: str | int | list[str | int] | None


# ==================== Processing Settings Types ====================


class ProcessingSettingsDict(TypedDict, total=False):
    """Processing settings (settings field)."""

    loader: str  # "sales_loader", etc.
    date_column: str | None
    timezone: str  # "UTC", "Europe/Moscow", etc.
    encoding: str | None  # "UTF-8", etc.
    separator: str | None  # "," for CSV
    renames: dict[str, str] | None  # column renaming map
    column_types: dict[str, str] | None  # column type casting
    date_format: str | None  # date format string
    decimal_separator: str | None  # "," for EU format
    computed_fields: list[dict[str, str]] | None  # computed column expressions
    filters: list[dict[str, Any]] | None  # row filters
    groupby: list[str] | None  # GROUP BY columns
    aggregations: list[dict[str, str]] | None  # aggregation config
    yoy_config: dict[str, Any] | None  # year-over-year config
    share_config: dict[str, Any] | None  # share calculation config
    custom_metrics: list[dict[str, Any]] | None  # custom metric formulas
    metric_agg: str | None  # Default aggregation function for metrics (sum, mean, min, max, count)


# ==================== Auth Token Types ====================


class TokenData(TypedDict):
    """JWT token data."""

    user_id: str
    email: str
    role: str
    exp: int | None


class LoginResponse(TypedDict):
    """Response on successful login."""

    access_token: str
    token_type: str
    expires_in: int | None


# ==================== Metadata Types ====================


class ChartMetadata(TypedDict, total=False):
    """Chart metadata."""

    graph_id: str
    graph_name: str
    count: int
    total: float | None


class ProcessingResultData(TypedDict, total=False):
    """Processing result data."""

    columns: list[str]
    rows: int
    dashboard_id: int
    preview: list[dict[str, int | float | str]] | None


# ==================== Pydantic Models for Runtime Validation ====================


class DimensionModel(BaseModel):
    """Pydantic model for dimensions."""

    year: int | None = None
    month: int | None = None
    category: str | None = None
    brand: str | None = None
    region: str | None = None

    model_config = {"extra": "allow"}


class MetricModel(BaseModel):
    """Pydantic model for metrics."""

    value: float | None = None
    sum: float | None = None
    avg: float | None = None
    count: int | None = None
    min: float | None = None
    max: float | None = None

    model_config = {"extra": "allow"}


class GraphConfigModel(BaseModel):
    """Pydantic model for chart configuration."""

    x: str | None = None
    y: str | None = None
    color: str | None = None
    xaxis: AxisConfig | None = None
    yaxis: AxisConfig | None = None
    title: str | None = None
    layout: ChartLayoutConfig | None = None
    yoy: YoYConfig | None = None
    secondary_y: list[str] | None = None
    # Sorting configuration
    sort_x: SortConfig | None = None
    sort_color: SortConfig | None = None

    model_config = {"extra": "allow"}


class FilterConfigModel(BaseModel):
    """Pydantic model for filter configuration."""

    field: str | None = None
    source: str | None = None
    multi: bool = False
    type: str | None = None
    options: list[str | int] | None = None
    default: str | int | list[str | int] | None = None

    model_config = {"extra": "allow"}


class ProcessingSettingsModel(BaseModel):
    """Pydantic model for processing settings."""

    loader: str | None = None
    date_column: str | None = None
    timezone: str = "UTC"
    encoding: str | None = "UTF-8"
    separator: str | None = ","
    metric_agg: AggregationFunctionEnum | None = None

    model_config = {"extra": "allow"}



