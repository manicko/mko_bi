"""Тесты для сервиса управления пользователями (user_service.py).

Тестирует бизнес-логику CRUD операций с пользователями
с использованием моков для изоляции тестов.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_role,
    delete_user,
    get_all_users,
    register_user,
    _validate_role,
    _validate_user_exists,
    _check_admin_deletion_allowed,
)
from mko_bi.db.models import user as user_model
from mko_bi.models.user import UserRead
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

    def test_user_exists(self):
        """Существующий пользователь должен возвращаться."""
        mock_user = MagicMock(spec=user_model.User)
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get.return_value = mock_user
            result = _validate_user_exists(test_uuid, mock_session)
            assert result == mock_user

    def test_user_not_exists(self):
        """Несуществующий пользователь должен возвращать None."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get.return_value = None
            result = _validate_user_exists(test_uuid, mock_session)
            assert result is None


class TestCheckAdminDeletionAllowed:
    """Тесты для функции проверки разрешения на удаление администратора."""

    def test_delete_last_admin_with_other_users(self):
        """Удаление последнего админа при наличии других пользователей должно вызывать ошибку."""
        mock_users = [
            MagicMock(spec=user_model.User, role="admin"),
            MagicMock(spec=user_model.User, role="viewer"),
        ]
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_all.return_value = mock_users
            with pytest.raises(ValueError, match="Нельзя удалить администратора"):
                _check_admin_deletion_allowed(mock_session)

    def test_delete_admin_with_only_admin(self):
        """Удаление админа, если он единственный, должно быть разрешено."""
        mock_users = [MagicMock(spec=user_model.User, role="admin")]
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_all.return_value = mock_users
            _check_admin_deletion_allowed(mock_session)  # Не должно вызывать ошибку

    def test_delete_admin_with_multiple_admins(self):
        """Удаление админа при наличии других админов должно быть разрешено."""
        mock_users = [
            MagicMock(spec=user_model.User, role="admin"),
            MagicMock(spec=user_model.User, role="admin"),
            MagicMock(spec=user_model.User, role="viewer"),
        ]
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_all.return_value = mock_users
            _check_admin_deletion_allowed(mock_session)  # Не должно вызывать ошибку


class TestCreateUser:
    """Тесты для функции создания пользователя."""

    def test_create_user_success(self):
        """Успешное создание пользователя."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "newuser@example.com"
        mock_user.role = UserRoleEnum.viewer
        mock_user.created_at = "2026-04-27T17:30:00"
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password') as mock_hash:

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.return_value = mock_user
            mock_repo.get_by_email.return_value = None

            result = create_user(
                "newuser@example.com", "password123", "viewer", mock_session
            )

            assert isinstance(result, UserRead)
            assert result.email == "newuser@example.com"
            assert result.role == UserRoleEnum.viewer
            mock_hash.assert_called_once_with("password123")
            mock_repo.create.assert_called_once()

    def test_create_user_duplicate_email_raises_error(self):
        """Создание пользователя с существующим email должно вызывать ошибку."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password'):

            mock_repo.get_by_email.return_value = MagicMock()

            with pytest.raises(ValueError, match="уже существует"):
                create_user("existing@example.com", "password123", "viewer", mock_session)

    def test_create_user_invalid_role_raises_error(self):
        """Создание пользователя с недопустимой ролью должно вызывать ошибку."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service._validate_role',
                   side_effect=ValueError("Недопустимая роль")):

            with pytest.raises(ValueError, match="Недопустимая роль"):
                create_user("user@example.com", "password123", "invalid", mock_session)

    def test_create_user_auto_session(self):
        """Создание пользователя с автоматическим созданием сессии."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "autouser@example.com"
        mock_user.role = UserRoleEnum.admin
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.user_service.get_session') as mock_get_session, \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password') as mock_hash, \
             patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service.UserRepository.get_by_email', return_value=None):

            mock_session = MagicMock(spec=Session)
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_session)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_get_session.return_value = mock_context
            mock_repo.create.return_value = mock_user
            mock_hash.return_value = "$2b$12$hashedpassword"

            result = create_user("autouser@example.com", "password123", "admin")

            assert isinstance(result, UserRead)
            assert result.email == "autouser@example.com"
            mock_get_session.assert_called_once()
            mock_session.close.assert_called_once()

    def test_create_user_database_error_rolls_back(self):
        """Ошибка базы данных должна вызывать откат транзакции."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password') as mock_hash, \
             patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service.UserRepository.get_by_email', return_value=None):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                create_user("user@example.com", "password123", "viewer", mock_session)


class TestGetUserByEmail:
    """Тесты для функции получения пользователя по email."""

    def test_get_user_by_email_found(self):
        """Пользователь должен быть найден по email."""
        mock_user = MagicMock(spec=user_model.User)
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.return_value = mock_user
            result = get_user_by_email("user@example.com", mock_session)
            assert result == mock_user
            mock_repo.get_by_email.assert_called_once_with("user@example.com", mock_session)

    def test_get_user_by_email_not_found(self):
        """Несуществующий email должен возвращать None."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.return_value = None
            result = get_user_by_email("nonexistent@example.com", mock_session)
            assert result is None

    def test_get_user_by_email_auto_session(self):
        """Получение пользователя с автоматическим созданием сессии."""
        mock_user = MagicMock(spec=user_model.User)
        with patch('mko_bi.services.user_service.get_session') as mock_get_session, \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_session = MagicMock(spec=Session)
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_session)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_get_session.return_value = mock_context
            mock_repo.get_by_email.return_value = mock_user

            result = get_user_by_email("user@example.com")

            assert result == mock_user
            mock_get_session.assert_called_once()
            mock_session.close.assert_called_once()


