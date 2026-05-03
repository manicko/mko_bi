"""Маршруты для работы с логами обработки."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from mko_bi.api.deps import get_db, get_current_user_dependency
from mko_bi.core.permissions import check_dashboard_access
from mko_bi.models.processing_logs import (
    ProcessingLogCreate,
    ProcessingLogRead,
    ProcessingLogUpdate,
)
from mko_bi.models.user import UserDB
from mko_bi.services import processing_log_service

router = APIRouter(prefix="/processing-logs", tags=["processing_logs"])

# Делаем зависимости доступными для тестов
get_current_user = get_current_user_dependency


@router.post(
    "/",
    response_model=ProcessingLogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать лог обработки",
    description="Создает новый лог обработки для дашборда.",
)
async def create_log_endpoint(
    log_create: ProcessingLogCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessingLogRead:
    """Создает новый лог обработки.

    Доступно только для пользователей с ролью admin или editor.
    Если указан dashboard_id, проверяется доступ к дашборду.
    """
    # Проверяем права доступа к дашборду, если он указан
    if log_create.dashboard_id is not None:
        has_access = check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=log_create.dashboard_id,
            required_permission="edit",
            db=db,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для создания лога для этого дашборда",
            )

    try:
        log = processing_log_service.create_log(db, log_create)
        return log
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании лога обработки: {str(e)}",
        ) from e


@router.put(
    "/{log_id}/status",
    response_model=ProcessingLogRead,
    summary="Обновить статус лога",
    description="Обновляет статус лога обработки и, при необходимости, сообщение об ошибке.",
)
async def update_log_status_endpoint(
    log_id: UUID,
    status_update: ProcessingLogUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessingLogRead:
    """Обновляет статус лога обработки.

    Доступно только для пользователей с ролью admin или editor.
    Проверяется доступ к дашборду, к которому привязан лог.
    """
    # Получаем лог для проверки доступа
    log = processing_log_service.get_log(db, log_id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лог обработки не найден",
        )

    # Проверяем права доступа к дашборду, если лог к нему привязан
    if log.dashboard_id is not None:
        has_access = check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=log.dashboard_id,
            required_permission="edit",
            db=db,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления лога этого дашборда",
            )

    try:
        updated_log = processing_log_service.update_log_status(db, log_id, status_update)
        if updated_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лог обработки не найден",
            )
        return updated_log
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении лога обработки: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=list[ProcessingLogRead],
    summary="Получить список логов",
    description="Получает список логов обработки с возможностью фильтрации.",
)
async def get_logs_endpoint(
    dashboard_id: UUID | None = Query(
        None,
        description="Фильтр по ID дашборда",
    ),
    status_filter: str | None = Query(
        None,
        description="Фильтр по статусу (started, success, failed)",
    ),
    start_date: datetime | None = Query(
        None,
        description="Фильтр по начальной дате",
    ),
    end_date: datetime | None = Query(
        None,
        description="Фильтр по конечной дате",
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
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProcessingLogRead]:
    """Получает список логов обработки с фильтрацией.

    Доступно только для пользователей с ролью admin или editor.
    Если указан dashboard_id, проверяется доступ к дашборду.
    """
    # Проверяем права доступа к дашборду, если он указан
    if dashboard_id is not None:
        has_access = check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=dashboard_id,
            required_permission="view",
            db=db,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра логов этого дашборда",
            )

    try:
        logs: list[ProcessingLogRead] = processing_log_service.get_logs(
            db,
            dashboard_id=dashboard_id,
            status=status_filter,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
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
    description="Получает лог обработки по его ID.",
)
async def get_log_endpoint(
    log_id: UUID,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessingLogRead:
    """Получает лог обработки по его ID.

    Доступно только для пользователей с ролью admin или editor.
    Проверяется доступ к дашборду, к которому привязан лог.
    """
    log = processing_log_service.get_log(db, log_id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лог обработки не найден",
        )

    # Проверяем права доступа к дашборду, если лог к нему привязан
    if log.dashboard_id is not None:
        has_access = check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=log.dashboard_id,
            required_permission="view",
            db=db,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра лога этого дашборда",
            )

    return log