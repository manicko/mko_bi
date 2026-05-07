"""Утилиты для валидации данных.

Предоставляет функции для проверки email, ролей, UUID и строк.
Используется для централизованной валидации во всем приложении.
"""

import logging
import re
from uuid import UUID

from mkobi.models.enums import UserRole

logger = logging.getLogger(__name__)

# Регулярное выражение для валидации email
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> bool:
    """Проверить валидность email адреса.

    Args:
        email: Email адрес для проверки.

    Returns:
        True, если email валиден, иначе False.

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        logger.warning("Email пустой или не является строкой")
        return False

    if not EMAIL_REGEX.match(email):
        logger.warning("Невалидный формат email: %s", email)
        return False

    return True


def validate_role(role: str | UserRole) -> bool:
    """Проверить, является ли роль допустимой.

    Args:
        role: Роль для проверки (строка или UserRole).

    Returns:
        True, если роль допустима, иначе False.

    Example:
        >>> validate_role("admin")
        True
        >>> validate_role("invalid_role")
        False
    """
    try:
        if isinstance(role, UserRole):
            return True
        UserRole(role)
        return True
    except (ValueError, TypeError):
        logger.warning("Недопустимая роль: %s", role)
        return False


def validate_uuid(uuid_str: str) -> bool:
    """Проверить, является ли строка валидным UUID.

    Args:
        uuid_str: Строка для проверки.

    Returns:
        True, если строка является валидным UUID, иначе False.

    Example:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> validate_uuid("not-a-uuid")
        False
    """
    try:
        UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        logger.warning("Невалидный UUID: %s", uuid_str)
        return False


def validate_string(
    value: str,
    min_length: int = 0,
    max_length: int | None = None,
    required: bool = True,
) -> bool:
    """Проверить строку на соответствие критериям.

    Args:
        value: Строка для проверки.
        min_length: Минимальная длина строки.
        max_length: Максимальная длина строки (None - без ограничений).
        required: Обязательно ли поле.

    Returns:
        True, если строка валидна, иначе False.

    Example:
        >>> validate_string("hello", min_length=1, max_length=10)
        True
        >>> validate_string("", required=True)
        False
    """
    if value is None:
        if required:
            logger.warning("Строка обязательна, но получено None")
            return False
        return True

    if not isinstance(value, str):
        logger.warning("Значение не является строкой: %s", type(value))
        return False

    if required and len(value) == 0:
        logger.warning("Строка не может быть пустой")
        return False

    if len(value) < min_length:
        logger.warning(
            "Строка слишком короткая: %s < %s", len(value), min_length
        )
        return False

    if max_length is not None and len(value) > max_length:
        logger.warning(
            "Строка слишком длинная: %s > %s", len(value), max_length
        )
        return False

    return True


def validate_password(password: str, min_length: int = 8) -> bool:
    """Проверить сложность пароля.

    Args:
        password: Пароль для проверки.
        min_length: Минимальная длина пароля.

    Returns:
        True, если пароль соответствует требованиям, иначе False.

    Example:
        >>> validate_password("SecurePass123")
        True
        >>> validate_password("short")
        False
    """
    if not password or not isinstance(password, str):
        logger.warning("Пароль пустой или не является строкой")
        return False

    if len(password) < min_length:
        logger.warning(
            "Пароль слишком короткий: %s < %s", len(password), min_length
        )
        return False

    # Проверка на наличие хотя бы одной цифры и одной буквы
    if not re.search(r"\d", password):
        logger.warning("Пароль должен содержать хотя бы одну цифру")
        return False

    if not re.search(r"[a-zA-Z]", password):
        logger.warning("Пароль должен содержать хотя бы одну букву")
        return False

    return True


def raise_if_invalid(condition: bool, message: str, exception_type: type = ValueError) -> None:
    """Выбросить исключение, если условие ложно.

    Args:
        condition: Условие для проверки.
        message: Сообщение об ошибке.
        exception_type: Тип исключения.

    Raises:
        exception_type: Если condition is False.
    """
    if not condition:
        logger.error("Ошибка валидации: %s", message)
        raise exception_type(message)
