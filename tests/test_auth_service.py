"""Тесты для сервиса аутентификации и регистрации (auth_service.py).

Тестирует бизнес-логику регистрации, аутентификации и входа пользователей.
Использует изолированную тестовую базу данных SQLite in-memory.
"""

import pytest
from unittest.mock import patch, MagicMock

from mko_bi.services.auth_service import (
    register_user,
    authenticate_user,
    login_user,
    _validate_role,
    _validate_email_format,
    _check_email_uniqueness,
    VALID_ROLES,
)
from mko_bi.db.models import user as user_model
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.db.session import SessionLocal


class TestValidateRole:
    """Тесты для функции проверки роли."""

    def test_valid_roles(self):
        """Все допустимые роли должны проходить проверку."""
        for role in VALID_ROLES:
            _validate_role(role)

    def test_invalid_role_raises_error(self):
        """Недопустимая роль должна вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role("invalid_role")

    def test_empty_role_raises_error(self):
        """Пустая роль должна вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role("")

    def test_none_role_raises_error(self):
        """None как роль должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role(None)


class TestValidateEmailFormat:
    """Тесты для функции проверки формата email."""

    def test_valid_email(self):
        """Валидный email должен проходить проверку."""
        result = _validate_email_format("user@example.com")
        assert result == "user@example.com"

    def test_valid_email_with_plus(self):
        """Email с плюсом должен проходить проверку."""
        result = _validate_email_format("user+tag@example.com")
        assert result == "user+tag@example.com"

    def test_valid_email_with_subdomain(self):
        """Email с поддоменом должен проходить проверку."""
        result = _validate_email_format("user@mail.example.com")
        assert result == "user@mail.example.com"

    def test_invalid_email_no_at(self):
        """Email без @ должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Некорректный формат email"):
            _validate_email_format("userexample.com")

    def test_invalid_email_no_domain(self):
        """Email без домена должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Некорректный формат email"):
            _validate_email_format("user@")

    def test_invalid_email_no_local_part(self):
        """Email без локальной части должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Некорректный формат email"):
            _validate_email_format("@example.com")

    def test_empty_email_raises_error(self):
        """Пустой email должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Некорректный формат email"):
            _validate_email_format("")


class TestCheckEmailUniqueness:
    """Тесты для функции проверки уникальности email."""

    def test_unique_email_passes(self, test_db):
        """Уникальный email должен проходить проверку."""
        # Не должно вызывать исключение
        _check_email_uniqueness("newuser@example.com", test_db)

    def test_duplicate_email_raises_error(self, test_db, test_user):
        """Дублирующийся email должен вызывать ValueError."""
        with pytest.raises(ValueError, match="уже существует"):
            _check_email_uniqueness(test_user.email, test_db)


class TestRegisterUser:
    """Тесты для функции регистрации пользователя."""

    def test_register_user_success(self, test_db):
        """Успешная регистрация пользователя."""
        user = register_user(
            "newuser@example.com", "secure_password123", "viewer", db=test_db
        )

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.role == "viewer"
        assert user.created_at is not None
        # Проверяем, что password_hash не возвращается
        assert not hasattr(user, "password_hash")

    def test_register_user_all_roles(self, test_db):
        """Регистрация пользователей со всеми допустимыми ролями."""
        for role in VALID_ROLES:
            email = f"{role}_user@example.com"
            user = register_user(email, "password123", role, db=test_db)
            assert user.role == role
            assert user.email == email

    def test_register_user_duplicate_email(self, test_db, test_user):
        """Регистрация с существующим email должна вызывать ошибку."""
        with pytest.raises(ValueError, match="уже существует"):
            register_user(test_user.email, "password123", "viewer", db=test_db)

    def test_register_user_invalid_role(self, test_db):
        """Регистрация с недопустимой ролью должна вызывать ошибку."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            register_user(
                "newuser@example.com", "password123", "invalid_role", db=test_db
            )

    def test_register_user_invalid_email(self, test_db):
        """Регистрация с некорректным email должна вызывать ошибку."""
        with pytest.raises(ValueError, match="Некорректный формат email"):
            register_user("invalid_email", "password123", "viewer", db=test_db)

    def test_register_user_password_is_hashed(self, test_db):
        """Пароль должен быть захеширован при сохранении."""
        register_user("hashuser@example.com", "plain_password", "viewer", db=test_db)

        user_obj = UserRepository.get_by_email("hashuser@example.com", test_db)
        assert user_obj is not None
        # Проверяем, что пароль захеширован (начинается с $2b$ для bcrypt)
        assert user_obj.password_hash.startswith("$2b$")
        assert user_obj.password_hash != "plain_password"

    def test_register_user_empty_password(self, test_db):
        """Регистрация с пустым паролем должна работать (bcrypt поддерживает)."""
        user = register_user("empty_pass@example.com", "", "viewer", db=test_db)
        assert user.email == "empty_pass@example.com"

    def test_register_user_long_password(self, test_db):
        """Регистрация с длинным паролем (более 72 байт)."""
        long_password = "a" * 100
        user = register_user(
            "longpass@example.com", long_password, "viewer", db=test_db
        )
        assert user.email == "longpass@example.com"

    def test_register_user_special_chars_password(self, test_db):
        """Регистрация с паролем со специальными символами."""
        special_password = "p@ssw0rd!#$%^&*()"
        user = register_user(
            "specialchars@example.com", special_password, "editor", db=test_db
        )
        assert user.role == "editor"

    def test_register_multiple_users(self, test_db):
        """Регистрация нескольких пользователей."""
        emails = ["multi1@example.com", "multi2@example.com", "multi3@example.com"]
        for i, email in enumerate(emails):
            user = register_user(email, f"password{i}", "viewer", db=test_db)
            assert user.email == email
            assert user.id > 0  # test_user уже есть с id=1

    def test_register_user_returns_correct_type(self, test_db):
        """register_user должна возвращать UserRead."""
        from mko_bi.models.user import UserRead

        user = register_user("typeduser@example.com", "password", "admin", db=test_db)
        assert isinstance(user, UserRead)


