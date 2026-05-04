"""Тесты для модуля управления доступом (permissions.py).

Тестирует функции проверки прав доступа, иерархию ролей,
проверку доступа к дашбордам и обработку ошибок.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from jose import JWTError

from mko_bi.core.permissions import (
    check_role,
    check_dashboard_access,
    get_current_user,
    require_role,
    ROLE_LEVELS,
    PERMISSION_LEVELS,
    AuthenticationError,
)
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.models.user import UserDB

from mko_bi.models.user_roles import UserRoleEnum


class TestRoleHierarchy:
    """Тесты иерархии ролей."""

    def test_role_levels_values(self):
        """Проверка значений уровней ролей."""
        assert ROLE_LEVELS[UserRoleEnum.viewer] == 1
        assert ROLE_LEVELS[UserRoleEnum.editor] == 2
        assert ROLE_LEVELS[UserRoleEnum.admin] == 3

    def test_permission_levels(self):
        """Проверка значений PERMISSION_LEVELS."""
        assert "view" in PERMISSION_LEVELS
        assert "edit" in PERMISSION_LEVELS
        assert "admin" in PERMISSION_LEVELS
        assert "read" in PERMISSION_LEVELS
        assert len(PERMISSION_LEVELS) == 4


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

    @pytest.mark.asyncio
    async def test_has_read_access(self):
        """Пользователь с правом view должен иметь доступ на чтение."""
        mock_db = AsyncMock()
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = "view"

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="view", db=mock_db
            )

            assert result is True
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_has_write_access(self):
        """Пользователь с правом edit должен иметь доступ на чтение и запись."""
        mock_db = AsyncMock()
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = "edit"

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="view", db=mock_db
            )
            assert result is True

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="edit", db=mock_db
            )
            assert result is True

            assert mock_check.call_count >= 2

    @pytest.mark.asyncio
    async def test_has_admin_access(self):
        """Пользователь с правом admin должен иметь все права."""
        mock_db = AsyncMock()
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = "admin"

            for permission in ["view", "edit", "admin"]:
                result = await check_dashboard_access(
                    user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission=permission, db=mock_db
                )
                assert result is True

            assert mock_check.call_count >= 3

    @pytest.mark.asyncio
    async def test_no_access(self):
        """Пользователь без доступа должен получать False."""
        mock_db = AsyncMock()
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = None

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="view", db=mock_db
            )

            assert result is False
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_insufficient_permission(self):
        """Пользователь с view не должен иметь доступ на запись."""
        mock_db = AsyncMock()
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = "view"

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="edit", db=mock_db
            )

            assert result is False
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_permission_level(self):
        """Неверный уровень доступа должен вызывать ValueError."""
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access") as mock_check:
            with pytest.raises(ValueError, match="Допустимые значения"):
                await check_dashboard_access(
                    user_id=test_user_id,
                    dashboard_id=test_dashboard_id,
                    required_permission="invalid",
                    db=AsyncMock(),
                )

            mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error(self):
        """Ошибка базы данных должна возвращать False."""
        mock_db = AsyncMock()
        test_user_id = uuid4()
        test_dashboard_id = uuid4()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check:
            mock_check.side_effect = Exception("DB error")

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="view", db=mock_db
            )

            assert result is False
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_session_if_none(self):
        """Функция должна создавать сессию, если она не передана."""
        test_user_id = uuid4()
        test_dashboard_id = uuid4()
        mock_session = AsyncMock()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check, \
             patch("mko_bi.core.permissions.get_session") as mock_get_session:
            mock_check.return_value = "view"
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="view", db=None
            )

            assert result is True
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_session_if_created(self):
        """Сессия должна закрываться, если она была создана функцией."""
        test_user_id = uuid4()
        test_dashboard_id = uuid4()
        mock_session = AsyncMock()

        with patch.object(AccessRepository, "check_access", new_callable=AsyncMock) as mock_check, \
             patch("mko_bi.core.permissions.get_session") as mock_get_session:
            mock_check.return_value = "view"
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await check_dashboard_access(
                user_id=test_user_id, dashboard_id=test_dashboard_id, required_permission="view", db=None
            )

            assert result is True


class TestGetCurrentUser:
    """Тесты функции get_current_user."""

    @pytest.mark.asyncio
    async def test_valid_token(self):
        """Валидный токен должен возвращать пользователя."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_user.email = "test@example.com"
        mock_user.role = "viewer"
        mock_db = AsyncMock()

        with patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={"user_id": "550e8400-e29b-41d4-a716-446655440000"},
        ), patch.object(UserRepository, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_user

            result = await get_current_user("valid_token", db=mock_db)

            assert result == mock_user
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_without_user_id(self):
        """Токен без user_id должен вызывать AuthenticationError."""
        mock_db = AsyncMock()
        with patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={},
        ):
            with pytest.raises(AuthenticationError, match="Некорректный токен"):
                await get_current_user("invalid_token", db=mock_db)

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Недействительный токен должен вызывать AuthenticationError."""
        mock_db = AsyncMock()
        with patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value=None,
        ):
            with pytest.raises(AuthenticationError, match="Недействительный токен"):
                await get_current_user("invalid_token", db=mock_db)

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """Отсутствие пользователя должно вызывать AuthenticationError."""
        mock_db = AsyncMock()
        with patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={"user_id": "550e8400-e29b-41d4-a716-446655440999"},
        ), patch.object(UserRepository, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(AuthenticationError, match="Пользователь не найден"):
                await get_current_user("valid_token", db=mock_db)

    @pytest.mark.asyncio
    async def test_jwt_error(self):
        """Ошибка JWT должна вызывать AuthenticationError."""
        mock_db = AsyncMock()
        with patch(
            "mko_bi.core.permissions._decode_token_cached",
            side_effect=JWTError("JWT error"),
        ):
            with pytest.raises(AuthenticationError, match="Ошибка декодирования токена"):
                await get_current_user("invalid_token", db=mock_db)

    @pytest.mark.asyncio
    async def test_creates_session_if_none(self):
        """Функция должна создавать сессию, если она не передана."""
        mock_session = AsyncMock()
        mock_user = MagicMock(spec=UserDB)

        with patch("mko_bi.core.permissions.get_session") as mock_get_session, \
             patch(
            "mko_bi.core.permissions._decode_token_cached",
            return_value={"user_id": "550e8400-e29b-41d4-a716-446655440000"},
        ), patch.object(UserRepository, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_user
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_current_user("valid_token", db=None)

            assert result == mock_user



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


