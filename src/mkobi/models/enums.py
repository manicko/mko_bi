"""Перечисления для компонентов приложения.

Используется StrEnum для типобезопасности и удобства сериализации.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей системы."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DashboardPermission(StrEnum):
    """Уровни доступа к дашбордам."""

    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class GraphType(StrEnum):
    """Типы графиков."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"


class FilterType(StrEnum):
    """Типы фильтров."""

    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"


class RegistrationStatus(StrEnum):
    """Статусы заявок на регистрацию."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UploadMode(StrEnum):
    """Режимы загрузки данных."""

    OVERWRITE = "overwrite"
    APPEND = "append"


class ProcessingStatus(StrEnum):
    """Статусы обработки данных."""

    STARTED = "started"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    COMPLETED = "completed"


# Alias for backwards compatibility
ProcessingStatusEnum = ProcessingStatus


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

    CSV = "csv"
    CSV_GZ = "csv.gz"

    @classmethod
    def allowed_values(cls) -> list[str]:
        """Возвращает список разрешенных расширений."""
        return [member.value for member in cls]


# Остальные enum-ы, используемые в дашбордах (Dash components)


class ButtonVariant(StrEnum):
    """Варианты стилей кнопок."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    LIGHT = "light"
    DARK = "dark"


class ComponentSize(StrEnum):
    """Размеры компонентов."""

    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"


class OrientationEnum(StrEnum):
    """Ориентация графика."""

    VERTICAL = "v"
    HORIZONTAL = "h"


class BarmodeEnum(StrEnum):
    """Режим отображения столбчатых диаграмм."""

    GROUP = "group"
    STACK = "stack"


class YoyModeEnum(StrEnum):
    """Режим отображения год-к-году сравнения."""

    ABSOLUTE = "absolute"
    PERCENT = "percent"


class AggregationFunctionEnum(StrEnum):
    """Функции агрегации данных."""

    SUM = "sum"
    MEAN = "mean"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"
    FIRST = "first"
    LAST = "last"


class FilterOperatorEnum(StrEnum):
    """Операторы для фильтрации данных."""

    EQ = "=="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
