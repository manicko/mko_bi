"""Маршруты для управления настройками обработки.

Этот модуль предоставляет эндпоинты для работы с настройками обработки данных.
Доступ к операциям чтения доступен viewer и выше,
а к операциям изменения - editor и admin.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mko_b_i.api.deps import (
    get_db,
    require_viewer_role,
    require_editor_role,
    CurrentUser,
)
from mko_b_i.models.processing_configs import (
    ProcessingConfigUpdate,
    ProcessingConfigRead,
)
from mko_b_i.services.processing_config_service import (
    get_by_dashboard_id,
    upsert,
    delete,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing-configs", tags=["processing_configs"])


@router.get(
    "/{dashboard_id}",
    response_model=ProcessingConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Получение настроек обработки",
    description="Возвращает настройки обработки для указанного дашборда. "
                "Доступно пользователям с ролью viewer и выше.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_config_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProcessingConfigRead:
    """Получает настройки обработки для дашборда."""
    logger.info(
        "Запрос настроек обработки: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        config = await get_by_dashboard_id(
            dashboard_id=dashboard_id,
            db=db,
        )
        if config is None:
            logger.warning(
                "Настройки не найдены: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Настройки обработки не найдены или у вас нет доступа",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при получении настроек dashboard_id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении настроек обработки",
        ) from e


@router.put(
    "/{dashboard_id}",
    response_model=ProcessingConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление настроек обработки",
    description="Обновляет (или создает, если не существуют) настройки обработки "
                "для указанного дашборда. Доступно пользователям с ролью editor и admin.",
    dependencies=[Depends(require_editor_role)],
)
async def upsert_config_endpoint(
    dashboard_id: UUID,
    config_update: ProcessingConfigUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProcessingConfigRead:
    """Обновляет настройки обработки для дашборда."""
    logger.info(
        "Обновление настроек обработки: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        if config_update.settings is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Настройки не могут быть пустыми",
            )

        config = await upsert(
            dashboard_id=dashboard_id,
            settings=config_update.settings,
            db=db,
        )
        return config
    except ValueError as e:
        logger.warning("Ошибка валидации при обновлении настроек: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при обновлении настроек dashboard_id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении настроек обработки",
        ) from e


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление настроек обработки",
    description="Удаляет настройки обработки для указанного дашборда. "
                "Доступно пользователям с ролью editor и admin.",
    dependencies=[Depends(require_editor_role)],
)
async def delete_config_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет настройки обработки для дашборда."""
    logger.info(
        "Удаление настроек обработки: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        success = await delete(
            dashboard_id=dashboard_id,
            db=db,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Настройки обработки не найдены",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при удалении настроек dashboard_id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении настроек обработки",
        ) from e
