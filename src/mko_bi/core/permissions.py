"""Модуль управления доступом и проверки прав.

Предоставляет функции и зависимости для проверки прав доступа пользователей
к дашбордам и операциям в системе BI Dashboard.

Иерархия ролей:
    admin > editor > viewer

Где admin имеет все права, editor может читать и писать,
viewer только читать.
"""

import logging
from functools import lru_cache
from collections.abc import AsyncGenerator
from typing import Any, cast
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.core.security import decode_token
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.db.session import get_session
from mko_bi.models.user import UserDB
from mko_bi.models.user_roles import PermissionEnum, UserRoleEnum


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI зависимость для получения сессии базы данных.
    
    Создает новую асинхронную сессию для каждого запроса и закрывает её после завершения.
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with get_session() as db:
        try:
            yield db
        finally:
            # Явное закрытие для гарантии
            await db.close()

logger = logging.getLogger(__name__)


# --- Констанны ---


# Иерархия ролей (чем выше значение, тем больше прав)
# Используем UserRoleEnum - значения уже определяют порядок
ROLE_LEVELS: dict[UserRoleEnum, int] = {
    UserRoleEnum.VIEWER: 1,
    UserRoleEnum.EDITOR: 2,
    UserRoleEnum.ADMIN: 3,
}

# Уровни доступа - используем PermissionEnum
PERMISSION_LEVELS: dict[str, int] = {
    "view": 1,
    "edit": 2,
    "admin": 3,
    "read": 1,  # Для обратной совместимости
}
# Для обратной совместимости также принимаем "read" как "view" и "write" как "edit"


# --- Исключения ---


class PermissionError(Exception):
    """Исключение, выбрасываемое при отсутствии прав доступа."""

    pass


class AuthenticationError(Exception):
    """Исключение, выбрасываемое при ошибке аутентификации."""

    pass


# --- Вспомогательные функции ---


def _get_role_level(role: str) -> int:
    """Получить числовой уровень роли.

    Args:
        role: Строковое представление роли (viewer, editor, admin).

    Returns:
        int: Числовой уровень роли.

    Raises:
        ValueError: Если роль неизвестна.
    """
    try:
        role_enum = UserRoleEnum(role)
        return ROLE_LEVELS[role_enum]
    except ValueError as err:
        logger.error("Неизвестная роль: %s", role)
        raise ValueError(f"Неизвестная роль: '{role}'") from err


# --- Основные функции проверки прав ---


def check_role(user_role: str, required_role: str) -> bool:
    """Проверить, достаточно ли роли пользователя для выполнения операции.

    Сравнивает уровень роли пользователя с требуемым уровнем.
    Использует иерархию: admin > editor > viewer.

    Args:
        user_role: Роль пользователя (viewer, editor, admin).
        required_role: Минимально требуемая роль.

    Returns:
        bool: True, если роль пользователя достаточна, иначе False.

    Example:
        >>> check_role("admin", "viewer")
        True
        >>> check_role("editor", "admin")
        False
        >>> check_role("viewer", "viewer")
        True
    """
    try:
        user_level = _get_role_level(user_role)
        required_level = _get_role_level(required_role)
        has_access = user_level >= required_level
        logger.debug(
            "Проверка роли: user_role=%s (уровень %d), "
            "required_role=%s (уровень %d) -> %s",
            user_role,
            user_level,
            required_role,
            required_level,
            has_access,
        )
        return has_access
    except ValueError as e:
        logger.error("Ошибка при проверке роли: %s", e)
        return False


