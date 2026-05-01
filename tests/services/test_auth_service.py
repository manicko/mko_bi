"""Тесты для сервиса аутентификации (auth_service.py).

Тестирует бизнес-логику регистрации и аутентификации пользователей
с использованием моков для изоляции тестов.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.services.auth_service import AuthService
from mko_bi.models.user import UserRead, UserDB
from mko_bi.models.user_roles import UserRoleEnum


class TestValidateRole:
    """Тесты для функции валидации роли."""

    def test_valid_role_admin(self):
        """Валидная роль admin должна проходить проверку."""
        service = AuthService()
        service._validate_role("admin")

    def test_valid_role_editor(self):
        """Валидная роль editor должна проходить проверку."""
        service = AuthService()
        service._validate_role("editor")

    def test_valid_role_viewer(self):
        """Валидная роль viewer должна проходить проверку."""
        service = AuthService()
        service._validate_role("viewer")

    def test_invalid_role_raises_value_error(self):
        """Недопустимая роль должна вызывать ValueError."""
        service = AuthService()
        with pytest.raises(ValueError, match="Недопустимая роль"):
            service._validate_role("invalid_role")

    def test_empty_role_raises_value_error(self):
        """Пустая роль должна вызывать ValueError."""
        service = AuthService()
        with pytest.raises(ValueError):
            service._validate_role("")


class TestValidateEmailFormat:
    """Тесты для функции валидации формата email."""

    def test_valid_email(self):
        """Валидный email должен проходить проверку."""
        service = AuthService()
        result = service._validate_email_format("user@example.com")
        assert result == "user@example.com"

    def test_valid_email_with_dots(self):
        """Email с точками должен проходить проверку."""
        service = AuthService()
        result = service._validate_email_format("first.last@example.co.uk")
        assert result == "first.last@example.co.uk"

    def test_valid_email_with_numbers(self):
        """Email с цифрами должен проходить проверку."""
        service = AuthService()
        result = service._validate_email_format("user123@example.com")
        assert result == "user123@example.com"

    def test_invalid_email_no_at(self):
        """Email без @ должен вызывать ValueError."""
        service = AuthService()
        with pytest.raises(ValueError, match="Некорректный формат email"):
            service._validate_email_format("userexample.com")

    def test_invalid_email_no_domain(self):
        """Email без домена должен вызывать ValueError."""
        service = AuthService()
        with pytest.raises(ValueError, match="Некорректный формат email"):
            service._validate_email_format("user@")

    def test_invalid_email_no_local_part(self):
        """Email без локальной части должен вызывать ValueError."""
        service = AuthService()
        with pytest.raises(ValueError, match="Некорректный формат email"):
            service._validate_email_format("@example.com")


class TestCheckEmailUniqueness:
    """Тесты для функции проверки уникальности email."""

    def test_unique_email_passes(self, db_session):
        """Уникальный email должен проходить проверку."""
        service = AuthService()
        with patch.object(AuthService, '_check_email_uniqueness') as mock_check:
            mock_check.return_value = None
            service._check_email_uniqueness("newuser@example.com", db_session)

    def test_duplicate_email_raises_value_error(self, db_session):
        """Дублирующийся email должен вызывать ValueError."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo:
            mock_user = MagicMock()
            mock_repo.get_by_email.return_value = mock_user
            with pytest.raises(ValueError, match="уже существует"):
                service._check_email_uniqueness("existing@example.com", db_session)


