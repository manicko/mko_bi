"""Модуль безопасности для хеширования паролей и работы с JWT токенами."""

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

import bcrypt
import redis
from jose import JWTError, jwt

from mko_bi.config import get_config

logger = logging.getLogger(__name__)


# Константы
SALT_ROUNDS: int = 12
MAX_PASSWORD_LENGTH: int = 72


class RateLimiter:
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client

    def check_rate_limit(self, key: str, max_attempts: int, ttl: int) -> bool:
        attempts = self._redis.get(key)
        if attempts is not None and int(str(attempts)) >= max_attempts:
            logger.warning("Rate limit exceeded for key: %s", key)
            return False

        pipeline = self._redis.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, ttl)
        pipeline.execute()
        return True


def _truncate_password(password: str) -> str:
    """Обрезает пароль до максимальной длины для bcrypt (72 байта).

    Bcrypt имеет ограничение на длину пароля - 72 байта.
    Если пароль длиннее, он обрезается до этой длины.

    Args:
        password: Исходный пароль.

    Returns:
        str: Пароль, обрезанный до 72 байт при необходимости.
    """
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_LENGTH:
        truncated = encoded[:MAX_PASSWORD_LENGTH].decode("utf-8", errors="ignore")
        logger.warning(
            "Пароль длиннее %d байт и был обрезан до %d байт",
            len(encoded),
            MAX_PASSWORD_LENGTH,
        )
        return truncated
    return password


def hash_password(password: str) -> str:
    """Хеширует пароль с использованием bcrypt.

    Использует алгоритм bcrypt с заданным числом раундов соли (SALT_ROUNDS=12).
    Пароль обрезается до 72 байт перед хешированием, так как bcrypt имеет
    ограничение на максимальную длину пароля.

    Args:
        password: Пароль в виде обычной строки.

    Returns:
        str: Хеш пароля в формате bcrypt.

    Example:
        >>> hash = hash_password("my_secure_password")
        >>> isinstance(hash, str)
        True
    """
    truncated_password = _truncate_password(password)
    password_bytes = truncated_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=SALT_ROUNDS)
    password_hash = bcrypt.hashpw(password_bytes, salt)
    logger.info("Пароль успешно захеширован")
    return password_hash.decode("latin-1")


def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хешу.

    Сравнивает переданный пароль с сохраненным хешем bcrypt.
    Пароль обрезается до 72 байт перед проверкой.

    Args:
        password: Пароль в виде обычной строки для проверки.
        hashed_password: Хеш пароля, сохраненный в базе данных.

    Returns:
        bool: True, если пароль соответствует хешу, иначе False.

    Example:
        >>> hash = hash_password("my_password")
        >>> verify_password("my_password", hash)
        True
        >>> verify_password("wrong_password", hash)
        False
    """
    truncated_password = _truncate_password(password)
    password_bytes = truncated_password.encode("utf-8")
    hash_bytes = hashed_password.encode("latin-1")
    try:
        result = bcrypt.checkpw(password_bytes, hash_bytes)
        if result:
            logger.info("Пароль успешно верифицирован")
        else:
            logger.warning("Неудачная попытка верификации пароля")
        return result
    except (ValueError, TypeError) as e:
        logger.error("Ошибка при верификации пароля: %s", e)
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Создает JWT токен доступа с указанными данными.

    Токен содержит переданные данные и время истечения (exp).
    Если expires_delta не указан, используется значение из конфигурации
    (по умолчанию 30 минут).

    Args:
        data: Данные для включения в токен (например, user_id, email).
        expires_delta: Дополнительное время жизни токена.
            Если None, используется значение из конфигурации.

    Returns:
        str: Закодированный JWT токен.

    Example:
        >>> token = create_access_token({"user_id": 1, "email": "user@example.com"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()
    # Конвертируем UUID объекты в строки для JWT сериализации
    for key, value in to_encode.items():
        from uuid import UUID
        if isinstance(value, UUID):
            to_encode[key] = str(value)
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        config = get_config()
        expire = datetime.now(UTC) + timedelta(
            minutes=config.jwt.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode,
        get_config().jwt.secret_key,
        algorithm=get_config().jwt.algorithm,
    )
    logger.info("JWT токен успешно создан")
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Декодирует и валидирует JWT токен.

    Проверяет подпись токена и время его действия (exp).
    В случае ошибки декодирования или валидации возвращает None.

    Args:
        token: JWT токен для декодирования.

    Returns:
        dict[str, Any] | None: Декодированные данные токена или None,
            если токен недействителен.

    Example:
        >>> token = create_access_token({"user_id": 1})
        >>> data = decode_token(token)
        >>> data["user_id"]
        1
        >>> decode_token("invalid.token.here") is None
        True
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            get_config().jwt.secret_key,
            algorithms=[get_config().jwt.algorithm],
        )
        logger.info("JWT токен успешно декодирован")
        return payload
    except JWTError as e:
        logger.error("Ошибка декодирования JWT токена: %s", e)
        return None
    except Exception as e:
        logger.error("Непредвиденная ошибка при декодировании токена: %s", e)
        return None


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Декодирует и валидирует JWT токен (alias для decode_token).

    Args:
        token: JWT токен для декодирования.

    Returns:
        dict[str, Any] | None: Декодированные данные токена или None.
    """
    return decode_token(token)


def get_current_user(token: str) -> dict[str, Any] | None:
    """Получить данные текущего пользователя из JWT токена.

    Декодирует токен и возвращает данные пользователя.

    Args:
        token: JWT токен доступа.

    Returns:
        dict[str, Any] | None: Данные пользователя из токена или None.
    """
    return decode_token(token)


# Alias для обратной совместимости
generate_password_hash = hash_password
