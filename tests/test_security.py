"""Тесты для модуля безопасности (security.py)."""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
from jose import jwt

from mko_bi.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    _truncate_password,
)
from mko_bi.config import config


class TestTruncatePassword:
    """Тесты для функции _truncate_password."""

    def test_short_password_not_truncated(self):
        """Короткий пароль не должен обрезаться."""
        password = "short"
        result = _truncate_password(password)
        assert result == password

    def test_exact_length_password_not_truncated(self):
        """Пароль ровно 72 байта не должен обрезаться."""
        password = "a" * 72
        result = _truncate_password(password)
        assert result == password

    def test_long_password_truncated(self):
        """Пароль длиннее 72 байт должен обрезаться."""
        password = "a" * 100
        result = _truncate_password(password)
        assert len(result.encode("utf-8")) <= 72
        assert result == "a" * 72

    def test_unicode_password_truncated(self):
        """Unicode пароль должен корректно обрезаться."""
        password = "α" * 50  # Каждый символ - 2 байта в UTF-8
        result = _truncate_password(password)
        assert len(result.encode("utf-8")) <= 72


class TestHashPassword:
    """Тесты для функции hash_password."""

    def test_hash_returns_string(self):
        """Хеш должен быть строкой."""
        result = hash_password("test_password")
        assert isinstance(result, str)

    def test_hash_starts_with_bcrypt_prefix(self):
        """Хеш bcrypt должен начинаться с $2b$."""
        result = hash_password("test_password")
        assert result.startswith("$2b$")

    def test_different_passwords_different_hashes(self):
        """Разные пароли должны давать разные хеши."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_same_password_same_hash(self):
        """Одинаковые пароли должны давать одинаковые хеши (с разной солью)."""
        # Из-за случайной соли хеши будут разными, но проверка должна работать
        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")
        assert hash1 != hash2  # Соли разные, поэтому хеши разные
        assert verify_password("same_password", hash1)
        assert verify_password("same_password", hash2)

    def test_hash_long_password(self):
        """Хеширование длинного пароля (более 72 байт)."""
        long_password = "a" * 100
        result = hash_password(long_password)
        assert isinstance(result, str)
        assert result.startswith("$2b$")

    def test_hash_empty_password(self):
        """Хеширование пустого пароля."""
        result = hash_password("")
        assert isinstance(result, str)
        assert result.startswith("$2b$")

    def test_hash_special_characters(self):
        """Хеширование пароля со специальными символами."""
        special_password = "p@ssw0rd!#$%^&*()"
        result = hash_password(special_password)
        assert isinstance(result, str)
        assert verify_password(special_password, result)


class TestVerifyPassword:
    """Тесты для функции verify_password."""

    def test_correct_password(self):
        """Правильный пароль должен проходить проверку."""
        password = "correct_password"
        hash_value = hash_password(password)
        assert verify_password(password, hash_value) is True

    def test_incorrect_password(self):
        """Неправильный пароль не должен проходить проверку."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hash_value = hash_password(password)
        assert verify_password(wrong_password, hash_value) is False

    def test_empty_password(self):
        """Проверка пустого пароля."""
        hash_value = hash_password("")
        assert verify_password("", hash_value) is True
        assert verify_password("not_empty", hash_value) is False

    def test_long_password_verification(self):
        """Проверка длинного пароля."""
        long_password = "a" * 100
        hash_value = hash_password(long_password)
        assert verify_password(long_password, hash_value) is True

    def test_invalid_hash_format(self):
        """Неверный формат хеша должен возвращать False."""
        assert verify_password("password", "invalid_hash") is False

    def test_empty_hash(self):
        """Пустой хеш должен возвращать False."""
        assert verify_password("password", "") is False

    def test_unicode_password_verification(self):
        """Проверка Unicode пароля."""
        unicode_password = "пароль123αβγ"
        hash_value = hash_password(unicode_password)
        assert verify_password(unicode_password, hash_value) is True


