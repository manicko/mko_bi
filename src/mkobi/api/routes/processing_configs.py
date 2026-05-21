"""Routes for managing processing configuration."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    get_db,
    get_processing_config_service,
    require_editor_role,
    require_viewer_role,
)
from mkobi.models.processing_configs import (
    ProcessingConfigRead,
    ProcessingConfigUpdate,
)
from mkobi.services.processing_config_service import ProcessingConfigService

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
    processing_config_service: ProcessingConfigService = Depends(get_processing_config_service),
) -> ProcessingConfigRead:
    try:
        config = await processing_config_service.get_by_dashboard_id(dashboard_id, db=db)
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing config not found",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting processing config: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting processing config",
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
    processing_config_service: ProcessingConfigService = Depends(get_processing_config_service),
) -> ProcessingConfigRead:
    try:
        if config_update.settings is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Settings cannot be empty",
            )
        config = await processing_config_service.upsert(
            dashboard_id=dashboard_id,
            db=db,
            settings=config_update.settings,
        )
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error updating processing config: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating processing config",
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
    processing_config_service: ProcessingConfigService = Depends(get_processing_config_service),
) -> None:
    try:
        await processing_config_service.delete(dashboard_id, db=db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error deleting processing config: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting processing config",
        ) from e
