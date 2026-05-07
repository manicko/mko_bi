"""Routes for managing processing configuration."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    get_db,
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
) -> ProcessingConfigRead:
    try:
        service = ProcessingConfigService(db=db)
        config = await service.get_by_dashboard_id(dashboard_id)
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
) -> ProcessingConfigRead:
    try:
        if config_update.settings is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Settings cannot be empty",
            )
        service = ProcessingConfigService(db=db)
        config = await service.upsert(
            dashboard_id=dashboard_id,
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
) -> None:
    try:
        service = ProcessingConfigService(db=db)
        await service.delete(dashboard_id)
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
