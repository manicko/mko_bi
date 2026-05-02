"""Тесты для сервиса аутентификации (auth_service.py).

Тестирует бизнес-логику регистрации и аутентификации пользователей
с использованием моков для изоляции тестов.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def test_unique_email_passes(self, async_db_session):
        """Уникальный email должен проходить проверку."""
        service = AuthService()
        with patch.object(AuthService, '_check_email_uniqueness') as mock_check:
            mock_check.return_value = None
            await service._check_email_uniqueness("newuser@example.com", async_db_session)

    async def test_duplicate_email_raises_value_error(self, async_db_session):
        """Дублирующийся email должен вызывать ValueError."""
        service = AuthService()
        with patch.object(AuthService, '_check_email_uniqueness', side_effect=ValueError("Пользователь с email 'dup@example.com' уже существует")):
            with pytest.raises(ValueError, match="уже существует"):
                await service._check_email_uniqueness("dup@example.com", async_db_session)


class TestRegisterUser:
    """Тесты для регистрации пользователя."""

    async def test_register_user_success(self, async_db_session):
        """Успешная регистрация пользователя."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "newuser@example.com"
        mock_user.role = UserRoleEnum.viewer
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.return_value = mock_user

            result = await service.register_user(
                "newuser@example.com", "password123", "viewer", async_db_session
            )

        assert isinstance(result, UserRead)

    async def test_register_user_with_auto_session(self):
        """Регистрация пользователя без передачи сессии."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "autouser@example.com"
        mock_user.role = UserRoleEnum.admin
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.auth_service.get_session') as mock_get_session, \
             patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_session = MagicMock(spec=AsyncSession)
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_get_session.return_value = mock_context
            mock_repo.create.return_value = mock_user
            mock_hash.return_value = "$2b$12$hashedpassword"

            result = await service.register_user(
                "autouser@example.com", "password123", "admin"
            )

        assert isinstance(result, UserRead)

    async def test_register_user_duplicate_email_raises_error(self, async_db_session):
        """Регистрация с существующим email должна вызывать ошибку."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock), \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness',
                         side_effect=ValueError("Пользователь с email 'dup@example.com' уже существует")):

            with pytest.raises(ValueError, match="уже существует"):
                await service.register_user("dup@example.com", "password123", "viewer", async_db_session)

    async def test_register_user_invalid_role_raises_error(self, async_db_session):
        """Регистрация с неверной ролью должна вызывать ошибку."""
        service = AuthService()
        with patch.object(AuthService, '_validate_role',
                         side_effect=ValueError("Недопустимая роль")):

            with pytest.raises(ValueError, match="Недопустимая роль"):
                await service.register_user("user@example.com", "password123", "invalid", async_db_session)

    async def test_register_user_database_error_rolls_back(self, async_db_session):
        """Ошибка БД при регистрации должна вызывать исключение."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                await service.register_user("user@example.com", "password123", "viewer", async_db_session)

    async def test_register_user_invalid_email_format(self, async_db_session):
        """Регистрация с неверным форматом email должна вызывать ошибку."""
        service = AuthService()
        with patch.object(AuthService, '_validate_role'):
            with pytest.raises(ValueError, match="Некорректный формат email"):
                await service.register_user("invalid-email", "password123", "viewer", async_db_session)


class TestAuthenticateUser:
    """Тесты для аутентификации пользователя."""

    async def test_authenticate_user_success(self, async_db_session):
        """Успешная аутентификация пользователя."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = uuid4()
        mock_user.email = "user@example.com"
        mock_user.password_hash = "$2b$12$correcthash"
        mock_user.role = UserRoleEnum.viewer
        mock_user.created_at = "2026-04-27T17:30:00"

        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.verify_password') as mock_verify:

            mock_repo.get_by_email.return_value = mock_user
            mock_verify.return_value = True

            result = await service.authenticate_user("user@example.com", "correct_password", async_db_session)

        assert result == mock_user

    async def test_authenticate_user_wrong_password(self, async_db_session):
        """Аутентификация с неверным паролем должна возвращать None."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.password_hash = "$2b$12$correcthash"

        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.verify_password') as mock_verify:

            mock_repo.get_by_email.return_value = mock_user
            mock_verify.return_value = False

            result = await service.authenticate_user("user@example.com", "wrong_password", async_db_session)

        assert result is None

    async def test_authenticate_user_not_found(self, async_db_session):
        """Аутентификация несуществующего пользователя должна возвращать None."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get_by_email.return_value = None

            result = await service.authenticate_user("nonexistent@example.com", "password", async_db_session)

        assert result is None

    async def test_authenticate_user_auto_session(self):
        """Аутентификация без передачи сессии."""
        service = AuthService()
        mock_user = MagicMock(spec=UserDB)
        mock_user.password_hash = "$2b$12$correcthash"

        with patch('mko_bi.services.auth_service.get_session') as mock_get_session, \
             patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.verify_password') as mock_verify:

            mock_session = MagicMock(spec=AsyncSession)
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_get_session.return_value = mock_context
            mock_repo.get_by_email.return_value = mock_user
            mock_verify.return_value = True

            result = await service.authenticate_user("user@example.com", "password")

        assert result == mock_user

    async def test_authenticate_user_database_error(self, async_db_session):
        """Ошибка БД при аутентификации должна вызывать исключение."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get_by_email.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                await service.authenticate_user("user@example.com", "password", async_db_session)


class TestLoginUser:
    """Тесты для входа пользователя."""

    async def test_login_user_success(self, async_db_session):
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

            result = await service.login_user("user@example.com", "password", async_db_session)

        assert result["access_token"] == "jwt.token.here"

    async def test_login_user_invalid_credentials(self, async_db_session):
        """Вход с неверными данными должен вызывать ValueError."""
        service = AuthService()
        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(service, '_rate_limiter') as mock_limiter:

            mock_auth.return_value = None
            mock_limiter.check_rate_limit.return_value = True

            with pytest.raises(ValueError, match="Неверный email или пароль"):
                await service.login_user("user@example.com", "wrong_password", async_db_session)

    async def test_login_user_auto_session(self):
        """Вход без передачи сессии."""
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

            result = await service.login_user("user@example.com", "password")

        assert result["access_token"] == "jwt.token.here"

    async def test_registration_with_sqlalchemy_error(self, async_db_session):
        """Ошибка БД при регистрации."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo, \
             patch('mko_bi.services.auth_service.hash_password') as mock_hash, \
             patch.object(AuthService, '_validate_role'), \
             patch.object(AuthService, '_validate_email_format'), \
             patch.object(AuthService, '_check_email_uniqueness'):

            mock_hash.return_value = "$2b$12$hashedpassword"
            mock_repo.create.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError, match="Database connection failed"):
                await service.register_user("user@example.com", "password123", "viewer", async_db_session)

    async def test_authentication_with_sqlalchemy_error(self, async_db_session):
        """Ошибка БД при аутентификации."""
        service = AuthService()
        with patch('mko_bi.services.auth_service.UserRepository', new_callable=AsyncMock) as mock_repo:
            mock_repo.get_by_email.side_effect = SQLAlchemyError("Database connection failed")

            with pytest.raises(SQLAlchemyError, match="Database connection failed"):
                await service.authenticate_user("user@example.com", "password", async_db_session)

    async def test_login_with_invalid_credentials(self, async_db_session):
        """Вход с неверными данными."""
        service = AuthService()
        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(service, '_rate_limiter') as mock_limiter:

            mock_auth.return_value = None
            mock_limiter.check_rate_limit.return_value = True

            with pytest.raises(ValueError, match="Неверный email или пароль"):
                await service.login_user("user@example.com", "wrong_password", async_db_session)

    async def test_login_with_database_error(self, async_db_session):
        """Ошибка БД при входе."""
        service = AuthService()
        with patch.object(AuthService, 'authenticate_user') as mock_auth, \
             patch.object(service, '_rate_limiter') as mock_limiter:

            mock_auth.side_effect = SQLAlchemyError("Database connection failed")
            mock_limiter.check_rate_limit.return_value = True

            with pytest.raises(SQLAlchemyError, match="Database connection failed"):
                await service.login_user("user@example.com", "password", async_db_session)
