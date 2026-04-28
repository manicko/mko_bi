"""Маршруты для управления настройками обработки.

Этот модуль предоставляет эндпоинты для работы с настройками обработки данных.
Доступ к операциям чтения доступен viewer и выше,
а к операциям изменения - editor и admin.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from mko_bi.api.deps import (
    get_db,
    require_viewer_role,
    require_editor_role,
    CurrentUser,
)
from mko_bi.models.processing_configs import (
    ProcessingConfigUpdate,
    ProcessingConfigRead,
)
from mko_bi.services.processing_config_service import (
    create_or_update_config,
    get_config,
    update_config,
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
    db: Session = Depends(get_db),
) -> ProcessingConfigRead:
    """Получает настройки обработки для дашборда.

    Проверяет права доступа пользователя и возвращает настройки обработки,
    если у пользователя есть доступ к дашборду.

    Args:
        dashboard_id: Идентификатор дашборда.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        ProcessingConfigRead: Модель настроек обработки.

    Raises:
        HTTPException 403: Если у пользователя нет прав на чтение.
        HTTPException 404: Если настройки не найдены.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Запрос настроек обработки: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        config = get_config(
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            db=db,
        )
        if config is None:
            logger.warning(
                "Настройки не найдены или нет доступа: dashboard_id=%s, user_id=%s",
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
async def update_config_endpoint(
    dashboard_id: UUID,
    config_update: ProcessingConfigUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProcessingConfigRead:
    """Обновляет настройки обработки для дашборда.

    Если настройки для дашборда еще не существуют, они будут созданы.
    Проверяет права доступа пользователя (требуется роль editor или admin).

    Args:
        dashboard_id: Идентификатор дашборда.
        config_update: Модель с новыми настройками.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        ProcessingConfigRead: Модель обновленных настроек обработки.

    Raises:
        HTTPException 403: Если у пользователя нет прав на изменение.
        HTTPException 404: Если дашборд не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Обновление настроек обработки: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        # Проверяем, что настройки переданы
        if config_update.settings is None:
            logger.warning(
                "Пустые настройки: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Настройки не могут быть пустыми",
            )

        config = update_config(
            dashboard_id=dashboard_id,
            settings=config_update.settings,
            user_id=current_user.id,
            db=db,
        )
        if config is None:
            # Проверяем, существует ли дашборд
            from mko_bi.services.dashboard_service import get_dashboard
            
            dashboard = get_dashboard(
                dashboard_id=dashboard_id,
                user_id=current_user.id,
                db=db,
            )
            
            if dashboard is None:
                logger.warning(
                    "Дашборд не найден: dashboard_id=%s",
                    dashboard_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Дашборд не найден",
                )
            
            # Если дашборд существует, но нет прав - пробуем создать
            try:
                config = create_or_update_config(
                    dashboard_id=dashboard_id,
                    settings=config_update.settings,
                    db=db,
                )
            except ValueError as e:
                logger.warning(
                    "Ошибка валидации при создании настроек: %s",
                    e,
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(e),
                ) from e

        return config
    except ValueError as e:
        logger.warning(
            "Ошибка валидации при обновлении настроек: %s",
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
            "Ошибка при обновлении настроек dashboard_id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении настроек обработки",
        ) from e