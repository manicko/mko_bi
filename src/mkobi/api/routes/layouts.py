"""Routes for managing layouts.

This module provides endpoints for CRUD operations on layouts.
Access is restricted and requires authentication.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_db_dependency,
    CurrentUser,
)
from mkobi.models.layout import (
    LayoutRead,
    LayoutUpdate,
    LayoutCreate,
)
from mkobi.models.enums import UserRole
from mkobi.services.layout_service import (
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
    summary="Create layout",
    description="Creates a new layout. Admin only.",
)
async def create_layout_endpoint(
    layout: LayoutCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> LayoutRead:
    """Create a new layout.

    Args:
        layout: Model with layout creation data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        LayoutRead: Model of the created layout.

    Raises:
        HTTPException 403: If user is not an admin.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    # Check admin permissions
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Insufficient permissions to create layout: user_id=%s, role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create layouts",
        )

    logger.info(
        "Creating layout: name=%s, user_id=%s",
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
        logger.warning("Validation error creating layout: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Error creating layout name=%s: %s",
            layout.name,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating layout",
        ) from e


@router.get(
    "/",
    response_model=list[LayoutRead],
    status_code=status.HTTP_200_OK,
    summary="List layouts",
    description="Returns list of all layouts.",
)
async def get_layouts_endpoint(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[LayoutRead]:
    """Get list of all layouts.

    Args:
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        list[LayoutRead]: List of layout models.

    Raises:
        HTTPException 500: On database error.
    """
    logger.info("Getting layout list")

    try:
        layouts: list[LayoutRead] = await get_all_layouts(db=db)
        logger.info("Retrieved layouts: %s", len(layouts))
        return layouts
    except Exception as e:
        logger.error("Error getting layout list: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting layout list",
        ) from e


@router.get(
    "/{layout_id}",
    response_model=LayoutRead,
    status_code=status.HTTP_200_OK,
    summary="Get layout by ID",
    description="Returns layout data by ID.",
)
async def get_layout_endpoint(
    layout_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> LayoutRead:
    """Get layout by ID.

    Args:
        layout_id: Layout ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        LayoutRead: Layout model.

    Raises:
        HTTPException 404: If layout not found.
        HTTPException 500: On database error.
    """
    logger.info("Layout request: layout_id=%s", layout_id)

    try:
        layout = await get_layout(layout_id=layout_id, db=db)
        if layout is None:
            logger.warning("Layout not found: id=%s", layout_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layout not found",
            )
        return layout
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting layout id=%s: %s", layout_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting layout",
        ) from e


@router.put(
    "/{layout_id}",
    response_model=LayoutRead,
    status_code=status.HTTP_200_OK,
    summary="Update layout",
    description="Updates layout data. Admin only.",
)
async def update_layout_endpoint(
    layout_id: UUID,
    layout_update: LayoutUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> LayoutRead:
    """Update layout.

    Admin-only operation.

    Args:
        layout_id: Layout ID to update.
        layout_update: Model with new data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        LayoutRead: Model of the updated layout.

    Raises:
        HTTPException 403: If user is not an admin.
        HTTPException 404: If layout not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    # Check admin permissions
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Insufficient permissions to update layout: user_id=%s, role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update layouts",
        )

    logger.info(
        "Updating layout: layout_id=%s, user_id=%s",
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
            logger.warning("Layout not found for update: id=%s", layout_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layout not found",
            )
        return updated
    except ValueError as e:
        logger.warning("Validation error updating layout: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating layout id=%s: %s", layout_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating layout",
        ) from e


@router.delete(
    "/{layout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete layout",
    description="Deletes a layout. Admin only.",
)
async def delete_layout_endpoint(
    layout_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> None:
    """Delete layout.

    Admin-only operation.

    Args:
        layout_id: Layout ID to delete.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException 403: If user is not an admin.
        HTTPException 404: If layout not found.
        HTTPException 500: On database error.
    """
    # Check admin permissions
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Insufficient permissions to delete layout: user_id=%s, role=%s",
            current_user.id,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete layouts",
        )

    logger.info(
        "Deleting layout: layout_id=%s, user_id=%s",
        layout_id,
        current_user.id,
    )

    try:
        result = await delete_layout(layout_id=layout_id, db=db)
        if not result:
            logger.warning("Layout not found for deletion: id=%s", layout_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layout not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting layout id=%s: %s", layout_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting layout",
        ) from e
