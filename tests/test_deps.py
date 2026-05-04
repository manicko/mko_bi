"""Тесты для модуля зависимостей FastAPI (deps.py).

Тестирует зависимости аутентификации и авторизации,
включая проверку токенов, ролей и доступа к дашбордам.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from jose import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.api.deps import (
    get_db_dependency,
    get_token_from_header,
    get_current_user_dependency,
    require_admin_role,
    require_editor_role,
    require_viewer_role,
    require_role_dependency,
    require_dashboard_read_access,
    require_dashboard_write_access,
    require_dashboard_admin_access,
)
from mko_bi.models.user import UserDB
from mko_bi.core.permissions import AuthenticationError


class TestGetDB:
    """Тесты зависимости get_db_dependency."""

    def test_get_db_yields_session(self):
        """get_db_dependency должна возвращать асинхронный генератор."""
        import inspect
        # Просто проверяем, что это асинхронный генератор
        assert inspect.isasyncgenfunction(get_db_dependency)


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

    @pytest.mark.asyncio
    async def test_valid_user(self, mocker):
        """Валидный токен должен возвращать пользователя."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.role = "viewer"

        mock_get_user = mocker.patch(
            "mko_bi.api.deps.get_current_user", return_value=mock_user
        )
        mock_db = AsyncMock(spec=AsyncSession)

        result = await get_current_user_dependency(
            token="valid_token",
            db=mock_db,
        )

        assert result == mock_user
        mock_get_user.assert_called_once_with("valid_token", mock_db)

    @pytest.mark.asyncio
    async def test_expired_token(self, mocker):
        """Истекший токен должен вызывать HTTPException 401."""
        mocker.patch(
            "mko_bi.api.deps.get_current_user",
            side_effect=ExpiredSignatureError(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_dependency(
                token="expired_token",
                db=AsyncMock(spec=AsyncSession),
            )

        assert exc_info.value.status_code == 401
        assert "истёк" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_authentication_error(self, mocker):
        """Ошибка аутентификации должна вызывать HTTPException 401."""
        mocker.patch(
            "mko_bi.api.deps.get_current_user",
            side_effect=AuthenticationError("Invalid token"),
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_dependency(
                token="invalid_token",
                db=AsyncMock(spec=AsyncSession),
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_unexpected_error(self, mocker):
        """Непредвиденная ошибка должна вызывать HTTPException 500."""
        mocker.patch(
            "mko_bi.api.deps.get_current_user",
            side_effect=Exception("Unexpected error"),
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_dependency(
                token="token",
                db=AsyncMock(spec=AsyncSession),
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

    @pytest.mark.asyncio
    async def test_read_access_granted(self, mocker):
        """Доступ на чтение должен быть предоставлен при наличии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        async def mock_check(*args, **kwargs):
            return True
        
        mocker.patch("mko_bi.api.deps.check_dashboard_access", side_effect=mock_check)
        mock_db = AsyncMock(spec=AsyncSession)

        result = await require_dashboard_read_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_read_access_denied(self, mocker):
        """Доступ на чтение должен быть отклонен при отсутствии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        async def mock_check(*args, **kwargs):
            return False
        
        mocker.patch("mko_bi.api.deps.check_dashboard_access", side_effect=mock_check)
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await require_dashboard_read_access(dashboard_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        assert "прав" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_write_access_granted(self, mocker):
        """Доступ на запись должен быть предоставлен при наличии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        async def mock_check(*args, **kwargs):
            return True
        
        mocker.patch("mko_bi.api.deps.check_dashboard_access", side_effect=mock_check)
        mock_db = AsyncMock(spec=AsyncSession)

        result = await require_dashboard_write_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_write_access_denied(self, mocker):
        """Доступ на запись должен быть отклонен при отсутствии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "viewer"

        async def mock_check(*args, **kwargs):
            return False
        
        mocker.patch("mko_bi.api.deps.check_dashboard_access", side_effect=mock_check)
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await require_dashboard_write_access(dashboard_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_access_granted(self, mocker):
        """Доступ на администрирование должен быть предоставлен при наличии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"

        async def mock_check(*args, **kwargs):
            return True
        
        mocker.patch("mko_bi.api.deps.check_dashboard_access", side_effect=mock_check)
        mock_db = AsyncMock(spec=AsyncSession)

        result = await require_dashboard_admin_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_admin_access_denied(self, mocker):
        """Доступ на администрирование должен быть отклонен при отсутствии прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "editor"

        async def mock_check(*args, **kwargs):
            return False
        
        mocker.patch("mko_bi.api.deps.check_dashboard_access", side_effect=mock_check)
        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await require_dashboard_admin_access(dashboard_id=1, user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self, mocker):
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
        db = AsyncMock(spec=AsyncSession)
        user = await get_current_user_dependency(token=token, db=db)
        assert user == mock_user

        # 3. Проверяем роль admin
        result = require_admin_role(user=user)
        assert result == mock_user

        # 4. Проверяем доступ к дашборду
        mock_check = mocker.patch("mko_bi.api.deps.check_dashboard_access", new_callable=AsyncMock)
        mock_check.return_value = True
        result = await require_dashboard_admin_access(dashboard_id=1, user=user, db=db)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_editor_cannot_access_admin_endpoint(self, mocker):
        """Editor не должен иметь доступа к эндпоинтам admin."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 2
        mock_user.role = "editor"

        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(user=mock_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_can_only_read_dashboard(self, mocker):
        """Viewer должен иметь доступ только на чтение дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 3
        mock_user.role = "viewer"

        # Доступ на чтение - OK
        mock_check = mocker.patch("mko_bi.api.deps.check_dashboard_access", new_callable=AsyncMock)
        mock_check.return_value = True
        mock_db = AsyncMock(spec=AsyncSession)
        result = await require_dashboard_read_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user

        # Доступ на запись - отказ
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await require_dashboard_write_access(dashboard_id=1, user=mock_user, db=mock_db)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_has_full_dashboard_access(self, mocker):
        """Admin должен иметь полный доступ к дашборду."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.role = "admin"
        mock_db = AsyncMock(spec=AsyncSession)

        # Все проверки доступа должны проходить
        mock_check = mocker.patch("mko_bi.api.deps.check_dashboard_access", new_callable=AsyncMock)
        mock_check.return_value = True

        result = await require_dashboard_read_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user

        result = await require_dashboard_write_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user

        result = await require_dashboard_admin_access(
            dashboard_id=1, user=mock_user, db=mock_db
        )
        assert result == mock_user