async def check_dashboard_access(
    user_id: UUID,
    dashboard_id: UUID,
    required_permission: str = "view",
    db: AsyncSession | None = None,
) -> bool:
    """Проверяет, есть ли у пользователя доступ к дашборду.

    Args:
        user_id: Идентификатор пользователя.
        dashboard_id: Идентификатор дашборда.
        required_permission: Требуемый уровень доступа (view/edit/admin).
        db: Асинхронная сессия базы данных. Если не передана, создается новая.

    Returns:
        True, если доступ есть, иначе False.
    """
    logger.info(
        "Проверка доступа: user_id=%s, dashboard_id=%s, required=%s",
        user_id,
        dashboard_id,
        required_permission,
    )

    # Валидация требуемого разрешения
    if required_permission not in [e.value for e in PermissionEnum]:
        raise ValueError(
            f"Допустимые значения: {[e.value for e in PermissionEnum]}"
        )

    # Если сессия не передана, создаем новую через контекстный менеджер
    if db is None:
        async with get_session() as session:
            return await _check_access_with_session(
                user_id, dashboard_id, required_permission, session
            )
    else:
        return await _check_access_with_session(
            user_id, dashboard_id, required_permission, db
        )


async def _check_access_with_session(
    user_id: UUID,
    dashboard_id: UUID,
    required_permission: str,
    db: AsyncSession,
) -> bool:
    """Внутренняя функция для проверки доступа с использованием сессии.

    Args:
        user_id: Идентификатор пользователя.
        dashboard_id: Идентификатор дашборда.
        required_permission: Требуемый уровень доступа.
        db: Асинхронная сессия базы данных.

    Returns:
        True, если доступ есть, иначе False.
    """
    try:
        # Получаем уровень доступа пользователя
        permission = await AccessRepository.check_access(
            user_id=user_id,
            dashboard_id=dashboard_id,
            db=db,
        )

        if permission is None:
            logger.warning(
                "Доступ отсутствует: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return False

        # Иерархия разрешений: admin > edit > view
        # Нормализуем названия для совместимости (read->view, write->edit)
        perm_map = {"view": "view", "edit": "edit", "admin": "admin"}
        permission_normalized = perm_map.get(permission, permission)
        required_normalized = perm_map.get(required_permission, required_permission)

        permission_levels = {"view": 1, "edit": 2, "admin": 3}
        has_access = (
            permission_levels[permission_normalized]
            >= permission_levels[required_normalized]
        )

        logger.info(
            "Проверка доступа: user_id=%s, dashboard_id=%s, "
            "permission=%s, required=%s -> %s",
            user_id,
            dashboard_id,
            permission,
            required_permission,
            has_access,
        )

        return has_access

    except Exception as e:
        logger.error(
            "Ошибка при проверке доступа user_id=%s, dashboard_id=%s: %s",
            user_id,
            dashboard_id,
            e,
        )
        return False


@lru_cache(maxsize=128)
def _decode_token_cached(token: str) -> dict[str, Any] | None:
    """Кэшированное декодирование токена.

    Args:
        token: JWT токен.

    Returns:
        dict[str, Any] | None: Декодированные данные токена или None.
    """
    result = decode_token(token)
    if result is None:
        return None
    return cast(dict[str, Any], result)


async def get_current_user(
    token: str,
    db: AsyncSession | None = None,
) -> UserDB:
    """Получить текущего пользователя по токену.

    Декодирует JWT токен, извлекает user_id и получает
    данные пользователя из базы.

    Args:
        token: JWT токен доступа.
        db: Асинхронная сессия базы данных. Если не передана, создается новая.

    Returns:
        UserDB: Модель пользователя с данными из базы.

    Raises:
        AuthenticationError: Если токен недействителен или пользователь не найден.
    """
    # Если сессия не передана, создаем новую через контекстный менеджер
    if db is None:
        async with get_session() as session:
            return await _get_current_user_with_session(token, session)
    else:
        return await _get_current_user_with_session(token, db)


async def _get_current_user_with_session(
    token: str,
    db: AsyncSession,
) -> UserDB:
    """Внутренняя функция для получения пользователя с использованием сессии.

    Args:
        token: JWT токен доступа.
        db: Асинхронная сессия базы данных.

    Returns:
        UserDB: Модель пользователя.

    Raises:
        AuthenticationError: Если токен недействителен или пользователь не найден.
    """
    try:
        # Декодируем токен (с кэшированием)
        payload = _decode_token_cached(token)
        if payload is None:
            logger.warning("Недействительный токен")
            raise AuthenticationError("Недействительный токен")

        user_id_raw = payload.get("user_id")
        if user_id_raw is None:
            logger.warning("В токене отсутствует user_id")
            raise AuthenticationError("Некорректный токен")

        user_id: UUID = UUID(str(user_id_raw))

        # Получаем пользователя из базы
        user = await UserRepository.get(user_id, db)
        if user is None:
            logger.warning("Пользователь не найден: user_id=%s", user_id)
            raise AuthenticationError("Пользователь не найден")

        logger.info("Пользователь аутентифицирован: user_id=%s", user_id)
        return UserDB.model_validate(user)

    except JWTError as e:
        logger.error("Ошибка декодирования JWT: %s", e)
        raise AuthenticationError("Ошибка декодирования токена") from e
    except Exception as e:
        if not isinstance(e, AuthenticationError):
            logger.error("Ошибка при получении пользователя: %s", e)
        raise


# --- FastAPI зависимости ---

security = HTTPBearer()


def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserDB:
    """FastAPI зависимость для получения текущего пользователя.

    Извлекает токен из заголовка Authorization, декодирует его
    и возвращает данные пользователя.

    Args:
        credentials: Учетные данные из заголовка Authorization.
        db: Сессия базы данных.

    Returns:
        UserDB: Модель аутентифицированного пользователя.

    Raises:
        HTTPException: Если токен недействителен или пользователь не найден.
    """
    try:
        user = get_current_user(credentials.credentials, db)
        # Сохраняем пользователя в state запроса для последующего использования
        # (будет доступно через request.state.user)
        return user
    except AuthenticationError as e:
        logger.warning("Ошибка аутентификации: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error("Неожиданная ошибка аутентификации: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        ) from e


def require_role(required_role: str):
    """Создает FastAPI зависимость для проверки роли пользователя.

    Args:
        required_role: Минимально требуемая роль.

    Returns:
        Callable: Зависимость FastAPI.

    Raises:
        HTTPException: Если у пользователя недостаточно прав.

    Example:
        @app.get("/admin")
        async def admin_route(user: UserDB = Depends(get_current_user_dependency),
                             _: None = Depends(require_role("admin"))):
            return {"message": "Admin area"}
    """

    def role_checker(user: UserDB = Depends(get_current_user_dependency)) -> UserDB:
        """Проверяет роль пользователя и возвращает его при успехе."""
        if not check_role(user.role, required_role):
            logger.warning(
                "Недостаточно прав: user_id=%s, user_role=%s, required_role=%s",
                user.id,
                user.role,
                required_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {required_role} или выше",
            )
        return user

    return role_checker


def require_dashboard_access(
    required_permission: str = "read",
):
    """Создает FastAPI зависимость для проверки доступа к дашборду.

    Проверяет, есть ли у пользователя доступ к указанному дашборду
    с требуемым уровнем разрешения.

    Args:
        required_permission: Требуемый уровень доступа (read/write/admin).
            По умолчанию "read".

    Returns:
        Callable: Зависимость FastAPI.

    Raises:
        HTTPException: Если у пользователя нет доступа.

    Example:
        @app.get("/dashboards/{dashboard_id}")
        async def get_dashboard(
            dashboard_id: int,
            user: UserDB = Depends(get_current_user_dependency),
            _: None = Depends(require_dashboard_access("read")),
        ):
            return {"message": "Dashboard data"}
    """

    async def access_checker(
        dashboard_id: UUID,
        user: UserDB = Depends(get_current_user_dependency),
        db: AsyncSession = Depends(get_db),
    ) -> UserDB:
        """Проверяет доступ пользователя к дашборду."""
        if not await check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission=required_permission,
            db=db,
        ):
            logger.warning(
                "Отказано в доступе: user_id=%s, dashboard_id=%s, required=%s",
                user.id,
                dashboard_id,
                required_permission,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этому дашборду",
            )
        return user

    return access_checker
