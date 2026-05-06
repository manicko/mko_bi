"""Конкретные типы для замены Any.

Содержит TypedDict и Pydantic модели для типизации структур,
которые ранее использовали dict[str, Any] или Any.
"""

from typing import TypedDict

from pydantic import BaseModel, Field


# ==================== Aggregated Data Types ====================


class DimensionData(TypedDict, total=False):
    """Данные измерений для агрегированных записей."""

    year: int
    month: int
    category: str
    brand: str
    region: str
    # Дополнительные поля могут присутствовать
    # в зависимости от конфигурации дашборда


class MetricData(TypedDict, total=False):
    """Данные метрик для агрегированных записей."""

    value: float
    sum: float
    avg: float
    count: int
    min: float
    max: float
    # Дополнительные метрики


class AggregatedRecordModel(BaseModel):
    """Pydantic модель для записи агрегированных данных."""

    dims: dict[str, int | float | str] = Field(default_factory=dict)
    metrics: dict[str, int | float | str] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


# ==================== Filter Types ====================


class FilterCondition(TypedDict):
    """Условие фильтрации данных."""

    field: str
    operator: str  # ">=", "<=", "==", "!=", ">", "<"
    value: int | str | float


class ChartFilterConfig(TypedDict):
    """Конфигурация фильтра для графика."""

    year: int | None
    category: str | None
    brand: str | None
    region: str | None
    filters: dict[str, list[str | int]]  # Дополнительные фильтры


# ==================== Transformation Types ====================


class TransformationConfig(TypedDict):
    """Конфигурация трансформации данных."""

    type: str  # "filter", "map", "derive", etc.
    condition: dict[str, dict[str, int | float | str]]  # Например: {"year": {"$gte": 2020}}


class AggregationConfig(TypedDict):
    """Конфигурация агрегации."""

    type: str  # "sum", "avg", "count", "min", "max"
    field: str


class ProcessingConfigData(TypedDict):
    """Конфигурация обработки данных."""

    transformations: list[TransformationConfig] | None
    aggregations: list[AggregationConfig] | None
    groupby: list[str] | None
    filters: list[FilterCondition] | None
    metrics: list[dict[str, str]] | None  # {"name": "...", "type": "...", "field": "..."}


# ==================== Graph Config Types ====================


class AxisConfig(TypedDict, total=False):
    """Конфигурация оси графика."""

    title: str
    label: str
    range: list[float] | None
    type: str | None  # "linear", "log", "date", etc.


class ChartLayoutConfig(TypedDict, total=False):
    """Конфигурация макета графика."""

    title: str
    xaxis: AxisConfig | None
    yaxis: AxisConfig | None
    showlegend: bool
    height: int
    width: int
    template: str | None


class YoYConfig(TypedDict, total=False):
    """Настройки год-к-году сравнения."""

    enabled: bool
    metric: str
    mode: str  # "percent", "absolute"
    year_field: str


class GraphConfigDict(TypedDict, total=False):
    """Конфигурация графика (config поле)."""

    x: str | None
    y: str | None
    color: str | None
    xaxis: AxisConfig | None
    yaxis: AxisConfig | None
    title: str | None
    layout: ChartLayoutConfig | None
    yoy: YoYConfig | None
    secondary_y: list[str] | None


# ==================== Filter Config Types ====================


class FilterConfigDict(TypedDict, total=False):
    """Конфигурация фильтра (config поле)."""

    field: str  # Поле для фильтрации
    source: str  # "dims", "metrics", "custom"
    multi: bool  # Множественный выбор
    type: str | None  # Тип input ("select", "multiselect", "range", "date")
    options: list[str | int] | None  # Доступные опции
    default: str | int | list[str | int] | None


# ==================== Processing Settings Types ====================


class ProcessingSettingsDict(TypedDict, total=False):
    """Настройки обработки (settings поле)."""

    loader: str  # "sales_loader", etc.
    date_column: str | None
    timezone: str  # "UTC", "Europe/Moscow", etc.
    encoding: str | None  # "UTF-8", etc.
    separator: str | None  # "," for CSV


# ==================== Auth Token Types ====================


class TokenData(TypedDict):
    """Данные JWT токена."""

    user_id: str
    email: str
    role: str
    exp: int | None


class LoginResponse(TypedDict):
    """Ответ при успешном логине."""

    access_token: str
    token_type: str
    expires_in: int | None


# ==================== Metadata Types ====================


class ChartMetadata(TypedDict, total=False):
    """Метаданные графика."""

    graph_id: str
    graph_name: str
    count: int
    total: float | None


class ProcessingResultData(TypedDict, total=False):
    """Данные результата обработки."""

    columns: list[str]
    rows: int
    dashboard_id: int
    preview: list[dict[str, int | float | str]] | None


# ==================== Pydantic Models for Runtime Validation ====================


class DimensionModel(BaseModel):
    """Pydantic модель для измерений."""

    year: int | None = None
    month: int | None = None
    category: str | None = None
    brand: str | None = None
    region: str | None = None

    model_config = {"extra": "allow"}


class MetricModel(BaseModel):
    """Pydantic модель для метрик."""

    value: float | None = None
    sum: float | None = None
    avg: float | None = None
    count: int | None = None
    min: float | None = None
    max: float | None = None

    model_config = {"extra": "allow"}


class GraphConfigModel(BaseModel):
    """Pydantic модель для конфигурации графика."""

    x: str | None = None
    y: str | None = None
    color: str | None = None
    xaxis: AxisConfig | None = None
    yaxis: AxisConfig | None = None
    title: str | None = None
    layout: ChartLayoutConfig | None = None
    yoy: YoYConfig | None = None
    secondary_y: list[str] | None = None

    model_config = {"extra": "allow"}


class FilterConfigModel(BaseModel):
    """Pydantic модель для конфигурации фильтра."""

    field: str | None = None
    source: str | None = None
    multi: bool = False
    type: str | None = None
    options: list[str | int] | None = None
    default: str | int | list[str | int] | None = None

    model_config = {"extra": "allow"}


class ProcessingSettingsModel(BaseModel):
    """Pydantic модель для настроек обработки."""

    loader: str | None = None
    date_column: str | None = None
    timezone: str = "UTC"
    encoding: str | None = "UTF-8"
    separator: str | None = ","

    model_config = {"extra": "allow"}
