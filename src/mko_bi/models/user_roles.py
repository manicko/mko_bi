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
