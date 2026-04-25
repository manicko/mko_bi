"""Тесты для модуля управления доступом (permissions.py).

Тестирует функции проверки прав доступа, иерархию ролей,
проверку доступа к дашбордам и обработку ошибок.
"""

import pytest
from unittest.mock import MagicMock, patch
from jose import JWTError
from sqlalchemy.orm import Session

from mko_bi.core.permissions import (
    check_role,
    check_dashboard_access,
    get_current_user,
    require_role,
    RoleHierarchy,
    ROLE_LEVELS,
    PERMISSION_LEVELS,
    AuthenticationError,
    PermissionError,
)
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.models.user import UserDB
from mko_bi.db.models import user as user_model


class TestRoleHierarchy:
    """Тесты иерархии ролей."""

    def test_role_levels_values(self):
        """Проверка значений уровней ролей."""
        assert ROLE_LEVELS["viewer"] == 1
        assert ROLE_LEVELS["editor"] == 2
        assert ROLE_LEVELS["admin"] == 3

    def test_role_hierarchy_enum(self):
        """Проверка значений перечисления RoleHierarchy."""
        assert RoleHierarchy.VIEWER.value == 1
        assert RoleHierarchy.EDITOR.value == 2
        assert RoleHierarchy.ADMIN.value == 3

    def test_permission_levels(self):
        """Проверка допустимых уровней доступа."""
        assert "view" in PERMISSION_LEVELS
        assert "edit" in PERMISSION_LEVELS
        assert "admin" in PERMISSION_LEVELS
        assert len(PERMISSION_LEVELS) == 3


class TestCheckRole:
    """Тесты функции check_role."""

    def test_admin_has_all_roles(self):
        """Admin должен иметь все права."""
        assert check_role("admin", "viewer") is True
        assert check_role("admin", "editor") is True
        assert check_role("admin", "admin") is True

    def test_editor_has_read_and_write(self):
        """Editor должен иметь права viewer и editor."""
        assert check_role("editor", "viewer") is True
        assert check_role("editor", "editor") is True
        assert check_role("editor", "admin") is False

    def test_viewer_has_only_read(self):
        """Viewer должен иметь только права viewer."""
        assert check_role("viewer", "viewer") is True
        assert check_role("viewer", "editor") is False
        assert check_role("viewer", "admin") is False

    def test_same_role(self):
        """Равные роли должны проходить проверку."""
        assert check_role("viewer", "viewer") is True
        assert check_role("editor", "editor") is True
        assert check_role("admin", "admin") is True

    def test_invalid_user_role(self):
        """Неверная роль пользователя должна возвращать False."""
        assert check_role("invalid", "viewer") is False

    def test_invalid_required_role(self):
        """Неверная требуемая роль должна возвращать False."""
        assert check_role("viewer", "invalid") is False

    def test_both_invalid_roles(self):
        """Обе неверные роли должны возвращать False."""
        assert check_role("invalid1", "invalid2") is False

    def test_case_sensitive_roles(self):
        """Роли должны быть чувствительны к регистру."""
        assert check_role("Admin", "viewer") is False
        assert check_role("EDITOR", "viewer") is False
        assert check_role("Viewer", "viewer") is False


class TestCheckDashboardAccess:
    """Тесты функции check_dashboard_access."""

    def test_has_read_access(self, mocker):
        """Пользователь с правом view должен иметь доступ на чтение."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", return_value="view"
        )

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="view", db=mock_db
        )

        assert result is True
        mock_check.assert_called_once_with(user_id=1, dashboard_id=1, db=mock_db)

    def test_has_write_access(self, mocker):
        """Пользователь с правом edit должен иметь доступ на чтение и запись."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", return_value="edit"
        )

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="view", db=mock_db
        )
        assert result is True

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="edit", db=mock_db
        )
        assert result is True

        mock_check.assert_called()

    def test_has_admin_access(self, mocker):
        """Пользователь с правом admin должен иметь все права."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", return_value="admin"
        )

        for permission in ["view", "edit", "admin"]:
            result = check_dashboard_access(
                user_id=1, dashboard_id=1, required_permission=permission, db=mock_db
            )
            assert result is True

        mock_check.assert_called()

    def test_no_access(self, mocker):
        """Пользователь без доступа должен получать False."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", return_value=None
        )

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="view", db=mock_db
        )

        assert result is False
        mock_check.assert_called_once()

    def test_insufficient_permission(self, mocker):
        """Пользователь с view не должен иметь доступ на запись."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", return_value="view"
        )

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="edit", db=mock_db
        )

        assert result is False
        mock_check.assert_called_once()

    def test_invalid_permission_level(self, mocker):
        """Неверный уровень доступа должен вызывать ValueError."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(AccessRepository, "check_access")

        with pytest.raises(ValueError, match="Неизвестный уровень доступа"):
            check_dashboard_access(
                user_id=1,
                dashboard_id=1,
                required_permission="invalid",
                db=mock_db,
            )

        mock_check.assert_not_called()

    def test_database_error(self, mocker):
        """Ошибка базы данных должна возвращать False."""
        mock_db = MagicMock()
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", side_effect=Exception("DB error")
        )

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="read", db=mock_db
        )

        assert result is False
        mock_check.assert_called_once()

    def test_creates_session_if_none(self, mocker):
        """Функция должна создавать сессию, если она не передана."""
        mock_session = MagicMock()
        mocker.patch("mko_bi.core.permissions.SessionLocal", return_value=mock_session)
        mock_check = mocker.patch.object(
            AccessRepository, "check_access", return_value="read"
        )

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="read", db=None
        )

        assert result is True
        mock_session.close.assert_called_once()
        mock_check.assert_called_once()

    def test_closes_session_if_created(self, mocker):
        """Функция должна закрывать созданную сессию."""
        mock_session = MagicMock()
        mocker.patch("mko_bi.core.permissions.SessionLocal", return_value=mock_session)
        mocker.patch.object(AccessRepository, "check_access", return_value="read")

        result = check_dashboard_access(
            user_id=1, dashboard_id=1, required_permission="read", db=None
        )

        assert result is True
        mock_session.close.assert_called_once()


