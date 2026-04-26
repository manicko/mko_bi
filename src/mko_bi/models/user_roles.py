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
