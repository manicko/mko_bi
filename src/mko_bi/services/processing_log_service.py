"""Сервис для работы с логами обработки.

Предоставляет бизнес-логику для создания, обновления и чтения логов обработки.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from mko_bi.db.repositories.processing_log_repo import ProcessingLogRepository
from mko_bi.models.processing_logs import (
    ProcessingLogCreate,
    ProcessingLogRead,
    ProcessingLogUpdate,
)

logger = logging.getLogger(__name__)


def create_log(
    db: Session,
    log_create: ProcessingLogCreate,
) -> ProcessingLogRead:
    """Создает новый лог обработки.

    Args:
        db: Сессия базы данных.
        log_create: Данные для создания лога.

    Returns:
        ProcessingLogRead: Созданный лог.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Создание лога обработки: dashboard_id=%s, status=%s",
        log_create.dashboard_id,
        log_create.status,
    )

    log_obj = ProcessingLogRepository.create(db, **log_create.model_dump())
    logger.info("Лог обработки создан: id=%s", log_obj.id)

    return ProcessingLogRead.model_validate(log_obj)


def update_log_status(
    db: Session,
    log_id: UUID,
    status_update: ProcessingLogUpdate,
) -> ProcessingLogRead | None:
    """Обновляет статус лога обработки.

    Args:
        db: Сессия базы данных.
        log_id: ID лога.
        status_update: Данные для обновления.

    Returns:
        ProcessingLogRead: Обновленный лог или None, если не найден.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Обновление лога обработки: id=%s", log_id)

    update_data = status_update.model_dump(exclude_unset=True)

    # Автоматически устанавливаем finished_at, если статус success или failed
    if status_update.status in ["success", "failed"] and "finished_at" not in update_data:
        update_data["finished_at"] = datetime.now()

    log_obj = ProcessingLogRepository.update(db, log_id, **update_data)

    if log_obj:
        logger.info(
            "Лог обработки обновлен: id=%s, status=%s",
            log_id,
            status_update.status,
        )
        return ProcessingLogRead.model_validate(log_obj)
    else:
        logger.warning("Лог обработки не найден для обновления: id=%s", log_id)
        return None


def get_log(
    db: Session,
    log_id: UUID,
) -> ProcessingLogRead | None:
    """Получает лог обработки по ID.

    Args:
        db: Сессия базы данных.
        log_id: ID лога.

    Returns:
        ProcessingLogRead: Найденный лог или None.
    """
    log_obj = ProcessingLogRepository.get(db, log_id)

    if log_obj:
        return ProcessingLogRead.model_validate(log_obj)
    else:
        logger.warning("Лог обработки не найден: id=%s", log_id)
        return None


def get_logs(
    db: Session,
    dashboard_id: UUID | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ProcessingLogRead]:
    """Получает список логов обработки с фильтрацией.

    Args:
        db: Сессия базы данных.
        dashboard_id: Фильтр по ID дашборда (опционально).
        status: Фильтр по статусу (опционально).
        start_date: Фильтр по начальной дате (опционально).
        end_date: Фильтр по конечной дате (опционально).
        skip: Количество пропускаемых записей для пагинации.
        limit: Максимальное количество записей для возврата.

    Returns:
        list[ProcessingLogRead]: Список логов.
    """
    # Получаем все логи через репозиторий
    all_logs = ProcessingLogRepository.get_all(db)

    # Применяем фильтры
    filtered_logs = all_logs

    if dashboard_id is not None:
        filtered_logs = [
            log for log in filtered_logs
            if log.dashboard_id == dashboard_id
        ]

    if status is not None:
        filtered_logs = [
            log for log in filtered_logs
            if log.status == status
        ]

    if start_date is not None:
        filtered_logs = [
            log for log in filtered_logs
            if log.started_at is not None and log.started_at >= start_date
        ]

    if end_date is not None:
        filtered_logs = [
            log for log in filtered_logs
            if log.started_at is not None and log.started_at <= end_date
        ]

    # Сортируем по started_at (новые сначала)
    filtered_logs.sort(
        key=lambda log: log.started_at or log.finished_at or datetime.min,
        reverse=True,
    )

    # Применяем пагинацию
    paginated_logs = filtered_logs[skip:skip + limit]

    logger.info(
        "Получен список логов обработки: dashboard_id=%s, status=%s, count=%d",
        dashboard_id,
        status,
        len(paginated_logs),
    )

    return [ProcessingLogRead.model_validate(log) for log in paginated_logs]
