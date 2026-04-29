"""Тесты для модуля зависимостей FastAPI (deps.py).

Тестирует зависимости аутентификации и авторизации,
включая проверку токенов, ролей и доступа к дашбордам.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from jose import ExpiredSignatureError
from sqlalchemy.orm import Session

from mko_bi.api.deps import (
    get_db,
    get_token_from_header,
    get_current_user_dependency,
    require_admin_role,
    require_editor_role,
    require_viewer_role,
    require_role_dependency,
    require_dashboard_read_access,
    require_dashboard_write_access,
    require_dashboard_admin_access,
    CurrentUser,
    AdminUser,
    EditorUser,
    ViewerUser,
)
from mko_bi.models.user import UserDB
from mko_bi.core.permissions import AuthenticationError


class TestGetDB:
    """Тесты зависимости get_db."""

    def test_get_db_yields_session(self):
        """get_db должна возвращать генератор сессии."""
        db_gen = get_db()
        # Проверяем, что это генератор
        assert hasattr(db_gen, '__iter__')
        assert hasattr(db_gen, '__next__')
        # Получаем сессию
        session = next(db_gen)
        assert isinstance(session, Session)
        # Закрываем генератор
        try:
            next(db_gen)
        except StopIteration:
            pass


class TestGetTokenFromHeader:
    """Тесты зависимости get_token_from_header."""

    def test_valid_bearer_token(self):
        """Валидный Bearer токен должен извлекаться корректно."""
        credentials = MagicMock()
        credentials.scheme = "Bearer"
        credentials.credentials = "valid_token"

        token = get_token_from_header(credentials)
        assert token == "valid_token"

    def test_invalid_scheme(self):
        """Некорректная схема аутентификации должна вызывать HTTPException."""
        credentials = MagicMock()
        credentials.scheme = "Basic"
        credentials.credentials = "token"

        with pytest.raises(HTTPException) as exc_info:
            get_token_from_header(credentials)

        assert exc_info.value.status_code == 401
        assert "Некорректная схема" in str(exc_info.value.detail)

    def test_lowercase_bearer(self):
        """Схема bearer в нижнем регистре должна работать."""
        credentials = MagicMock()
        credentials.scheme = "bearer"
        credentials.credentials = "token"

        token = get_token_from_header(credentials)
        assert token == "token"


class TestGetCurrentUserDependency:
    """Тесты зависимости get_current_user_dependency."""

    def test_valid_user(self, mocker):
        """Валидный токен должен возвращать пользователя."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.role = "viewer"

        mock_get_user = mocker.patch(
            "mko_bi.api.deps.get_current_user", return_value=mock_user
        )
        mock_db = MagicMock(spec=Session)

        result = get_current_user_dependency(
            token="valid_token",
            db=mock_db,
        )

        assert result == mock_user
        mock_get_user.assert_called_once_with("valid_token", mock_db)

    def test_expired_token(self, mocker):
        """Истекший токен должен вызывать HTTPException 401."""
        mocker.patch(
            "mko_bi.api.deps.get_current_user",
            side_effect=ExpiredSignatureError(),
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_dependency(
                token="expired_token",
                db=MagicMock(),
            )

        assert exc_info.value.status_code == 401
        assert "истек" in str(exc_info.value.detail).lower()

    def test_authentication_error(self, mocker):
        """Ошибка аутентификации должна вызывать HTTPException 401."""
        mocker.patch(
            "mko_bi.api.deps.get_current_user",
            side_effect=AuthenticationError("Invalid token"),
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_dependency(
                token="invalid_token",
                db=MagicMock(),
            )

        assert exc_info.value.status_code == 401

    def test_unexpected_error(self, mocker):
        """Непредвиденная ошибка должна вызывать HTTPException 500."""
        mocker.patch(
            "mko_bi.api.deps.get_current_user",
            side_effect=Exception("Unexpected error"),
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_dependency(
                token="token",
                db=MagicMock(),
            )

        assert exc_info.value.status_code == 500


class TestRequireAdminRole:
    """Тесты зависимости require_admin_role."""

    def test_admin_user_passes(self):
        """Пользователь admin должен проходить проверку."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        result = require_admin_role(user=mock_user)
        assert result == mock_user

    def test_editor_fails(self):
        """Пользователь editor не должен проходить проверку admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(user=mock_user)

        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail).lower()

    def test_viewer_fails(self):
        """Пользователь viewer не должен проходить проверку admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(user=mock_user)

        assert exc_info.value.status_code == 403


class TestRequireEditorRole:
    """Тесты зависимости require_editor_role."""

    def test_admin_passes(self):
        """Пользователь admin должен проходить проверку editor."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        result = require_editor_role(user=mock_user)
        assert result == mock_user

    def test_editor_passes(self):
        """Пользователь editor должен проходить проверку editor."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        result = require_editor_role(user=mock_user)
        assert result == mock_user

    def test_viewer_fails(self):
        """Пользователь viewer не должен проходить проверку editor."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        with pytest.raises(HTTPException) as exc_info:
            require_editor_role(user=mock_user)

        assert exc_info.value.status_code == 403


class TestRequireViewerRole:
    """Тесты зависимости require_viewer_role."""

    def test_admin_passes(self):
        """Пользователь admin должен проходить проверку viewer."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        result = require_viewer_role(user=mock_user)
        assert result == mock_user

    def test_editor_passes(self):
        """Пользователь editor должен проходить проверку viewer."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        result = require_viewer_role(user=mock_user)
        assert result == mock_user

    def test_viewer_passes(self):
        """Пользователь viewer должен проходить проверку viewer."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        result = require_viewer_role(user=mock_user)
        assert result == mock_user


class TestRequireRoleDependency:
    """Тесты универсальной зависимости require_role_dependency."""

    def test_admin_for_admin(self):
        """Пользователь admin должен проходить проверку admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        checker = require_role_dependency("admin")
        result = checker(user=mock_user)
        assert result == mock_user

    def test_editor_for_admin_fails(self):
        """Пользователь editor не должен проходить проверку admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        checker = require_role_dependency("admin")

        with pytest.raises(HTTPException) as exc_info:
            checker(user=mock_user)

        assert exc_info.value.status_code == 403

    def test_editor_for_editor(self):
        """Пользователь editor должен проходить проверку editor."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        checker = require_role_dependency("editor")
        result = checker(user=mock_user)
        assert result == mock_user

    def test_viewer_for_viewer(self):
        """Пользователь viewer должен проходить проверку viewer."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        checker = require_role_dependency("viewer")
        result = checker(user=mock_user)
        assert result == mock_user


class TestRequireDashboardAccess:
    """Тесты зависимостей доступа к дашбордам."""

    def test_read_access_granted(self, mocker):
        """Доступ на чтение должен быть предоставлен при наличии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        mock_check = mocker.patch(
            "mko_bi.api.deps.check_dashboard_access", return_value=True
        )
        mock_db = MagicMock(spec=Session)

        result = require_dashboard_read_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )

        assert result == mock_user
        mock_check.assert_called_once_with(
            user_id=1, dashboard_id=1, required_permission="view", db=mock_db
        )

    def test_read_access_denied(self, mocker):
        """Доступ на чтение должен быть отклонен при отсутствии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=False)
        mock_db = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            require_dashboard_read_access(dashboard_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        assert "прав" in str(exc_info.value.detail).lower()

    def test_write_access_granted(self, mocker):
        """Доступ на запись должен быть предоставлен при наличии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=True)
        mock_db = MagicMock(spec=Session)

        result = require_dashboard_write_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )

        assert result == mock_user

    def test_write_access_denied(self, mocker):
        """Доступ на запись должен быть отклонен при отсутствии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=False)
        mock_db = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            require_dashboard_write_access(dashboard_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403

    def test_admin_access_granted(self, mocker):
        """Доступ на администрирование должен быть предоставлен при наличии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=True)
        mock_db = MagicMock(spec=Session)

        result = require_dashboard_admin_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )

        assert result == mock_user

    def test_admin_access_denied(self, mocker):
        """Доступ на администрирование должен быть отклонен при отсутствии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=False)
        mock_db = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            require_dashboard_admin_access(dashboard_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_auth_flow(self, mocker):
        """Полный цикл аутентификации и авторизации."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.email = "admin@example.com"
        mock_user.role = "admin"

        # 1. Извлекаем токен
        credentials = MagicMock()
        credentials.scheme = "Bearer"
        credentials.credentials = "valid_token"
        token = get_token_from_header(credentials)
        assert token == "valid_token"

        # 2. Получаем пользователя
        mocker.patch("mko_bi.api.deps.get_current_user", return_value=mock_user)
        db = MagicMock(spec=Session)
        user = get_current_user_dependency(token=token, db=db)
        assert user == mock_user

        # 3. Проверяем роль admin
        result = require_admin_role(user=user)
        assert result == mock_user

        # 4. Проверяем доступ к дашборду
        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=True)
        result = require_dashboard_admin_access(dashboard_id=1, user=user, db=db)
        assert result == mock_user

    def test_editor_cannot_access_admin_endpoint(self, mocker):
        """Editor не должен иметь доступа к эндпоинтам admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 2
        mock_user.role = "editor"

        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(user=mock_user)

        assert exc_info.value.status_code == 403

    def test_viewer_can_only_read_dashboard(self, mocker):
        """Viewer должен иметь доступ только на чтение дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 3
        mock_user.role = "viewer"

        # Доступ на чтение - OK
        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=True)
        mock_db = MagicMock(spec=Session)
        result = require_dashboard_read_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user

        # Доступ на запись - отказ
        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=False)
        with pytest.raises(HTTPException) as exc_info:
            require_dashboard_write_access(dashboard_id=1, user=mock_user, db=mock_db)
        assert exc_info.value.status_code == 403

    def test_admin_has_full_dashboard_access(self, mocker):
        """Admin должен иметь полный доступ к дашборду."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"
        mock_db = MagicMock(spec=Session)

        # Все проверки доступа должны проходить
        mocker.patch("mko_bi.api.deps.check_dashboard_access", return_value=True)

        result = require_dashboard_read_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user

        result = require_dashboard_write_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user

        result = require_dashboard_admin_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user
