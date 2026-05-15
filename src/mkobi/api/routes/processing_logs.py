"""Routes for processing log operations.

Provides endpoints for viewing data processing logs.
Complies with SPEC.md section 14.4 and task 011_processing_logs.md.
"""

from datetime import datetime
from uuid import UUID
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_db_dependency,
    get_processing_log_repository,
    get_processing_log_service,
    require_admin_role,
)
from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead
from mkobi.services.processing_log_service import ProcessingLogService

router = APIRouter(prefix="/admin/logs", tags=["admin", "processing_logs"])


@router.get(
    "/",
    response_model=list[ProcessingLogRead],
    summary="Get processing logs",
    description="Returns list of processing logs with filtering and pagination. Admin only.",
)
async def get_logs_endpoint(
    dashboard_id: UUID | None = Query(
        None,
        description="Filter by dashboard ID",
    ),
    status_filter: ProcessingStatus | None = Query(
        None,
        description="Filter by status (STARTED, UPLOADED, PROCESSING, SUCCESS, FAILED)",
    ),
    date_from: datetime | None = Query(
        None,
        description="Filter by start date (started_at)",
    ),
    date_to: datetime | None = Query(
        None,
        description="Filter by end date (started_at)",
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip for pagination",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records (max. 1000)",
    ),
    _current_user=Depends(require_admin_role),
    db: AsyncSession = Depends(get_db_dependency),
    log_service: ProcessingLogService = Depends(get_processing_log_service),
) -> list[ProcessingLogRead]:
    """Get list of processing logs with filtering.

    Admin-only operation.
    Supports filtering by dashboard_id, status, date range.
    Sorted by started_at DESC.
    """
    try:
        filters = ProcessingLogFilter(
            dashboard_id=dashboard_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
        )
        logs: list[ProcessingLogRead] = await log_service.get_filtered(
            filters=filters, db=db
        )
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting log list: {str(e)}",
        ) from e


@router.get(
    "/{log_id}",
    response_model=ProcessingLogRead,
    summary="Get log by ID",
    description="Returns processing log details by ID. Admin only.",
)
async def get_log_endpoint(
    log_id: UUID,
    _current_user=Depends(require_admin_role),
    db: AsyncSession = Depends(get_db_dependency),
) -> ProcessingLogRead:
    """Get processing log by ID.

    Admin-only operation.
    """
    try:
        repo = get_processing_log_repository()
        log = await repo.get_by_id(log_id, db)
        if log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing log not found",
            )
        return cast(ProcessingLogRead, ProcessingLogRead.model_validate(log))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting log: {str(e)}",
        ) from e