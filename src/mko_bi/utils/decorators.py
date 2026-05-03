"""Декораторы для повторяющихся паттернов.

Предоставляет декораторы для замера времени, повторных попыток,
логирования и проверки прав доступа.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from mko_bi.models.user_roles import UserRoleEnum

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def timing(func: Callable[P, T]) -> Callable[P, T]:
    """Декоратор для замера времени выполнения функции.

    Логирует время выполнения функции в миллисекундах.

    Args:
        func: Функция для декорирования.

    Returns:
        Обернутая функция.

    Example:
        @timing
        def slow_function():
            time.sleep(1)
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "Время выполнения %s: %.2f мс", func.__name__, elapsed
        )
        return result

    return cast(Callable[P, T], wrapper)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Декоратор для повторных попыток при ошибке.

    Args:
        max_attempts: Максимальное количество попыток.
        delay: Задержка между попытками в секундах.
        exceptions: Кортеж исключений, при которых повторять попытку.

    Returns:
        Декоратор.

    Example:
        @retry(max_attempts=3, delay=0.5)
        def unreliable_function():
            # может упасть
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        "Попытка %s/%s для %s не удалась: %s",
                        attempt,
                        max_attempts,
                        func.__name__,
                        e,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)

            logger.error(
                "Все %s попыток для %s не удались. Последняя ошибка: %s",
                max_attempts,
                func.__name__,
                last_exception,
            )
            if last_exception:
                raise last_exception
            raise RuntimeError("All attempts failed but no exception was captured")

        return cast(Callable[P, T], wrapper)

    return decorator


def log_execution(
    log_args: bool = True, log_result: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Декоратор для логирования выполнения функции.

    Args:
        log_args: Логировать аргументы функции.
        log_result: Логировать результат функции.

    Returns:
        Декоратор.

    Example:
        @log_execution(log_args=True, log_result=True)
        def process_data(data):
            return data
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if log_args:
                logger.info(
                    "Вызов %s с args=%s, kwargs=%s",
                    func.__name__,
                    args,
                    kwargs,
                )
            else:
                logger.info("Вызов %s", func.__name__)

            try:
                result = func(*args, **kwargs)
                if log_result:
                    logger.info(
                        "Результат %s: %s", func.__name__, result
                    )
                return result
            except Exception as e:
                logger.error(
                    "Ошибка в %s: %s", func.__name__, e, exc_info=True
                )
                raise

        return cast(Callable[P, T], wrapper)

    return decorator


def require_role(required_role: str | UserRoleEnum) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Декоратор для проверки роли пользователя.

    Args:
        required_role: Требуемая роль.

    Returns:
        Декоратор.

    Example:
        @require_role("admin")
        def admin_only_function(user):
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Ожидаем, что user передается как аргумент или keyword аргумент
            user = kwargs.get("user") or (args[0] if args else None)

            if not user:
                logger.error(
                    "Пользователь не передан в %s для проверки роли",
                    func.__name__,
                )
                raise PermissionError("Пользователь не найден")

            # Получаем роль пользователя
            user_role = getattr(user, "role", None)
            if not user_role:
                logger.error(
                    "Роль пользователя не найдена в %s", func.__name__
                )
                raise PermissionError("Роль пользователя не найдена")

            # Проверяем роль
            from mko_bi.core.permissions import check_role

            if not check_role(str(user_role), str(required_role)):
                logger.warning(
                    "Недостаточно прав для %s: role=%s, required=%s",
                    func.__name__,
                    user_role,
                    required_role,
                )
                raise PermissionError(
                    f"Требуется роль: {required_role} или выше"
                )

            return func(*args, **kwargs)

        return cast(Callable[P, T], wrapper)

    return decorator


def error_handler(
    fallback_value: T | None = None, log_error: bool = True
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Декоратор для обработки ошибок с fallback значением.

    Args:
        fallback_value: Значение, возвращаемое при ошибке.
        log_error: Логировать ошибку.

    Returns:
        Декоратор.

    Example:
        @error_handler(fallback_value=[])
        def get_data():
            # может упасть
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        "Ошибка в %s: %s", func.__name__, e, exc_info=True
                    )
                if fallback_value is not None:
                    return fallback_value
                raise

        return cast(Callable[P, T], wrapper)

    return decorator