class TestGetUserById:
    """Тесты для функции получения пользователя по ID."""

    def test_get_user_by_id_found(self):
        """Пользователь должен быть найден по ID."""
        mock_user = MagicMock(spec=user_model.User)
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get.return_value = mock_user
            result = get_user_by_id(test_uuid, mock_session)
            assert result == mock_user
            mock_repo.get.assert_called_once_with(test_uuid, mock_session)

    def test_get_user_by_id_not_found(self):
        """Несуществующий ID должен возвращать None."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get.return_value = None
            result = get_user_by_id(test_uuid, mock_session)
            assert result is None


class TestUpdateUserRole:
    """Тесты для функции обновления роли пользователя."""


    def test_update_user_role_not_found(self):
        """Обновление роли несуществующего пользователя должно вернуть None."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service._validate_user_exists', return_value=None):

            result = update_user_role(test_uuid, "admin", mock_session)
            assert result is None

    def test_update_user_role_invalid_role_raises_error(self):
        """Обновление с недопустимой ролью должно вызывать ошибку."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service._validate_role',
                   side_effect=ValueError("Недопустимая роль")):

            with pytest.raises(ValueError, match="Недопустимая роль"):
                update_user_role(test_uuid, "invalid", mock_session)


class TestDeleteUser:
    """Тесты для функции удаления пользователя."""


    def test_delete_user_not_found(self):
        """Удаление несуществующего пользователя должно вернуть False."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service._validate_user_exists', return_value=None):
            result = delete_user(test_uuid, mock_session)
            assert result is False

    def test_delete_last_admin_with_other_users_raises_error(self):
        """Удаление последнего админа при наличии других пользователей должно вызывать ошибку."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.role = "admin"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed',
                   side_effect=ValueError("Нельзя удалить администратора")):

            mock_val_exists.return_value = mock_user

            with pytest.raises(ValueError, match="Нельзя удалить администратора"):
                delete_user(test_uuid, mock_session)

    def test_delete_user_database_error_rolls_back(self):
        """Ошибка базы данных при удалении должна вызывать откат."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.role = "viewer"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_user
            mock_repo.delete.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                delete_user(test_uuid, mock_session)