class TestRegisterUser:
    """Тесты для функции регистрации пользователя."""

    def test_register_user_success(self, db_session):
        """Успешная регистрация пользователя."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "newuser@example.com"
        mock_user.role = UserRoleEnum.viewer
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role') as mock_val_role, \
             patch.object(AuthService, '_validate_email_format') as mock_val_email, \
             patch.object(AuthService, '_check_email_uniqueness') as mock_check_unique:

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.return_value = mock_user

            result = service.register_user(
                "newuser@example.com", "password123", "viewer", db_session
            )

            assert isinstance(result, UserRead)
            assert result.email == "newuser@example.com"
            assert result.role == UserRoleEnum.viewer
            mock_val_role.assert_called_once_with("viewer")
            mock_val_email.assert_called_once_with("newuser@example.com")
            mock_check_unique.assert_called_once_with("newuser@example.com", db_session)
            mock_hash.assert_called_once_with("password123")
            mock_repo.create.assert_called_once()

    def test_register_user_with_auto_session(self):
        """Регистрация пользователя с автоматическим созданием сессии."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "autouser@example.com"
        mock_user.role = UserRoleEnum.admin
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.auth_service.get_session') as mock_get_session, \
             patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_session = MagicMock(spec=Session)
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_session)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_get_session.return_value = mock_context
            mock_repo.create.return_value = mock_user
            mock_hash.return_value = "$2b$12$hashedpassword"

            result = service.register_user(
                "autouser@example.com", "password123", "admin"
            )

            assert isinstance(result, UserRead)
            assert result.email == "autouser@example.com"
            mock_get_session.assert_called_once()

    def test_register_user_duplicate_email_raises_error(self, db_session):
        """Попытка регистрации с существующим email должна вызывать ошибку."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository'), \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness',
                         side_effect=ValueError("Пользователь с email 'dup@example.com' уже существует")):

            with pytest.raises(ValueError, match="уже существует"):
                service.register_user("dup@example.com", "password123", "viewer", db_session)

    def test_register_user_invalid_role_raises_error(self, db_session):
        """Попытка регистрации с недопустимой ролью должна вызывать ошибку."""
        service = AuthService()
        with patch.object(AuthService, '_validate_role',
                         side_effect=ValueError("Недопустимая роль")):

            with pytest.raises(ValueError, match="Недопустимая роль"):
                service.register_user("user@example.com", "password123", "invalid", db_session)

    def test_register_user_database_error_rolls_back(self, db_session):
        """Ошибка базы данных должна вызывать откат транзакции."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                service.register_user("user@example.com", "password123", "viewer", db_session)

    def test_register_user_invalid_email_format(self, db_session):
        """Некорректный формат email должен вызывать ошибку."""
        service = AuthService()
        with patch.object(AuthService, '_validate_role'):
            with pytest.raises(ValueError, match="Некорректный формат email"):
                service.register_user("invalid-email", "password123", "viewer", db_session)