class TestAuthenticateUser:
    """Тесты для функции аутентификации пользователя."""

    def test_authenticate_user_success(self, test_db, test_user):
        """Успешная аутентификация с правильным паролем."""
        # Сначала зарегистрируем пользователя с известным паролем
        register_user("authuser@example.com", "correct_password", "viewer", db=test_db)

        user = authenticate_user("authuser@example.com", "correct_password", db=test_db)
        assert user is not None
        assert user.email == "authuser@example.com"
        assert user.role == "viewer"
        assert user.id is not None

    def test_authenticate_user_wrong_password(self, test_db):
        """Аутентификация с неверным паролем должна возвращать None."""
        register_user("wrongpass@example.com", "correct_password", "viewer", db=test_db)

        user = authenticate_user("wrongpass@example.com", "wrong_password", db=test_db)
        assert user is None

    def test_authenticate_user_nonexistent(self, test_db):
        """Аутентификация несуществующего пользователя должна возвращать None."""
        user = authenticate_user("nonexistent@example.com", "any_password", db=test_db)
        assert user is None

    def test_authenticate_user_empty_password(self, test_db):
        """Аутентификация с пустым паролем."""
        register_user("emptypass@example.com", "", "viewer", db=test_db)

        user = authenticate_user("emptypass@example.com", "", db=test_db)
        assert user is not None
        assert user.email == "emptypass@example.com"

    def test_authenticate_user_wrong_password_for_existing(self, test_db, test_user):
        """Аутентификация существующего пользователя с неверным паролем."""
        user = authenticate_user(test_user.email, "wrong_password", db=test_db)
        assert user is None

    def test_authenticate_user_returns_userdb(self, test_db):
        """authenticate_user должна возвращать UserDB."""
        from mko_bi.models.user import UserDB

        register_user("typedauth@example.com", "password", "admin", db=test_db)
        user = authenticate_user("typedauth@example.com", "password", db=test_db)
        assert isinstance(user, UserDB)

    def test_authenticate_user_has_password_hash(self, test_db):
        """UserDB должен содержать password_hash."""
        register_user("hashcheck@example.com", "password", "viewer", db=test_db)
        user = authenticate_user("hashcheck@example.com", "password", db=test_db)
        assert hasattr(user, "password_hash")
        assert user.password_hash.startswith("$2b$")


