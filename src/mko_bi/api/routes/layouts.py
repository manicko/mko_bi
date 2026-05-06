"""Маршруты для управления layout-ами.

Этот модуль предоставляет эндпоинты для CRUD операций с layout-ами.
Доступ к операциям ограничен и требует аутентификации.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.api.deps import (
    get_db_dependency,
    CurrentUser,
)
from mko_bi.models.layout import (
    LayoutRead,
    LayoutUpdate,
    LayoutCreate,
)
from mko_bi.models.enums import UserRole
from mko_bi.services.layout_service import (
    create_layout,
    get_layout,
    get_all_layouts,
    update_layout,
    delete_layout,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/layouts", tags=["layouts"])


@router.post(
    "/",
    response_model=LayoutRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание layout-а",
    description="Создает новый layout. Доступно только администраторам.",
)
async def create_layout_endpoint(
    layout: LayoutCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> LayoutRead:
    """Создает новый layout.
    
    Args:
        layout: Модель с данными для создания layout-а.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.
    
    Returns:
        LayoutRead: Модель созданного layout-а.
    
    Raises:
        HTTPException 403: Если у пользователя нет прав администратора.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    # Проверка прав администратора
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Нет прав на создание layout-а: user_id=%s, role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут создавать layout-ы",
        )

    logger.info(
        "Создание layout-а: name=%s, user_id=%s",
        layout.name,
        current_user.id,
    )

    try:
        result = await create_layout(
            name=layout.name,
            definition=layout.definition,
            db=db,
        )
        return result
    except ValueError as e:
        logger.warning("Ошибка валидации при создании layout-а: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Ошибка при создании layout-а name=%s: %s",
            layout.name,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании layout-а",
        ) from e


@router.get(
    "/",
    response_model=list[LayoutRead],
    status_code=status.HTTP_200_OK,
    summary="Список доступных layout-ов",
    description="Возвращает список всех layout-ов.",
)
async def get_layouts_endpoint(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[LayoutRead]:
    """Получает список всех layout-ов.
    
    Args:
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.
    
    Returns:
        list[LayoutRead]: Список моделей layout-ов.
    
    Raises:
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Получение списка layout-ов")

    try:
        layouts: list[LayoutRead] = await get_all_layouts(db=db)
        logger.info("Получено layout-ов: %s", len(layouts))
        return layouts
    except Exception as e:
        logger.error("Ошибка при получении списка layout-ов: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка layout-ов",
        ) from e


@router.get(
    "/{layout_id}",
    response_model=LayoutRead,
    status_code=status.HTTP_200_OK,
    summary="Получение layout-а по ID",
    description="Возвращает данные layout-а по его ID.",
)
async def get_layout_endpoint(
    layout_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> LayoutRead:
    """Получает layout по ID.
    
    Args:
        layout_id: ID layout-а.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.
    
    Returns:
        LayoutRead: Модель layout-а.
    
    Raises:
        HTTPException 404: Если layout не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info("Запрос layout-а: layout_id=%s", layout_id)

    try:
        layout = await get_layout(layout_id=layout_id, db=db)
        if layout is None:
            logger.warning("Layout не найден: id=%s", layout_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layout не найден",
            )
        return layout
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при получении layout-а id=%s: %s", layout_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении layout-а",
        ) from e


@router.put(
    "/{layout_id}",
    response_model=LayoutRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление layout-а",
    description="Обновляет данные layout-а. Доступно только администраторам.",
)
async def update_layout_endpoint(
    layout_id: UUID,
    layout_update: LayoutUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> LayoutRead:
    """Обновляет layout.
    
    Доступно только администраторам.
    
    Args:
        layout_id: ID layout-а для обновления.
        layout_update: Модель с новыми данными.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.
    
    Returns:
        LayoutRead: Модель обновленного layout-а.
    
    Raises:
        HTTPException 403: Если у пользователя нет прав администратора.
        HTTPException 404: Если layout не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    # Проверка прав администратора
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Нет прав на обновление layout-а: user_id=%s, role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут обновлять layout-ы",
        )

    logger.info(
        "Обновление layout-а: layout_id=%s, user_id=%s",
        layout_id,
        current_user.id,
    )

    try:
        updated = await update_layout(
            layout_id=layout_id,
            update_data=layout_update,
            db=db,
        )
        if updated is None:
            logger.warning("Layout не найден для обновления: id=%s", layout_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layout не найден",
            )
        return updated
    except ValueError as e:
        logger.warning("Ошибка валидации при обновлении layout-а: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при обновлении layout-а id=%s: %s", layout_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении layout-а",
        ) from e


@router.delete(
    "/{layout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление layout-а",
    description="Удаляет layout. Доступно только администраторам.",
)
async def delete_layout_endpoint(
    layout_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> None:
    """Удаляет layout.
    
    Доступно только администраторам.
    
    Args:
        layout_id: ID layout-а для удаления.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.
    
    Raises:
        HTTPException 403: Если у пользователя нет прав администратора.
        HTTPException 404: Если layout не найден.
        HTTPException 500: При ошибке базы данных.
    """
    # Проверка прав администратора
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Нет прав на удаление layout-а: user_id=%s, role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут удалять layout-ы",
        )

    logger.info(
        "Удаление layout-а: layout_id=%s, user_id=%s",
        layout_id,
        current_user.id,
    )

    try:
        result = await delete_layout(layout_id=layout_id, db=db)
        if not result:
            logger.warning("Layout не найден для удаления: id=%s", layout_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layout не найден",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при удалении layout-а id=%s: %s", layout_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении layout-а",
        ) from e
