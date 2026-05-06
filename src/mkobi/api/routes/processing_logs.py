"""Маршруты для работы с логами обработки.

Предоставляет endpoints для просмотра логов обработки данных.
Соответствует требованиям SPEC.md п.14.4 и задаче 011_processing_logs.md.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import get_db_dependency, require_admin_role
from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead
from mkobi.services.processing_log_service import ProcessingLogService

router = APIRouter(prefix="/admin/logs", tags=["admin", "processing_logs"])


@router.get(
    "/",
    response_model=list[ProcessingLogRead],
    summary="Получить список логов обработки",
    description="Получает список логов обработки с фильтрацией и пагинацией. Только для администраторов.",
)
async def get_logs_endpoint(
    dashboard_id: UUID | None = Query(
        None,
        description="Фильтр по ID дашборда",
    ),
    status_filter: ProcessingStatus | None = Query(
        None,
        description="Фильтр по статусу (STARTED, UPLOADED, PROCESSING, SUCCESS, FAILED)",
    ),
    date_from: datetime | None = Query(
        None,
        description="Фильтр по начальной дате (started_at)",
    ),
    date_to: datetime | None = Query(
        None,
        description="Фильтр по конечной дате (started_at)",
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Количество пропускаемых записей для пагинации",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Максимальное количество записей (макс. 1000)",
    ),
    _current_user=Depends(require_admin_role),
    db: AsyncSession = Depends(get_db_dependency),
) -> list[ProcessingLogRead]:
    """Получает список логов обработки с фильтрацией.

    Доступно только для администраторов.
    Поддерживает фильтрацию по dashboard_id, status, date range.
    Сортировка по started_at DESC.
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
        logs: list[ProcessingLogRead] = await ProcessingLogService.get_filtered(
            filters=filters, db=db
        )
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка логов: {str(e)}",
        ) from e


@router.get(
    "/{log_id}",
    response_model=ProcessingLogRead,
    summary="Получить лог по ID",
    description="Получает детали лога обработки по его ID. Только для администраторов.",
)
async def get_log_endpoint(
    log_id: UUID,
    _current_user=Depends(require_admin_role),
    db: AsyncSession = Depends(get_db_dependency),
) -> ProcessingLogRead:
    """Получает лог обработки по его ID.

    Доступно только для администраторов.
    """
    try:
        from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository

        repo = ProcessingLogRepository(db)
        log = await repo.get_by_id(log_id)
        if log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лог обработки не найден",
            )
        return ProcessingLogRead.model_validate(log)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении лога: {str(e)}",
        ) from e
