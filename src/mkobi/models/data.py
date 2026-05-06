from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID

from mkobi.models.enums import FileExtensionEnum, GraphType, BarmodeEnum, OrientationEnum, ProcessingStatus
from mkobi.models.transformation_configs import (
    AggregationConfig,
    CustomMetricConfig,
    FilterConfig,
    ShareConfig,
    YoyConfig,
)
from mkobi.models.types import (
    AggregatedRecordModel,
    ChartMetadata,
    ChartLayoutConfig,
    ProcessingResultData,
)


class DataUpload(BaseModel):
    """Модель для загрузки данных."""

    file: bytes
    filename: str
    dashboard_id: UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "filename": "data.csv.gz",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        },
    )


class UploadResponse(BaseModel):
    """Модель ответа при загрузке файла."""

    task_id: UUID
    filename: str
    dashboard_id: UUID
    status: ProcessingStatus
    message: str
    uploaded_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "data.csv.gz",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "uploaded",
                "message": "File uploaded successfully",
                "uploaded_at": "2026-04-24T16:02:46+03:00",
            }
        },
    )


class ProcessingStatusResponse(BaseModel):
    """Модель статуса обработки."""

    task_id: UUID
    filename: str
    dashboard_id: UUID
    status: ProcessingStatus
    progress: int = Field(0, ge=0, le=100)
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "data.csv.gz",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 50,
                "message": "Processing data...",
                "started_at": "2026-04-24T16:02:46+03:00",
                "completed_at": None,
            }
        },
    )


class ProcessingConfig(BaseModel):
    """Модель конфигурации обработки данных."""

    filters: list[FilterConfig] | None = None
    groupby: list[str] | None = None
    aggregations: list[AggregationConfig] | None = None
    sort_by: list[str] | None = None
    descending: bool = False
    limit: int | None = None
    yoy_config: YoyConfig | None = None
    share_config: ShareConfig | None = None
    custom_metrics: list[CustomMetricConfig] | None = None
    metrics: list[dict[str, str]] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "filters": [
                    {"column": "year", "operator": ">=", "value": 2020}
                ],
                "groupby": ["category", "region"],
                "aggregations": [
                    {"column": "revenue", "function": "sum", "alias": "total_revenue"}
                ],
                "sort_by": ["year"],
                "descending": False,
                "yoy_config": {
                    "year_column": "year",
                    "value_column": "revenue_sum",
                },
                "share_config": {
                    "value_column": "revenue_sum",
                },
                "custom_metrics": [
                    {"name": "profit", "formula": "revenue - cost"}
                ],
            }
        },
    )


class ProcessingResult(BaseModel):
    """Модель результата обработки данных."""

    success: bool
    task_id: UUID
    dashboard_id: UUID
    rows_processed: int
    message: str
    data: ProcessingResultData | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "rows_processed": 1000,
                "message": "Data processed successfully",
                "data": {"columns": ["category", "revenue"], "rows": 50},
            }
        },
    )


class AggregatedData(BaseModel):
    """Модель агрегированных данных для дашборда."""

    dashboard_id: UUID
    chart_type: GraphType
    data: list[AggregatedRecordModel]
    metadata: ChartMetadata | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "chart_type": "bar",
                "data": [
                    {"dims": {"category": "A"}, "metrics": {"revenue": 1000}},
                    {"dims": {"category": "B"}, "metrics": {"revenue": 2000}},
                ],
                "metadata": {"total": 3000, "count": 2},
            }
        },
    )


class DataFilter(BaseModel):
    """Модель фильтров для агрегированных данных.

    Используется для фильтрации данных по году, категории, бренду и другим параметрам.
    """

    dashboard_id: UUID
    filters: dict[str, Any] | None = None
    year: int | None = None
    category: str | None = None
    brand: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "year": 2023,
                "category": "Electronics",
                "brand": "Brand A",
                "filters": {
                    "region": "North",
                    "status": "active",
                },
            }
        },
    )


class ChartDataRequest(BaseModel):
    """Модель запроса данных для конкретных графиков.

    Используется для получения данных только для указанных графиков дашборда.
    """

    dashboard_id: UUID
    chart_ids: list[UUID] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
                "chart_ids": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                ],
            }
        },
    )


class LoaderConfig(BaseModel):
    """Конфигурация загрузчика CSV данных.

    Используется для настройки параметров загрузки и валидации данных.
    """

    required_columns: list[str] = Field(
        default_factory=list,
        description="Список обязательных колонок",
    )
    column_types: dict[str, str] = Field(
        default_factory=dict,
        description="Сопоставление колонок с ожидаемыми типами данных",
    )
    strict_schema: bool = Field(
        default=False,
        description="Проверять ли строгое соответствие схемы",
    )
    max_file_size: int = Field(
        default=100 * 1024 * 1024,
        description="Максимальный размер файла в байтах",
        ge=1,
        le=1024 * 1024 * 1024,  # 1GB max
    )
    allowed_file_types: list[FileExtensionEnum] = Field(
        default_factory=lambda: [FileExtensionEnum.CSV, FileExtensionEnum.CSV_GZ],
        description="Разрешенные типы файлов",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "required_columns": ["date", "category", "revenue"],
                "column_types": {
                    "date": "date",
                    "revenue": "float",
                    "category": "str",
                },
                "strict_schema": False,
                "max_file_size": 104857600,
                "allowed_file_types": [".csv", ".csv.gz"],
            }
        },
    )


class ValidationResult(BaseModel):
    """Результат валидации данных.

    Содержит информацию о том, прошли ли данные валидацию,
    а также список ошибок и предупреждений.
    """

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    columns: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Найдено 5 null-значений в колонке 'category'"],
                "row_count": 1000,
                "column_count": 5,
                "columns": ["date", "category", "revenue", "region", "brand"],
            }
        },
    )


class ChartData(BaseModel):
    """Модель данных для графика.

    Содержит список словарей с данными, где каждый словарь
    представляет одну точку данных с измерениями и метриками.
    """

    data: list[dict[str, int | float | str]]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "data": [
                    {"category": "A", "revenue": 1000, "year": 2023},
                    {"category": "B", "revenue": 2000, "year": 2023},
                ]
            }
        },
    )


class ChartConfig(BaseModel):
    """Модель конфигурации графика.

    Определяет параметры визуализации: оси, цвета, режимы отображения
    и дополнительные настройки макета.
    """

    x: str
    color: str | None = None
    metrics: list[str]
    orientation: OrientationEnum = OrientationEnum.VERTICAL
    barmode: BarmodeEnum = BarmodeEnum.GROUP
    secondary_y: list[str] = Field(default_factory=list)
    layout: ChartLayoutConfig | None = Field(default=None)
    yoy: YoyConfig | None = Field(
        default=None,
        description="Настройки год-к-году сравнения",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "x": "category",
                "color": "year",
                "metrics": ["revenue", "sales"],
                "orientation": "v",
                "barmode": "group",
                "secondary_y": ["profit"],
                "layout": {"title": "Sales by Category"},
                "yoy": {
                    "enabled": True,
                    "metric": "revenue",
                    "mode": "percent",
                    "year_field": "year",
                },
            }
        },
    )


class FilterState(BaseModel):
    """Модель состояния фильтров дашборда.

    Хранит текущие значения фильтров в виде словаря,
    где ключ - имя фильтра, значение - список выбранных значений.
    """

    filters: dict[str, list[int | str]] = Field(default_factory=dict)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "filters": {
                    "year": [2023, 2024],
                    "category": ["Electronics"],
                    "region": ["North", "South"],
                }
            }
        },
    )