class TestAuthenticateUser:
    """Тесты для функции аутентификации пользователя."""

    def test_authenticate_user_success(self, db_session):
        """Успешная аутентификация с правильным паролем."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "user@example.com"
        mock_user.password_hash = "$2b$12$correcthash"
        mock_user.role = UserRoleEnum.viewer
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.verify_password') as mock_verify:

            mock_repo.get_by_email.return_value = mock_user
            mock_verify.return_value = True

            result = service.authenticate_user("user@example.com", "correct_password", db_session)

            assert result == mock_user
            mock_repo.get_by_email.assert_called_once_with("user@example.com", db_session)
            mock_verify.assert_called_once_with("correct_password", "$2b$12$correcthash")

    def test_authenticate_user_wrong_password(self, db_session):
        """Аутентификация с неправильным паролем должна вернуть None."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.password_hash = "$2b$12$correcthash"

        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.verify_password') as mock_verify:

            mock_repo.get_by_email.return_value = mock_user
            mock_verify.return_value = False

            result = service.authenticate_user("user@example.com", "wrong_password", db_session)

            assert result is None
            mock_verify.assert_called_once_with("wrong_password", "$2b$12$correcthash")

    def test_authenticate_user_not_found(self, db_session):
        """Аутентификация несуществующего пользователя должна вернуть None."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.return_value = None

            result = service.authenticate_user("nonexistent@example.com", "password", db_session)

            assert result is None
            mock_repo.get_by_email.assert_called_once_with(
                "nonexistent@example.com", db_session
            )

    def test_authenticate_user_auto_session(self):
        """Аутентификация с автоматическим созданием сессии."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.password_hash = "$2b$12$correcthash"

        with patch('mko_bi.services.auth_service.get_session') as mock_get_session, \
             patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.verify_password') as mock_verify:

            mock_session = MagicMock(spec=Session)
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_session)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_get_session.return_value = mock_context
            mock_repo.get_by_email.return_value = mock_user
            mock_verify.return_value = True

            result = service.authenticate_user("user@example.com", "password")

            assert result == mock_user
            mock_get_session.assert_called_once()

    def test_authenticate_user_database_error(self, db_session):
        """Ошибка базы данных при аутентификации должна вызывать исключение."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                service.authenticate_user("user@example.com", "password", db_session)


class TestLoginUser:
    """Тесты для функции входа пользователя (создание JWT токена)."""

    def test_login_user_success(self, db_session):
        """Успешный вход пользователя."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "user@example.com"
        mock_user.role = UserRoleEnum.viewer

        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(AuthService, 'create_access_token') as mock_token, \
             patch.object(service, '_rate_limiter') as mock_limiter:

            mock_auth.return_value = mock_user
            mock_token.return_value = "jwt.token.here"
            mock_limiter.check_rate_limit.return_value = True

            result = service.login_user("user@example.com", "password", db_session)

            assert result["access_token"] == "jwt.token.here"
            assert result["token_type"] == "bearer"
            assert result["user_id"] == mock_user.id
            assert result["email"] == "user@example.com"
            assert result["role"] == UserRoleEnum.viewer
            mock_auth.assert_called_once_with("user@example.com", "password", db_session)
            mock_token.assert_called_once()

    def test_login_user_invalid_credentials(self, db_session):
        """Вход с неверными учетными данными должен вызывать ошибку."""
        service = AuthService()
        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(service, '_rate_limiter') as mock_limiter:
            mock_auth.return_value = None
            mock_limiter.check_rate_limit.return_value = True

            with pytest.raises(ValueError, match="Неверный email или пароль"):
                service.login_user("user@example.com", "wrong_password", db_session)

    def test_login_user_auto_session(self):
        """Вход с автоматическим созданием сессии."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "user@example.com"
        mock_user.role = UserRoleEnum.admin

        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(AuthService, 'create_access_token') as mock_token, \
             patch.object(service, '_rate_limiter') as mock_limiter:

            mock_auth.return_value = mock_user
            mock_token.return_value = "jwt.token.here"
            mock_limiter.check_rate_limit.return_value = True

            result = service.login_user("user@example.com", "password")

            assert result["access_token"] == "jwt.token.here"
            assert result["user_id"] == mock_user.id
            mock_auth.assert_called_once_with("user@example.com", "password", None)
            mock_token.assert_called_once()

    def test_registration_with_sqlalchemy_error(self, db_session):
        """Тест обработки ошибки SQLAlchemy при регистрации."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError, match="Database connection failed"):
                service.register_user("user@example.com", "password123", "viewer", db_session)

    def test_authentication_with_sqlalchemy_error(self, db_session):
        """Тест обработки ошибки SQLAlchemy при аутентификации."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository') as mock_repo:
            mock_repo.get_by_email.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError, match="Database connection failed"):
                service.authenticate_user("user@example.com", "password", db_session)

    def test_login_with_invalid_credentials(self, db_session):
        """Тест входа с неверными учетными данными."""
        service = AuthService()
        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(service, '_rate_limiter') as mock_limiter:
            mock_auth.return_value = None
            mock_limiter.check_rate_limit.return_value = True

            with pytest.raises(ValueError, match="Неверный email или пароль"):
                service.login_user("user@example.com", "wrong_password", db_session)

            mock_auth.assert_called_once_with("user@example.com", "wrong_password", db_session)

    def test_login_with_database_error(self, db_session):
        """Тест обработки ошибки базы данных при входе."""
        service = AuthService()
        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(service, '_rate_limiter') as mock_limiter:
            mock_auth.side_effect = SQLAlchemyError("Database connection failed")
            mock_limiter.check_rate_limit.return_value = True

            with pytest.raises(SQLAlchemyError, match="Database connection failed"):
                service.login_user("user@example.com", "password", db_session)

            mock_auth.assert_called_once_with("user@example.com", "password", db_session)