class TestCreateAccessToken:
    """Тесты для функции create_access_token."""

    def test_token_is_string(self):
        """Токен должен быть строкой."""
        token = create_access_token({"user_id": 1})
        assert isinstance(token, str)

    def test_token_contains_dot(self):
        """JWT токен должен содержать точки (формат header.payload.signature)."""
        token = create_access_token({"user_id": 1})
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_with_user_data(self):
        """Токен должен содержать переданные данные."""
        data = {"user_id": 123, "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 123
        assert decoded["email"] == "test@example.com"

    def test_token_with_custom_expiry(self):
        """Токен с кастомным временем жизни."""
        data = {"user_id": 1}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires_delta)
        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_token_has_exp_claim(self):
        """Токен должен содержать время истечения (exp)."""
        token = create_access_token({"user_id": 1})
        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_different_tokens_for_different_data(self):
        """Разные данные должны давать разные токены."""
        token1 = create_access_token({"user_id": 1})
        token2 = create_access_token({"user_id": 2})
        assert token1 != token2

    def test_empty_data_token(self):
        """Токен с пустыми данными."""
        token = create_access_token({})
        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded


class TestDecodeToken:
    """Тесты для функции decode_token."""

    def test_valid_token_decoding(self):
        """Декодирование валидного токена."""
        token = create_access_token({"user_id": 1, "email": "test@example.com"})
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 1
        assert decoded["email"] == "test@example.com"

    def test_invalid_token_returns_none(self):
        """Неверный токен должен возвращать None."""
        result = decode_token("invalid.token.here")
        assert result is None

    def test_empty_token_returns_none(self):
        """Пустой токен должен возвращать None."""
        result = decode_token("")
        assert result is None

    def test_malformed_token_returns_none(self):
        """Некорректно сформированный токен должен возвращать None."""
        result = decode_token("not.a.token")
        assert result is None

    def test_token_with_wrong_signature(self):
        """Токен с неверной подписью должен возвращать None."""
        # Создаем токен с правильным ключом
        token = create_access_token({"user_id": 1})
        # Пытаемся декодировать с другим ключом (имитация ошибки)
        with patch("mko_bi.core.security.config") as mock_config:
            mock_config.JWT_SECRET_KEY = "wrong_secret"
            mock_config.JWT_ALGORITHM = "HS256"
            result = decode_token(token)
            assert result is None

    def test_expired_token_returns_none(self):
        """Истекший токен должен возвращать None."""
        # Создаем токен с отрицательным временем жизни (уже истек)
        expired_delta = timedelta(seconds=-1)
        token = create_access_token({"user_id": 1}, expires_delta=expired_delta)
        result = decode_token(token)
        assert result is None

    def test_token_without_exp_claim(self):
        """Токен без exp claim (если создать вручную) должен декодироваться."""
        # Создаем токен вручную без exp
        payload = {"user_id": 1}
        token = jwt.encode(
            payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM,
        )
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 1
        assert "exp" not in decoded

    def test_token_with_additional_claims(self):
        """Токен с дополнительными полями."""
        data = {
            "user_id": 1,
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 1
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write"]


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_password_hash_and_verify_cycle(self):
        """Полный цикл: хеширование и проверка пароля."""
        original_password = "My$ecureP@ssw0rd!"
        hash_value = hash_password(original_password)
        assert verify_password(original_password, hash_value) is True
        assert verify_password("WrongPassword", hash_value) is False

    def test_full_token_create_and_decode_cycle(self):
        """Полный цикл: создание и декодирование токена."""
        user_data = {"user_id": 42, "email": "user42@example.com"}
        token = create_access_token(user_data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 42
        assert decoded["email"] == "user42@example.com"

    def test_token_expiration_from_config(self):
        """Проверка, что время жизни токена берется из конфигурации."""
        token = create_access_token({"user_id": 1})
        decoded = decode_token(token)
        assert decoded is not None
        assert "exp" in decoded
        # exp должен быть в будущем
        import time

        assert decoded["exp"] > time.time()

    def test_multiple_users_different_tokens(self):
        """Разные пользователи должны иметь разные токены."""
        token1 = create_access_token({"user_id": 1})
        token2 = create_access_token({"user_id": 2})
        token3 = create_access_token({"user_id": 3})
        assert token1 != token2 != token3
        assert decode_token(token1)["user_id"] == 1
        assert decode_token(token2)["user_id"] == 2
        assert decode_token(token3)["user_id"] == 3

    def test_password_hash_uniqueness(self):
        """Хеши одного и того же пароля должны быть разными (из-за соли)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_token_with_user_id_only(self):
        """Токен только с user_id."""
        token = create_access_token({"user_id": 999})
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == 999