class TestGetAllUsers:
    """Тесты для функции получения всех пользователей."""

    def test_get_all_users(self):
        """Должен возвращаться список всех пользователей."""
        mock_users = [
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
        ]
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_all.return_value = mock_users
            result = get_all_users(mock_session)
            assert result == mock_users
            mock_repo.get_all.assert_called_once_with(mock_session)

    def test_get_all_users_empty(self):
        """При отсутствии пользователей должен возвращаться пустой список."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_all.return_value = []
            result = get_all_users(mock_session)
            assert result == []

class TestRegisterUser:
    """Тесты для функции регистрации пользователя (алиас)."""

    def test_register_user_is_alias(self):
        """Функция register_user должна быть алиасом для create_user."""
        mock_user = MagicMock(spec=UserRead)
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.create_user') as mock_create:
            mock_create.return_value = mock_user
            result = register_user("user@example.com", "password", "viewer", mock_session)
            assert result == mock_user
            mock_create.assert_called_once_with(
                "user@example.com", "password", "viewer", mock_session
            )


class TestUserServiceIntegration:
    """Интеграционные тесты для сервиса пользователей."""



    def test_user_email_uniqueness_enforced(self):
        """Проверка принудительного соблюдения уникальности email."""
        existing_user = MagicMock(spec=user_model.User)
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password'):

            mock_repo.get_by_email.return_value = existing_user

            with pytest.raises(ValueError, match="уже существует"):
                create_user("duplicate@example.com", "password123", "viewer", mock_session)

    def test_cannot_delete_last_admin_with_other_users(self):
        """Нельзя удалить последнего админа, если есть другие пользователи."""
        mock_admin = MagicMock(spec=user_model.User)
        mock_admin.role = "admin"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        mock_users = [
            MagicMock(spec=user_model.User, role="admin"),
            MagicMock(spec=user_model.User, role="viewer"),
        ]

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_admin
            mock_repo.get_all.return_value = mock_users

            with pytest.raises(ValueError, match="Нельзя удалить администратора"):
                delete_user(test_uuid, mock_session)

    def test_can_delete_admin_if_only_admin(self):
        """Можно удалить админа, если он единственный пользователь."""
        mock_admin = MagicMock(spec=user_model.User)
        mock_admin.role = "admin"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_admin
            mock_repo.get_all.return_value = [mock_admin]
            mock_repo.delete.return_value = True

            result = delete_user(test_uuid, mock_session)
            assert result is True


    def test_user_deletion_cascade_handling(self):
        """Проверка обработки каскадного удаления."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.role = "viewer"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_user
            mock_repo.delete.return_value = True

            result = delete_user(test_uuid, mock_session)
            assert result is True
            mock_repo.delete.assert_called_once_with(test_uuid, mock_session)

    def test_get_nonexistent_user_by_email(self):
        """Поиск несуществующего пользователя по email."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.return_value = None
            result = get_user_by_email("ghost@example.com", mock_session)
            assert result is None

    def test_get_nonexistent_user_by_id(self):
        """Поиск несуществующего пользователя по ID."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get.return_value = None
            result = get_user_by_id(test_uuid, mock_session)
            assert result is None

    def test_update_nonexistent_user_role(self):
        """Обновление роли несуществующего пользователя."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service._validate_user_exists', return_value=None):

            result = update_user_role(test_uuid, "admin", mock_session)
            assert result is None

    def test_sqlalchemy_error_on_user_creation(self):
        """Обработка ошибки SQLAlchemy при создании пользователя."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password') as mock_hash, \
             patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service.UserRepository.get_by_email', return_value=None):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(SQLAlchemyError):
                create_user("user@example.com", "password", "viewer", mock_session)

    def test_sqlalchemy_error_on_user_deletion(self):
        """Обработка ошибки SQLAlchemy при удалении пользователя."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.role = "viewer"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_user
            mock_repo.delete.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(SQLAlchemyError):
                delete_user(test_uuid, mock_session)

    def test_can_delete_admin_if_only_admin(self):
        """Можно удалить админа, если он единственный пользователь."""
        mock_admin = MagicMock(spec=user_model.User)
        mock_admin.role = "admin"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_admin
            mock_repo.get_all.return_value = [mock_admin]
            mock_repo.delete.return_value = True

            result = delete_user(test_uuid, mock_session)
            assert result is True


    def test_user_deletion_cascade_handling(self):
        """Проверка обработки каскадного удаления."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.role = "viewer"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_user
            mock_repo.delete.return_value = True

            result = delete_user(test_uuid, mock_session)
            assert result is True
            mock_repo.delete.assert_called_once_with(test_uuid, mock_session)

    def test_get_nonexistent_user_by_email(self):
        """Поиск несуществующего пользователя по email."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.return_value = None
            result = get_user_by_email("ghost@example.com", mock_session)
            assert result is None

    def test_get_nonexistent_user_by_id(self):
        """Поиск несуществующего пользователя по ID."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo:
            mock_repo.get.return_value = None
            result = get_user_by_id(test_uuid, mock_session)
            assert result is None

    def test_update_nonexistent_user_role(self):
        """Обновление роли несуществующего пользователя."""
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service._validate_user_exists', return_value=None):

            result = update_user_role(test_uuid, "admin", mock_session)
            assert result is None

    def test_sqlalchemy_error_on_user_creation(self):
        """Обработка ошибки SQLAlchemy при создании пользователя."""
        mock_session = MagicMock(spec=Session)
        with patch('mko_bi.services.user_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.user_service.hash_password') as mock_hash, \
             patch('mko_bi.services.user_service._validate_role'), \
             patch('mko_bi.services.user_service.UserRepository.get_by_email', return_value=None):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(SQLAlchemyError):
                create_user("user@example.com", "password", "viewer", mock_session)

    def test_sqlalchemy_error_on_user_deletion(self):
        """Обработка ошибки SQLAlchemy при удалении пользователя."""
        mock_user = MagicMock(spec=user_model.User)
        mock_user.role = "viewer"
        test_uuid = uuid4()
        mock_session = MagicMock(spec=Session)

        with patch('mko_bi.services.user_service._validate_user_exists') as mock_val_exists, \
             patch('mko_bi.services.user_service._check_admin_deletion_allowed'), \
             patch('mko_bi.services.user_service.UserRepository') as mock_repo:

            mock_val_exists.return_value = mock_user
            mock_repo.delete.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(SQLAlchemyError):
                delete_user(test_uuid, mock_session)