class TestGetCurrentUser:
    """Тесты функции get_current_user."""

    def test_valid_token(self, mocker):
        """Валидный токен должен возвращать пользователя."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.role = "viewer"
        mock_db = MagicMock()

        mock_decode = mocker.patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={"user_id": 1},
        )
        mock_get = mocker.patch.object(UserRepository, "get", return_value=mock_user)

        result = get_current_user("valid_token", db=mock_db)

        assert result == mock_user
        mock_decode.assert_called_once_with("valid_token")
        mock_get.assert_called_once_with(1, mock_db)

    def test_token_without_user_id(self, mocker):
        """Токен без user_id должен вызывать AuthenticationError."""
        mock_db = MagicMock()
        mocker.patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={},
        )

        with pytest.raises(AuthenticationError, match="Некорректный токен"):
            get_current_user("invalid_token", db=mock_db)

    def test_invalid_token(self, mocker):
        """Недействительный токен должен вызывать AuthenticationError."""
        mock_db = MagicMock()
        mocker.patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value=None,
        )

        with pytest.raises(AuthenticationError, match="Недействительный токен"):
            get_current_user("invalid_token", db=mock_db)

    def test_user_not_found(self, mocker):
        """Отсутствие пользователя должно вызывать AuthenticationError."""
        mock_db = MagicMock()
        mocker.patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={"user_id": 999},
        )
        mocker.patch.object(UserRepository, "get", return_value=None)

        with pytest.raises(AuthenticationError, match="Пользователь не найден"):
            get_current_user("valid_token", db=mock_db)

    def test_jwt_error(self, mocker):
        """Ошибка JWT должна вызывать AuthenticationError."""
        mock_db = MagicMock()
        mocker.patch(
            "mko_bi.core.permissions._decode_token_cached",
            side_effect=JWTError("JWT error"),
        )

        with pytest.raises(AuthenticationError, match="Ошибка декодирования токена"):
            get_current_user("invalid_token", db=mock_db)

    def test_creates_session_if_none(self, mocker):
        """Функция должна создавать сессию, если она не передана."""
        mock_session = MagicMock()
        mock_user = MagicMock(spec=UserDB)

        mocker.patch("mko_bi.core.permissions.SessionLocal", return_value=mock_session)
        mocker.patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={"user_id": 1},
        )
        mocker.patch.object(UserRepository, "get", return_value=mock_user)

        result = get_current_user("valid_token", db=None)

        assert result == mock_user
        mock_session.close.assert_called_once()


class TestRequireRole:
    """Тесты функции require_role (зависимости FastAPI)."""

    def test_admin_user_passes_admin_check(self):
        """Пользователь admin должен проходить проверку admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        checker = require_role("admin")
        result = checker(user=mock_user)

        assert result == mock_user

    def test_editor_fails_admin_check(self):
        """Пользователь editor не должен проходить проверку admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        checker = require_role("admin")

        with pytest.raises(Exception) as exc_info:
            checker(user=mock_user)

        assert exc_info.value.status_code == 403

    def test_editor_passes_editor_check(self):
        """Пользователь editor должен проходить проверку editor."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        checker = require_role("editor")
        result = checker(user=mock_user)

        assert result == mock_user

    def test_viewer_passes_viewer_check(self):
        """Пользователь viewer должен проходить проверку viewer."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        checker = require_role("viewer")
        result = checker(user=mock_user)

        assert result == mock_user


class TestIntegration:
    """Интеграционные тесты."""