class TestLoginUser:
    """Тесты для функции входа пользователя."""

    def test_login_user_success(self, test_db):
        """Успешный вход пользователя."""
        register_user("loginuser@example.com", "login_password", "editor", db=test_db)

        result = login_user("loginuser@example.com", "login_password", db=test_db)

        assert "access_token" in result
        assert "token_type" in result
        assert "user_id" in result
        assert "email" in result
        assert "role" in result
        assert result["token_type"] == "bearer"
        assert result["email"] == "loginuser@example.com"
        assert result["role"] == "editor"
        assert isinstance(result["user_id"], int)
        assert isinstance(result["access_token"], str)
        assert "." in result["access_token"]  # JWT формат

    def test_login_user_wrong_password(self, test_db):
        """Вход с неверным паролем должен вызывать ValueError."""
        register_user(
            "wronglogin@example.com", "correct_password", "viewer", db=test_db
        )

        with pytest.raises(ValueError, match="Неверный email или пароль"):
            login_user("wronglogin@example.com", "wrong_password", db=test_db)

    def test_login_user_nonexistent(self, test_db):
        """Вход несуществующего пользователя должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Неверный email или пароль"):
            login_user("nonexistent_login@example.com", "any_password", db=test_db)

    def test_login_user_returns_correct_structure(self, test_db):
        """login_user должна возвращать словарь с правильными ключами."""
        register_user("structuser@example.com", "password", "admin", db=test_db)

        result = login_user("structuser@example.com", "password", db=test_db)

        expected_keys = {"access_token", "token_type", "user_id", "email", "role"}
        assert set(result.keys()) == expected_keys

    def test_login_user_token_is_valid(self, test_db):
        """Созданный токен должен быть валидным JWT."""
        register_user("tokenuser@example.com", "password", "viewer", db=test_db)

        result = login_user("tokenuser@example.com", "password", db=test_db)
        token = result["access_token"]

        # Проверяем базовую структуру JWT
        parts = token.split(".")
        assert len(parts) == 3
        assert all(part for part in parts)  # Все части не пустые

    def test_login_user_different_users_different_tokens(self, test_db):
        """Разные пользователи должны получать разные токены."""
        register_user("multi1@example.com", "password1", "viewer", db=test_db)
        register_user("multi2@example.com", "password2", "admin", db=test_db)

        token1 = login_user("multi1@example.com", "password1", db=test_db)[
            "access_token"
        ]
        token2 = login_user("multi2@example.com", "password2", db=test_db)[
            "access_token"
        ]

        assert token1 != token2

    def test_login_user_token_contains_user_data(self, test_db):
        """Токен должен содержать данные пользователя."""
        from mko_bi.core.security import decode_token

        register_user("decodeduser@example.com", "password", "editor", db=test_db)

        result = login_user("decodeduser@example.com", "password", db=test_db)
        token = result["access_token"]

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["email"] == "decodeduser@example.com"
        assert decoded["role"] == "editor"
        assert decoded["user_id"] == result["user_id"]


class TestIntegrationAuthFlow:
    """Интеграционные тесты полного цикла аутентификации."""

    def test_full_registration_and_login_flow(self, test_db):
        """Полный цикл: регистрация -> аутентификация -> вход."""
        # 1. Регистрация
        user = register_user(
            "fullflow@example.com", "my_secure_password", "admin", db=test_db
        )
        assert user.email == "fullflow@example.com"
        assert user.role == "admin"

        # 2. Аутентификация
        auth_user = authenticate_user(
            "fullflow@example.com", "my_secure_password", db=test_db
        )
        assert auth_user is not None
        assert auth_user.email == user.email
        assert auth_user.role == user.role

        # 3. Вход (получение токена)
        login_result = login_user(
            "fullflow@example.com", "my_secure_password", db=test_db
        )
        assert "access_token" in login_result
        assert login_result["email"] == user.email

    def test_failed_auth_flow(self, test_db):
        """Цикл с неверным паролем на этапе аутентификации."""
        # Регистрация
        register_user("failflow@example.com", "correct_pass", "viewer", db=test_db)

        # Аутентификация с неверным паролем
        auth_user = authenticate_user("failflow@example.com", "wrong_pass", db=test_db)
        assert auth_user is None

        # Вход должен завершиться ошибкой
        with pytest.raises(ValueError):
            login_user("failflow@example.com", "wrong_pass", db=test_db)

    def test_register_login_multiple_users(self, test_db):
        """Регистрация и вход нескольких пользователей."""
        users_data = [
            ("alice@example.com", "alice_pass", "admin"),
            ("bob@example.com", "bob_pass", "editor"),
            ("charlie@example.com", "charlie_pass", "viewer"),
        ]

        for email, password, role in users_data:
            # Регистрация
            user = register_user(email, password, role, db=test_db)
            assert user.role == role

            # Аутентификация
            auth_user = authenticate_user(email, password, db=test_db)
            assert auth_user is not None

            # Вход
            login_result = login_user(email, password, db=test_db)
            assert login_result["email"] == email
            assert login_result["role"] == role


class TestAuthServiceErrorHandling:
    """Тесты обработки ошибок в сервисе аутентификации."""

    def test_register_with_db_error(self, test_db, monkeypatch):
        """Ошибка базы данных при регистрации должна пробрасываться."""

        def mock_create(*args, **kwargs):
            raise Exception("DB connection failed")

        monkeypatch.setattr(UserRepository, "create", mock_create)

        with pytest.raises(Exception, match="DB connection failed"):
            register_user("erroruser@example.com", "password", "viewer", db=test_db)

    def test_authenticate_with_db_error(self, test_db, monkeypatch):
        """Ошибка базы данных при аутентификации должна пробрасываться."""

        def mock_get_by_email(*args, **kwargs):
            raise Exception("DB connection failed")

        monkeypatch.setattr(UserRepository, "get_by_email", mock_get_by_email)

        with pytest.raises(Exception, match="DB connection failed"):
            authenticate_user("erroruser@example.com", "password", db=test_db)

    def test_register_user_rollback_on_error(self, test_db):
        """При ошибке регистрации изменения должны откатиться."""
        # Регистрируем первого пользователя
        user1 = register_user("rollback1@example.com", "password", "viewer", db=test_db)

        # Пробуем зарегистрировать с тем же email (должно быть исключение)
        with pytest.raises(ValueError):
            register_user("rollback1@example.com", "password2", "admin", db=test_db)

        # Проверяем, что в базе только один пользователь с этим email
        users = (
            test_db.execute(
                test_db.query(user_model.User).filter(
                    user_model.User.email == "rollback1@example.com"
                )
            )
            .scalars()
            .all()
        )
        assert len(users) == 1
        assert users[0].role == "viewer"  # Роль не изменилась


class TestAuthServiceLogging:
    """Тесты логирования в сервисе аутентификации."""

    def test_register_user_logs_info(self, test_db, caplog):
        """Регистрация должна логировать информацию."""
        with caplog.at_level("INFO"):
            register_user("loguser@example.com", "password", "viewer", db=test_db)

        assert any(
            "Starting user registration" in record.message for record in caplog.records
        )
        assert any(
            "User successfully registered" in record.message
            for record in caplog.records
        )

    def test_authenticate_user_logs_warning_on_failure(self, test_db, caplog):
        """Неудачная аутентификация должна логировать предупреждение."""
        with caplog.at_level("WARNING"):
            authenticate_user("nonexistent@example.com", "password", db=test_db)

        assert any("не найден" in record.message for record in caplog.records)

    def test_login_user_logs_warning_on_failure(self, test_db, caplog):
        """Неудачный вход должен логировать предупреждение."""
        with caplog.at_level("WARNING"):
            with pytest.raises(ValueError):
                login_user("nonexistent@example.com", "password", db=test_db)

        assert any(
            "Failed login attempt" in record.message for record in caplog.records
        )
