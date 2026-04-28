from enum import StrEnum


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


class FilterTypeEnum(StrEnum):
    """Типы фильтров."""
    select = "select"
    multiselect = "multiselect"
    range = "range"
    date = "date"
