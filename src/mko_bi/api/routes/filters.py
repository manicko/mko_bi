"""Маршруты для управления глобальными фильтрами.

Этот модуль предоставляет эндпоинты для CRUD операций с фильтрами.
Доступ к операциям создания и удаления ограничен ролями admin,
операции чтения и обновления доступны editor и admin.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from mko_bi.api.deps import (
    get_db,
    require_admin_role,
    require_editor_role,
    CurrentUser,
)
from mko_bi.models.filters import (
    FilterCreate,
    FilterRead,
    FilterUpdate,
)
from mko_bi.services.filter_service import (
    create_filter,
    get_filter,
    get_filters,
    update_filter,
    delete_filter,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/filters", tags=["filters"])


@router.post(
    "/",
    response_model=FilterRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание фильтра",
    description="Создает новый глобальный фильтр. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def create_filter_endpoint(
    filter_data: FilterCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> FilterRead:
    """Создает новый глобальный фильтр.

    Доступно только пользователям с ролью admin.
    Проверяется уникальность имени фильтра.

    Args:
        filter_data: Модель с данными для создания фильтра.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        FilterRead: Модель созданного фильтра.

    Raises:
        HTTPException 409: Если фильтр с таким именем уже существует.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Создание фильтра: name=%s, type=%s, user_id=%s",
        filter_data.name,
        filter_data.type,
        current_user.id,
    )

    try:
        result = create_filter(
            name=filter_data.name,
            type=filter_data.type,
            config=filter_data.config.model_dump(),
            db=db,
        )
        return result
    except ValueError as e:
        logger.warning(
            "Ошибка валидации при создании фильтра: name=%s, error=%s",
            filter_data.name,
            e,
        )
        if "уже существует" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Ошибка при создании фильтра name=%s: %s",
            filter_data.name,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании фильтра",
        ) from e


@router.get(
    "/",
    response_model=list[FilterRead],
    status_code=status.HTTP_200_OK,
    summary="Список фильтров",
    description="Возвращает список всех глобальных фильтров. Доступно editor и admin.",
    dependencies=[Depends(require_editor_role)],
)
async def get_filters_endpoint(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[FilterRead]:
    """Получает список всех глобальных фильтров.

    Доступно пользователям с ролями editor и admin.

    Args:
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        list[FilterRead]: Список моделей фильтров.

    Raises:
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Получение списка фильтров для пользователя: user_id=%s",
        current_user.id,
    )

    try:
        filters: list[FilterRead] = get_filters(db=db)
        logger.info(
            "Получено фильтров для пользователя id=%s: %s",
            current_user.id,
            len(filters),
        )
        return filters
    except Exception as e:
        logger.error(
            "Ошибка при получении списка фильтров для пользователя id=%s: %s",
            current_user.id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка фильтров",
        ) from e


@router.get(
    "/{filter_id}",
    response_model=FilterRead,
    status_code=status.HTTP_200_OK,
    summary="Получение фильтра по ID",
    description="Возвращает данные фильтра по его ID. Доступно editor и admin.",
    dependencies=[Depends(require_editor_role)],
)
async def get_filter_endpoint(
    filter_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> FilterRead:
    """Получает фильтр по ID.

    Доступно пользователям с ролями editor и admin.

    Args:
        filter_id: ID фильтра.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        FilterRead: Модель фильтра.

    Raises:
        HTTPException 404: Если фильтр не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Запрос фильтра: filter_id=%s, user_id=%s",
        filter_id,
        current_user.id,
    )

    try:
        filter_obj = get_filter(filter_id=filter_id, db=db)
        if filter_obj is None:
            logger.warning(
                "Фильтр не найден: filter_id=%s, user_id=%s",
                filter_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Фильтр не найден",
            )
        return filter_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при получении фильтра id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении фильтра",
        ) from e


@router.put(
    "/{filter_id}",
    response_model=FilterRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление фильтра",
    description="Обновляет данные фильтра. Доступно editor и admin.",
    dependencies=[Depends(require_editor_role)],
)
async def update_filter_endpoint(
    filter_id: UUID,
    filter_update: FilterUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> FilterRead:
    """Обновляет данные фильтра.

    Доступно пользователям с ролями editor и admin.

    Args:
        filter_id: ID фильтра для обновления.
        filter_update: Модель с новыми данными.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        FilterRead: Модель обновленного фильтра.

    Raises:
        HTTPException 404: Если фильтр не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Обновление фильтра: filter_id=%s, user_id=%s",
        filter_id,
        current_user.id,
    )

    try:
        updated = update_filter(
            filter_id=filter_id,
            name=filter_update.name,
            type=filter_update.type,
            config=filter_update.config.model_dump() if filter_update.config else None,
            db=db,
        )
        if updated is None:
            logger.warning(
                "Фильтр не найден для обновления: filter_id=%s",
                filter_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Фильтр не найден",
            )
        return updated
    except ValueError as e:
        logger.warning(
            "Ошибка валидации при обновлении фильтра id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при обновлении фильтра id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении фильтра",
        ) from e


@router.delete(
    "/{filter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление фильтра",
    description="Удаляет фильтр. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_filter_endpoint(
    filter_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> None:
    """Удаляет фильтр.

    Доступно только пользователям с ролью admin.

    Args:
        filter_id: ID фильтра для удаления.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Raises:
        HTTPException 404: Если фильтр не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Удаление фильтра: filter_id=%s, user_id=%s",
        filter_id,
        current_user.id,
    )

    try:
        result = delete_filter(filter_id=filter_id, db=db)
        if not result:
            logger.warning(
                "Фильтр не найден для удаления: filter_id=%s",
                filter_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Фильтр не найден",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при удалении фильтра id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении фильтра",
        ) from e