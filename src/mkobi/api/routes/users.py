"""Маршруты для управления пользователями.

Этот модуль предоставляет эндпоинты для CRUD операций с пользователями.
Доступ к большинству операций ограничен и требует аутентификации.
Операции удаления и просмотра всех пользователей доступны только администраторам.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from mkobi.api.deps import (
    get_user_service,
    require_admin_role,
    CurrentUser,
)
from mkobi.models.enums import UserRole
from mkobi.models.user import UserRead
from mkobi.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание пользователя",
    description="Создает нового пользователя. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def create_user_endpoint(
    email: str,
    password: str,
    role: UserRole,
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Создает нового пользователя в системе.

    Args:
        email: Email пользователя. Должен быть валидным и уникальным.
        password: Пароль пользователя. Будет захеширован перед сохранением.
        role: Роль пользователя. Допустимые значения: 'admin', 'editor', 'viewer'.
        _: Пользователь с ролью admin (проверка через зависимость).
        user_service: Сервис пользователей.

    Returns:
        UserRead: Модель созданного пользователя без пароля.

    Raises:
        HTTPException 403: Если роль недопустима или email уже занят.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Создание пользователя: email=%s, role=%s", email, role)

    try:
        user_data = await user_service.create_user(email=email, password=password, role=role)
        return user_data
    except ValueError as e:
        logger.warning("Ошибка валидации при создании пользователя: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка при создании пользователя %s: %s", email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя",
        ) from e


@router.get(
    "/",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Список всех пользователей",
    description="Возвращает список всех пользователей. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def get_users_endpoint(
    user_service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """Получает список всех пользователей в системе.

    Args:
        _: Пользователь с ролью admin (проверка через зависимость).
        user_service: Сервис пользователей.

    Returns:
        list[UserRead]: Список всех пользователей.

    Raises:
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Получение списка всех пользователей")

    try:
        users_data = await user_service.get_all_users()
        return [UserRead(**user) for user in users_data]
    except Exception as e:
        logger.error("Ошибка при получении списка пользователей: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка пользователей",
        ) from e


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получение пользователя по ID",
    description="Возвращает данные пользователя по его ID. Пользователь может получить только свои данные, администраторы - любые.",
)
async def get_user_endpoint(
    user_id: UUID,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Получает пользователя по ID.

    Пользователь может получить только свои данные.
    Администраторы могут получить данные любого пользователя.

    Args:
        user_id: ID пользователя.
        current_user: Текущий аутентифицированный пользователь.
        user_service: Сервис пользователей.

    Returns:
        UserRead: Модель пользователя.

    Raises:
        HTTPException 403: Если пользователь пытается получить чужие данные.
        HTTPException 404: Если пользователь не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Получение пользователя: id=%s, requester_id=%s", user_id, current_user.id)

    # Проверка прав: пользователь может получить только свои данные, админ - любые
    if current_user.role != UserRole.ADMIN and str(current_user.id) != str(user_id):
        logger.warning(
            "Попытка получить чужие данные: requester_id=%s, target_id=%s",
            current_user.id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для получения данных этого пользователя",
        )

    try:
        user_data = await user_service.get_user_by_id(user_id=user_id)
        if user_data is None:
            logger.warning("Пользователь не найден: id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
        return UserRead(**user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при получении пользователя id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении пользователя",
        ) from e


@router.put(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление роли пользователя",
    description="Обновляет роль пользователя. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def update_user_endpoint(
    user_id: UUID,
    new_role: UserRole,
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """обновляет роль пользователя.

    Args:
        user_id: ID пользователя для обновления.
        new_role: Новая роль пользователя.
            Допустимые значения: 'admin', 'editor', 'viewer'.
        _: Пользователь с ролью admin (проверка через зависимость).
        user_service: Сервис пользователей.

    Returns:
        UserRead: Модель обновленного пользователя.

    Raises:
        HTTPException 404: Если пользователь не найден.
        HTTPException 422: Если роль недопустима.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Обновление пользователя: id=%s, new_role=%s", user_id, new_role)

    try:
        updated = await user_service.update_user_role(user_id=user_id, role=new_role)
        if updated is None:
            logger.warning("Пользователь не найден для обновления: id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
        return updated
    except ValueError as e:
        logger.warning("Ошибка валидации при обновлении пользователя: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при обновлении пользователя id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении пользователя",
        ) from e


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление своего аккаунта",
    description="Удаляет аккаунт текущего пользователя.",
)
async def delete_me_endpoint(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> None:
    """Удаляет аккаунт текущего пользователя.

    Args:
        current_user: Текущий аутентифицированный пользователь.
        user_service: Сервис пользователей.

    Returns:
        None: Возвращает пустой ответ с кодом 204.

    Raises:
        HTTPException 403: Если попытка удалить аккаунт администратора.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Удаление своего аккаунта: id=%s", current_user.id)

    try:
        result = await user_service.delete_user(user_id=current_user.id)
        if not result:
            logger.warning("Пользователь не найден для удаления: id=%s", current_user.id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
    except ValueError as e:
        logger.warning("Ошибка при удалении аккаунта: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка при удалении аккаунта id=%s: %s", current_user.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении аккаунта",
        ) from e


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя",
    description="Удаляет пользователя из системы. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_user_endpoint(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
) -> None:
    """Удаляет пользователя из системы.

    Args:
        user_id: ID пользователя для удаления.
        _: Пользователь с ролью admin (проверка через зависимость).
        user_service: Сервис пользователей.

    Returns:
        None: Возвращает пустой ответ с кодом 204.

    Raises:
        HTTPException 404: Если пользователь не найден.
        HTTPException 403: Если попытка удалить администратора при наличии других пользователей.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Удаление пользователя: id=%s", user_id)

    try:
        result = await user_service.delete_user(user_id=user_id)
        if not result:
            logger.warning("Пользователь не найден для удаления: id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
    except ValueError as e:
        logger.warning("Ошибка при удалении пользователя: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при удалении пользователя id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя",
        ) from e
