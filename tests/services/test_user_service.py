"""Тесты для сервиса управления пользователями (user_service.py).

Тестирует бизнес-логику CRUD операций с пользователями
с использованием моков для изоляции тестов.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.services.user_service import (
    UserService,
    _validate_role,
    _validate_user_exists,
    _check_admin_deletion_allowed,
)
from mko_bi.db.models import user as user_model
from mko_bi.models.user_roles import UserRoleEnum


class TestValidateRole:
    """Тесты для функции валидации роли."""

    def test_valid_role_admin(self):
        """Валидная роль admin должна проходить проверку."""
        _validate_role("admin")

    def test_valid_role_editor(self):
        """Валидная роль editor должна проходить проверку."""
        _validate_role("editor")

    def test_valid_role_viewer(self):
        """Валидная роль viewer должна проходить проверку."""
        _validate_role("viewer")

    def test_invalid_role_raises_value_error(self):
        """Недопустимая роль должна вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role("invalid_role")

    def test_empty_role_raises_value_error(self):
        """Пустая роль должна вызывать ValueError."""
        with pytest.raises(ValueError):
            _validate_role("")


class TestValidateUserExists:
    """Тесты для функции проверки существования пользователя."""

    @pytest.mark.asyncio
    async def test_user_exists(self):
        """Существующий пользователь должен возвращаться."""
        mock_user = MagicMock(spec=user_model.User)
        test_uuid = uuid4()
        mock_session = AsyncMock()

        with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get.return_value = mock_user
            result = await _validate_user_exists(test_uuid, mock_session)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_user_not_exists(self):
        """Несуществующий пользователь должен возвращать None."""
        test_uuid = uuid4()
        mock_session = AsyncMock()

        with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get.return_value = None
            result = await _validate_user_exists(test_uuid, mock_session)
            assert result is None


class TestCheckAdminDeletionAllowed:
    """Тесты для функции проверки разрешения на удаление администратора."""

    @pytest.mark.asyncio
    async def test_delete_admin_with_only_admin(self):
        """Удаление админа, если он единственный, должно быть разрешено."""
        mock_users = [MagicMock(spec=user_model.User, role="admin")]
        mock_session = AsyncMock()

        with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get_all.return_value = mock_users
            await _check_admin_deletion_allowed(mock_session)  # Не должно вызывать ошибку

    @pytest.mark.asyncio
    async def test_delete_admin_with_multiple_admins(self):
        """Удаление админа при наличии других админов должно быть разрешено."""
        mock_users = [
            MagicMock(spec=user_model.User, role="admin"),
            MagicMock(spec=user_model.User, role="admin"),
            MagicMock(spec=user_model.User, role="viewer"),
        ]
        mock_session = AsyncMock(spec=AsyncSession)
        with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get_all.return_value = mock_users
            await _check_admin_deletion_allowed(mock_session)  # Не должно вызывать ошибку


class TestUserServiceCreateUser:
    """Тесты для метода create_user сервиса UserService."""

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Успешное создание пользователя."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "newuser@example.com"
        mock_user.role = UserRoleEnum.viewer
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password') as mock_hash:

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.get_by_email.return_value = None
            mock_repo.create.return_value = mock_user

            service = UserService()
            with patch('mko_bi.services.user_service.get_session') as mock_get_session:
                mock_session = AsyncMock(spec=AsyncSession)
                mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await service.create_user(
                    email="newuser@example.com",
                    password="password123",
                    role=UserRoleEnum.viewer,
                )

                assert isinstance(result, dict)
                assert result["email"] == "newuser@example.com"
                mock_hash.assert_called_once_with("password123")
                mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_error(self):
        """Создание пользователя с существующим email должно вызывать ошибку."""
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password'):
            mock_repo.get_by_email.return_value = MagicMock()

            service = UserService()
            with pytest.raises(ValueError, match="уже существует"):
                await service.create_user(
                    email="existing@example.com",
                    password="password123",
                    role=UserRoleEnum.viewer,
                )

    @pytest.mark.asyncio
    async def test_create_user_invalid_role_raises_error(self):
        """Создание пользователя с недопустимой ролью должно вызывать ошибку."""
        with patch('mko_bi.services.user_service._validate_role',
                   side_effect=ValueError("Недопустимая роль")):

            service = UserService()
            with pytest.raises(ValueError, match="Недопустимая роль"):
                await service.create_user(
                    email="user@example.com",
                    password="password123",
                    role="invalid",
                )


class TestUserServiceGetUserById:
    """Тесты для метода get_user_by_id сервиса UserService."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_exists(self):
        """Получение существующего пользователя по ID."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "user@example.com"
        mock_user.role = UserRoleEnum.viewer

        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
                mock_repo.get.return_value = mock_user

                result = await service.get_user_by_id(mock_user.id)

                assert result is not None
                assert result["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_exists(self):
        """Получение несуществующего пользователя должно возвращать None."""
        test_uuid = uuid4()

        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
                mock_repo.get.return_value = None

                result = await service.get_user_by_id(test_uuid)

                assert result is None


class TestUserServiceListUsers:
    """Тесты для метода list_users сервиса UserService."""

    @pytest.mark.asyncio
    async def test_list_users_returns_list(self):
        """Получение списка пользователей."""
        mock_users = [
            MagicMock(spec=user_model.User, email="user1@example.com"),
            MagicMock(spec=user_model.User, email="user2@example.com"),
        ]

        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
                mock_repo.get_all.return_value = mock_users

                result = await service.get_all_users()

                assert len(result) == 2


class TestUserServiceUpdateUserRole:
    """Тесты для метода update_user_role сервиса UserService."""

    @pytest.mark.asyncio
    async def test_update_user_role_success(self):
        """Успешное обновление роли пользователя."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()

        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
                mock_repo.update.return_value = mock_user

                result = await service.update_user_role(
                    user_id=mock_user.id,
                    role=UserRoleEnum.admin,
                )

                assert result is not None

    @pytest.mark.asyncio
    async def test_update_user_role_not_found(self):
        """Обновление роли несуществующего пользователя должно возвращать None."""
        test_uuid = uuid4()

        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo:
                mock_repo.update.return_value = None

                result = await service.update_user_role(
                    user_id=test_uuid,
                    role=UserRoleEnum.admin,
                )

                assert result is None


class TestUserServiceDeleteUser:
    """Тесты для метода delete_user сервиса UserService."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Успешное удаление пользователя."""
        mock_user = MagicMock(spec=user_model.User, role="viewer")

        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
                 patch('mko_bi.services.user_service._validate_user_exists', return_value=mock_user), \
                 patch('mko_bi.services.user_service._check_admin_deletion_allowed'):

                mock_repo.delete.return_value = True

                result = await service.delete_user(user_id=uuid4())

                assert result is True

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        """Удаление несуществующего пользователя должно возвращать False."""
        service = UserService()
        with patch('mko_bi.services.user_service.get_session') as mock_get_session:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch('mko_bi.services.user_service.UserRepository'), \
                 patch('mko_bi.services.user_service._validate_user_exists', return_value=None):

                result = await service.delete_user(user_id=uuid4())

                assert result is False
