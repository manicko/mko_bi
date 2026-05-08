"""Routes for managing global filters.

This module provides endpoints for CRUD operations on filters.
Create and delete operations are admin-only.
Read and update operations are available to editors and admins.

Uses FilterService via dependency injection following the project's DI pattern.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_db_dependency,
    get_filter_service,
    require_admin_role,
    require_editor_role,
    CurrentUser,
)
from mkobi.models.filters import (
    FilterCreate,
    FilterRead,
    FilterUpdate,
)
from mkobi.services.filter_service import FilterService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["filters"])


@router.post(
    "/",
    response_model=FilterRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create filter",
    description="Creates a new global filter. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def create_filter_endpoint(
    filter_data: FilterCreate,
    current_user: CurrentUser,
    filter_service: FilterService = Depends(get_filter_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> FilterRead:
    """Create a new global filter.

    Admin-only operation.
    Checks filter name uniqueness.

    Args:
        filter_data: Model with filter creation data.
        current_user: Current authenticated user.
        filter_service: Injected filter service.
        db: Database session.

    Returns:
        FilterRead: Model of the created filter.

    Raises:
        HTTPException 409: If filter with this name already exists.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Creating filter: name=%s, type=%s, user_id=%s",
        filter_data.name,
        filter_data.type,
        current_user.id,
    )

    try:
        result = await filter_service.create_filter(
            name=filter_data.name,
            type_=filter_data.type,
            config=filter_data.config,
            db=db,
        )
        return result
    except ValueError as e:
        logger.warning(
            "Validation error creating filter: name=%s, error=%s",
            filter_data.name,
            e,
        )
        if "already exists" in str(e):
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
            "Error creating filter name=%s: %s",
            filter_data.name,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating filter",
        ) from e


@router.get(
    "/",
    response_model=list[FilterRead],
    status_code=status.HTTP_200_OK,
    summary="List filters",
    description="Returns list of all global filters. Available to editors and admins.",
    dependencies=[Depends(require_editor_role)],
)
async def get_filters_endpoint(
    current_user: CurrentUser,
    filter_service: FilterService = Depends(get_filter_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> list[FilterRead]:
    """Get list of all global filters.

    Available to users with editor and admin roles.

    Args:
        current_user: Current authenticated user.
        filter_service: Injected filter service.
        db: Database session.

    Returns:
        list[FilterRead]: List of filter models.

    Raises:
        HTTPException 500: On database error.
    """
    logger.info(
        "Getting filter list for user: user_id=%s",
        current_user.id,
    )

    try:
        filters: list[FilterRead] = await filter_service.get_all_filters(db=db)
        logger.info(
            "Retrieved filters for user id=%s: %s",
            current_user.id,
            len(filters),
        )
        return filters
    except Exception as e:
        logger.error(
            "Error getting filter list for user id=%s: %s",
            current_user.id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting filter list",
        ) from e


@router.get(
    "/{filter_id}",
    response_model=FilterRead,
    status_code=status.HTTP_200_OK,
    summary="Get filter by ID",
    description="Returns filter data by ID. Available to editors and admins.",
    dependencies=[Depends(require_editor_role)],
)
async def get_filter_endpoint(
    filter_id: UUID,
    current_user: CurrentUser,
    filter_service: FilterService = Depends(get_filter_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> FilterRead:
    """Get filter by ID.

    Available to users with editor and admin roles.

    Args:
        filter_id: Filter ID.
        current_user: Current authenticated user.
        filter_service: Injected filter service.
        db: Database session.

    Returns:
        FilterRead: Filter model.

    Raises:
        HTTPException 404: If filter not found.
        HTTPException 500: On database error.
    """
    logger.info(
        "Filter request: filter_id=%s, user_id=%s",
        filter_id,
        current_user.id,
    )

    try:
        filter_obj = await filter_service.get_filter_by_id(filter_id=filter_id, db=db)
        if filter_obj is None:
            logger.warning(
                "Filter not found: filter_id=%s, user_id=%s",
                filter_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filter not found",
            )
        return filter_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting filter id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting filter",
        ) from e


@router.put(
    "/{filter_id}",
    response_model=FilterRead,
    status_code=status.HTTP_200_OK,
    summary="Update filter",
    description="Updates filter data. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def update_filter_endpoint(
    filter_id: UUID,
    filter_update: FilterUpdate,
    current_user: CurrentUser,
    filter_service: FilterService = Depends(get_filter_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> FilterRead:
    """Update filter data.

    Admin-only operation.

    Args:
        filter_id: Filter ID to update.
        filter_update: Model with new data.
        current_user: Current authenticated user.
        filter_service: Injected filter service.
        db: Database session.

    Returns:
        FilterRead: Model of the updated filter.

    Raises:
        HTTPException 404: If filter not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    logger.info(
        "Updating filter: filter_id=%s, user_id=%s",
        filter_id,
        current_user.id,
    )

    try:
        updated = await filter_service.update_filter(
            filter_id=filter_id,
            updates=filter_update,
            db=db,
        )
        if updated is None:
            logger.warning(
                "Filter not found for update: filter_id=%s",
                filter_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filter not found",
            )
        return updated
    except ValueError as e:
        logger.warning(
            "Validation error updating filter id=%s: %s",
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
            "Error updating filter id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating filter",
        ) from e


@router.delete(
    "/{filter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete filter",
    description="Deletes a filter. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_filter_endpoint(
    filter_id: UUID,
    current_user: CurrentUser,
    filter_service: FilterService = Depends(get_filter_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> None:
    """Delete filter.

    Admin-only operation.

    Args:
        filter_id: Filter ID to delete.
        current_user: Current authenticated user.
        filter_service: Injected filter service.
        db: Database session.

    Raises:
        HTTPException 404: If filter not found.
        HTTPException 500: On database error.
    """
    logger.info(
        "Deleting filter: filter_id=%s, user_id=%s",
        filter_id,
        current_user.id,
    )

    try:
        result = await filter_service.delete_filter(filter_id=filter_id, db=db)
        if not result:
            logger.warning(
                "Filter not found for deletion: filter_id=%s",
                filter_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filter not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting filter id=%s: %s",
            filter_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting filter",
        ) from e
