"""Маршруты для управления настройками обработки."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_db,
    require_viewer_role,
    require_editor_role,
    CurrentUser,
)
from mkobi.models.processing_configs import (
    ProcessingConfigUpdate,
    ProcessingConfigRead,
)
from mkobi.services.processing_config_service import (
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
    dependencies=[Depends(require_viewer_role)],
)
async def get_config_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProcessingConfigRead:
    try:
        config = await get_by_dashboard_id(dashboard_id=dashboard_id, db=db)
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Настройки обработки не найдены",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения настроек",
        ) from e


@router.put(
    "/{dashboard_id}",
    response_model=ProcessingConfigRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_editor_role)],
)
async def upsert_config_endpoint(
    dashboard_id: UUID,
    config_update: ProcessingConfigUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProcessingConfigRead:
    try:
        if config_update.settings is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Settings cannot be empty",
            )
        config = await upsert(
            dashboard_id=dashboard_id,
            settings=config_update.settings,
            db=db,
        )
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления настроек",
        ) from e


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_editor_role)],
)
async def delete_config_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        success = await delete(dashboard_id=dashboard_id, db=db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Настройки не найдены",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления настроек",
        ) from e
