"""Перечисления для компонентов приложения.

Используется StrEnum для типобезопасности и удобства сериализации.
"""

from enum import StrEnum


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


class FilterType(StrEnum):
    """Типы фильтров."""

    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"


class GraphType(StrEnum):
    """Типы графиков."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"


class ComponentSize(StrEnum):
    """Размеры компонентов."""

    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"
