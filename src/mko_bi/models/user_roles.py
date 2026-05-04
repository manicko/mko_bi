from enum import StrEnum

# mypy: ignore-errors


class UserRoleEnum(StrEnum):
    """Роли пользователей системы."""
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class PermissionEnum(StrEnum):
    """Уровни доступа к дашбордам."""
    view = "view"
    edit = "edit"
    admin = "admin"


class GraphTypeEnum(StrEnum):
    """Типы графиков для дашбордов."""
    bar = "bar"
    line = "line"
    pie = "pie"
    table = "table"


class OrientationEnum(StrEnum):
    """Ориентация графика."""
    vertical = "v"
    horizontal = "h"


class BarmodeEnum(StrEnum):
    """Режим отображения столбчатых диаграмм."""
    group = "group"
    stack = "stack"


class YoyModeEnum(StrEnum):
    """Режим отображения год-к-году сравнения."""
    absolute = "absolute"
    percent = "percent"


class AggregationFunctionEnum(StrEnum):
    """Функции агрегации данных."""
    sum_val = "sum"
    mean = "mean"
    count = "count"
    min_val = "min"
    max_val = "max"
    median = "median"
    std = "std"
    var = "var"
    first = "first"
    last = "last"


class FilterOperatorEnum(StrEnum):
    """Операторы для фильтрации данных."""
    EQ = "=="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="


class FilterTypeEnum(StrEnum):
    """Типы фильтров."""
    select = "select"
    multiselect = "multiselect"
    range = "range"
    date = "date"


class ProcessingStatusEnum(StrEnum):
    """Статусы обработки данных."""
    started = "started"
    uploaded = "uploaded"
    processing = "processing"
    success = "success"
    failed = "failed"
    completed = "completed"


class EnvironmentEnum(StrEnum):
    """Окружения приложения."""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class MimeTypeEnum(StrEnum):
    """Разрешенные MIME-типы для загружаемых файлов."""
    TEXT_CSV = "text/csv"
    APPLICATION_GZIP = "application/gzip"
    APPLICATION_X_GZIP = "application/x-gzip"

    @classmethod
    def allowed_values(cls) -> list[str]:
        """Возвращает список разрешенных MIME-типов."""
        return [member.value for member in cls]


class FileExtensionEnum(StrEnum):
    """Разрешенные расширения файлов."""
    CSV_GZ = ".csv.gz"
    CSV = ".csv"

    @classmethod
    def allowed_values(cls) -> list[str]:
        """Возвращает список разрешенных расширений."""
        return [member.value for member in cls]
