"""Decorators for common patterns.

Provides decorators for timing, retry, logging, and access control.
Supports both sync and async functions.
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from mkobi.core.permissions import check_role, DashboardPermissionError
from mkobi.models.enums import UserRole

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def timing(func: Callable[P, T]) -> Callable[P, T]:  # noqa: UP047
    """Decorator for measuring function execution time.

    Logs function execution time in milliseconds.
    Supports both sync and async functions.

    Args:
        func: Function to decorate.

    Returns:
        Wrapped function.

    Example:
        @timing
        def slow_function():
            time.sleep(1)

        @timing
        async def async_function():
            await asyncio.sleep(1)
    """

    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            start = asyncio.get_event_loop().time()
            result = await func(*args, **kwargs)
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            logger.info("Execution time %s: %.2f ms", func.__name__, elapsed)
            return result

        return cast(Callable[P, T], async_wrapper)
    else:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            start = asyncio.get_event_loop().time()
            result = func(*args, **kwargs)
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            logger.info("Execution time %s: %.2f ms", func.__name__, elapsed)
            return result

        return cast(Callable[P, T], sync_wrapper)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for retrying on error.

    Supports both sync and async functions.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Delay between attempts in seconds.
        exceptions: Tuple of exceptions to retry on.

    Returns:
        Decorator.

    Example:
        @retry(max_attempts=3, delay=0.5)
        def unreliable_function():
            # may fail
            pass

        @retry(max_attempts=3, delay=0.5)
        async def async_unreliable():
            await some_operation()
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                last_exception: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        logger.warning(
                            "Attempt %s/%s for %s failed: %s",
                            attempt,
                            max_attempts,
                            func.__name__,
                            e,
                        )
                        if attempt < max_attempts:
                            await asyncio.sleep(delay)

                logger.error(
                    "All %s attempts for %s failed. Last error: %s",
                    max_attempts,
                    func.__name__,
                    last_exception,
                )
                if last_exception:
                    raise last_exception
                raise RuntimeError("All attempts failed but no exception was captured")

            return cast(Callable[P, T], async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                last_exception: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        logger.warning(
                            "Attempt %s/%s for %s failed: %s",
                            attempt,
                            max_attempts,
                            func.__name__,
                            e,
                        )
                        if attempt < max_attempts:
                            import time
                            time.sleep(delay)

                logger.error(
                    "All %s attempts for %s failed. Last error: %s",
                    max_attempts,
                    func.__name__,
                    last_exception,
                )
                if last_exception:
                    raise last_exception
                raise RuntimeError("All attempts failed but no exception was captured")

            return cast(Callable[P, T], sync_wrapper)

    return decorator


def log_execution(
    log_args: bool = True, log_result: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for logging function execution.

    Supports both sync and async functions.

    Args:
        log_args: Log function arguments.
        log_result: Log function result.

    Returns:
        Decorator.

    Example:
        @log_execution(log_args=True, log_result=True)
        def process_data(data):
            return data
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                if log_args:
                    logger.info(
                        "Calling %s with args=%s, kwargs=%s",
                        func.__name__,
                        args,
                        kwargs,
                    )
                else:
                    logger.info("Calling %s", func.__name__)

                try:
                    result = await func(*args, **kwargs)
                    if log_result:
                        logger.info("Result %s: %s", func.__name__, result)
                    return result
                except Exception as e:
                    logger.error("Error in %s: %s", func.__name__, e, exc_info=True)
                    raise

            return cast(Callable[P, T], async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                if log_args:
                    logger.info(
                        "Calling %s with args=%s, kwargs=%s",
                        func.__name__,
                        args,
                        kwargs,
                    )
                else:
                    logger.info("Calling %s", func.__name__)

                try:
                    result = func(*args, **kwargs)
                    if log_result:
                        logger.info("Result %s: %s", func.__name__, result)
                    return result
                except Exception as e:
                    logger.error("Error in %s: %s", func.__name__, e, exc_info=True)
                    raise

            return cast(Callable[P, T], sync_wrapper)

    return decorator


def require_role(
    required_role: str | UserRole,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for checking user role.

    Supports both sync and async functions.

    Args:
        required_role: Required role.

    Returns:
        Decorator.

    Example:
        @require_role("admin")
        def admin_only_function(user):
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                user = kwargs.get("user") or (args[0] if args else None)

                if not user:
                    logger.error(
                        "User not provided in %s for role check",
                        func.__name__,
                    )
                    raise DashboardPermissionError("User not found")

                user_role = getattr(user, "role", None)
                if not user_role:
                    logger.error("User role not found in %s", func.__name__)
                    raise DashboardPermissionError("User role not found")

                if not check_role(str(user_role), str(required_role)):
                    logger.warning(
                        "Insufficient permissions for %s: role=%s, required=%s",
                        func.__name__,
                        user_role,
                        required_role,
                    )
                    raise DashboardPermissionError(f"Required role: {required_role} or higher")

                return await func(*args, **kwargs)

            return cast(Callable[P, T], async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                user = kwargs.get("user") or (args[0] if args else None)

                if not user:
                    logger.error(
                        "User not provided in %s for role check",
                        func.__name__,
                    )
                    raise DashboardPermissionError("User not found")

                user_role = getattr(user, "role", None)
                if not user_role:
                    logger.error("User role not found in %s", func.__name__)
                    raise DashboardPermissionError("User role not found")

                if not check_role(str(user_role), str(required_role)):
                    logger.warning(
                        "Insufficient permissions for %s: role=%s, required=%s",
                        func.__name__,
                        user_role,
                        required_role,
                    )
                    raise DashboardPermissionError(f"Required role: {required_role} or higher")

                return func(*args, **kwargs)

            return cast(Callable[P, T], sync_wrapper)

    return decorator


def error_handler(  # noqa: UP047
    fallback_value: T | None = None, log_error: bool = True
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for error handling with fallback value.

    Supports both sync and async functions.

    Args:
        fallback_value: Value returned on error.
        log_error: Log the error.

    Returns:
        Decorator.

    Example:
        @error_handler(fallback_value=[])
        def get_data():
            # may fail
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if log_error:
                        logger.error("Error in %s: %s", func.__name__, e, exc_info=True)
                    if fallback_value is not None:
                        return fallback_value
                    raise

            return cast(Callable[P, T], async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if log_error:
                        logger.error("Error in %s: %s", func.__name__, e, exc_info=True)
                    if fallback_value is not None:
                        return fallback_value
                    raise

            return cast(Callable[P, T], sync_wrapper)

    return decorator
