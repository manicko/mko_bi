"""Сервис обработки данных.

Предоставляет бизнес-логику для загрузки, обработки и отслеживания статуса
обработки данных для дашбордов.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from mkobi.config import get_config, get_redis_client
from mkobi.core.permissions import check_dashboard_access
from mkobi.core.security import RateLimiter
from mkobi.core.task_queue import enqueue_job
from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.db.session import get_session
from mkobi.data.processing.transformations import (
    apply_transformations,
    calculate_aggregations,
)
from mkobi.models.data import (
    AggregatedData,
    ProcessingConfig,
    ProcessingResult,
    ProcessingStatusResponse,
    UploadResponse,
)
from mkobi.models.processing_logs import ProcessingLogCreate, ProcessingLogUpdate
from mkobi.models.user_roles import (
    MimeTypeEnum,
    ProcessingStatusEnum,
)
from mkobi.models.types import (
    ProcessingResultData,
)
from mkobi.models.enums import UploadMode

logger = logging.getLogger(__name__)

# Rate limiter for upload endpoints
_upload_rate_limiter = RateLimiter(get_redis_client())
_UPLOAD_RATE_LIMIT = 10  # requests
_UPLOAD_RATE_PERIOD = 60  # seconds (1 minute)


def _get_rate_limit_key_for_upload(user_id: int, dashboard_id: UUID) -> str:
    """Generate rate limit key for upload endpoint.

    Args:
        user_id: ID of the user making the request.
        dashboard_id: ID of the dashboard.

    Returns:
        str: Rate limit key.
    """
    return f"rate_limit:upload:{user_id}:{dashboard_id}"


def _validate_mime_type(content_type: str | None) -> None:
    """Валидирует MIME-type загружаемого файла.

    Проверяет, что MIME-type файла входит в список разрешенных
    (text/csv, application/gzip, application/x-gzip).

    Args:
        content_type: MIME-type файла из заголовков запроса.

    Raises:
        ValueError: Если MIME-type не разрешен.
    """
    if content_type is None:
        logger.warning("MIME-type не указан, пропускаем проверку")
        return

    allowed_mime_types = MimeTypeEnum.allowed_values()

    if content_type not in allowed_mime_types:
        logger.error(
            "Недопустимый MIME-type: %s. Допустимые: %s",
            content_type,
            allowed_mime_types,
        )
        raise ValueError(f"Недопустимый MIME-type: {content_type}")

    logger.info("MIME-type успешно проверен: %s", content_type)


def _validate_file(filename: str, file_content: bytes, content_type: str | None = None) -> None:
    """Валидирует загружаемый файл.

    Проверяет MIME-type и формат файла (.csv.gz) и размер (не более 100MB).

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.
        content_type: MIME-type файла из заголовков.

    Raises:
        ValueError: Если файл не соответствует требованиям.
    """
    # 1. Проверка MIME-type (ДОЛЖНО быть первым согласно SPEC.md п.6)
    _validate_mime_type(content_type)

    config = get_config()

    # 2. Проверка формата файла
    allowed_extensions = config.allowed_file_types
    if not any(filename.lower().endswith(ext.lower()) for ext in allowed_extensions):
        logger.error(
            "Недопустимый формат файла: %s. Допустимые: %s",
            filename,
            allowed_extensions,
        )
        raise ValueError(
            f"Недопустимый формат файла: '{filename}'. "
            f"Допустимые форматы: {', '.join(allowed_extensions)}"
        )

    # Проверка размера файла
    max_size = config.max_file_size
    if len(file_content) > max_size:
        logger.error(
            "Файл превышает максимальный размер: %s (%d > %d)",
            filename,
            len(file_content),
            max_size,
        )
        raise ValueError(
            f"Файл '{filename}' превышает максимальный размер "
            f"({len(file_content)} > {max_size} байт)"
        )

    logger.info("Файл успешно валидирован: %s (%d байт)", filename, len(file_content))


def cleanup_task_files(task_id: uuid.UUID) -> None:
    """Удаляет временные файлы задачи.

    Args:
        task_id: ID задачи.
    """
    logger.info("Очистка файлов задачи: task_id=%s", task_id)

    # Ищем файлы, связанные с задачей, во временной директории
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    
    # Ищем файлы, в имени которых есть task_id
    csv_files = list(upload_dir.glob(f"*{task_id}*.csv.gz"))
    
    for file_path in csv_files:
        try:
            file_path.unlink()
            logger.info("Файл удален: %s", file_path)
        except Exception as e:
            logger.error("Ошибка при удалении файла %s: %s", file_path, e)


async def _save_aggregated_data_logic(
    dashboard_id: UUID,
    aggregates: list[dict[str, Any]],
    db: AsyncSession,
) -> int:
    """Внутренняя логика сохранения агрегированных данных с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда.
        aggregates: Список агрегированных данных для сохранения.
        db: Асинхронная сессия базы данных.

    Returns:
        Количество успешно сохраненных записей.
    """
    logger.info(
        "Сохранение агрегированных данных (внутренняя логика): dashboard_id=%s, количество записей: %d",
        dashboard_id,
        len(aggregates),
    )

    # Выполняем операцию в транзакции
    inserted_count: int = await AggregatedDataRepository.bulk_insert(
        db=db,
        dashboard_id=dashboard_id,
        aggregates=aggregates,
        clear_old=True,
    )

    logger.info(
        "Агрегированные данные сохранены для дашборда %s: %d записей",
        dashboard_id,
        inserted_count,
    )
    return inserted_count


async def save_aggregated_data(
    dashboard_id: UUID,
    aggregates: list[dict[str, Any]],
    db: AsyncSession | None = None,
) -> int:
    """Сохраняет агрегированные данные в базу данных.

    Выполняет пакетную вставку агрегированных данных для дашборда.
    Перед вставкой удаляет старые данные для данного дашборда.
    Операция выполняется в транзакции: удаление старых данных и
    вставка новых выполняются атомарно.

    Args:
        dashboard_id: ID дашборда.
        aggregates: Список агрегированных данных для сохранения.
            Каждый элемент должен содержать:
            - graph_id: UUID графика
            - dims: dict[str, Any] значения измерений
            - metrics: dict[str, Any] значения метрик
        db: Опциональная асинхронная сессия базы данных. Если не передана,
            создается новая сессия.

    Returns:
        Количество успешно сохраненных записей.

    Raises:
        ValueError: Если данные невалидны или графики не найдены.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Сохранение агрегированных данных для дашборда %s, количество записей: %d",
        dashboard_id,
        len(aggregates),
    )

    if db is not None:
        return await _save_aggregated_data_logic(dashboard_id, aggregates, db)

    async with get_session() as db_session:
        return await _save_aggregated_data_logic(dashboard_id, aggregates, db_session)


async def _upload_file_logic(
    filename: str,
    file_path: Path,
    content_type: str | None,
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession,
    mode: UploadMode = UploadMode.OVERWRITE,
) -> UploadResponse:
    """Внутренняя логика загрузки файла с использованием переданной сессии.

    Args:
        filename: Имя загружаемого файла.
        file_path: Путь к сохраненному файлу.
        content_type: MIME-type файла из заголовков запроса.
        dashboard_id: ID дашборда.
        user_id: ID пользователя, загружающего файл.
        db: Асинхронная сессия базы данных.

    Returns:
        UploadResponse: Модель с информацией о загрузке.
    """
    # Check rate limit for upload
    rate_limit_key = _get_rate_limit_key_for_upload(user_id, dashboard_id)
    if not _upload_rate_limiter.check_rate_limit(
        rate_limit_key, _UPLOAD_RATE_LIMIT, _UPLOAD_RATE_PERIOD
    ):
        logger.warning(
            "Rate limit exceeded for upload: user_id=%d, dashboard_id=%s",
            user_id,
            dashboard_id,
        )
        raise ValueError("Превышен лимит запросов на загрузку. Попробуйте позже.")

    # Проверяем существование дашборда
    dashboard = await DashboardRepository.get(dashboard_id, db)
    if dashboard is None:
        logger.warning("Дашборд не найден: id=%s", dashboard_id)
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверяем права на запись (editor или admin)
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на загрузку: user_id=%d, dashboard_id=%s",
            user_id,
            dashboard_id,
        )
        raise PermissionError("Недостаточно прав для загрузки файла")

    # Handle upload mode - clear old data if OVERWRITE
    if mode == UploadMode.OVERWRITE:
        await AggregatedDataRepository.delete_by_dashboard(db, dashboard_id)
        logger.info("Cleared old aggregated data for dashboard %s (OVERWRITE mode)", dashboard_id)
    elif mode == UploadMode.APPEND:
        logger.info("Appending to existing data for dashboard %s (APPEND mode)", dashboard_id)
    else:
        logger.warning("Unknown upload mode %s, defaulting to OVERWRITE", mode)
        await AggregatedDataRepository.delete_by_dashboard(db, dashboard_id)

    # Проверка размера файла на диске
    max_size = get_config().max_file_size
    if file_path.stat().st_size > max_size:
        file_path.unlink(missing_ok=True)
        logger.error("Файл превышает максимальный размер: %s", filename)
        raise ValueError(f"Файл '{filename}' превышает максимальный размер")

    # Создание записи лога обработки в БД
    uploaded_at = datetime.now()
    log_create = ProcessingLogCreate(
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.UPLOADED,
        message=f"Файл {filename} успешно загружен",
        started_at=uploaded_at,
    )
    processing_log = await ProcessingLogRepository.create(db, **log_create.model_dump())
    logger.info("Лог обработки создан в БД: id=%s", processing_log.id)

    # Enqueue processing task automatically
    job_id = await enqueue_job(
        "mkobi.workers.data_worker.process_csv_background",
        str(file_path),
        str(processing_log.id),
        str(dashboard_id),
        None,  # processing_config
        job_timeout=3600,
    )

    if job_id:
        logger.info("Processing job enqueued: job_id=%s, log_id=%s", job_id, processing_log.id)
    else:
        # Failed to enqueue, update status to failed
        log_update = ProcessingLogUpdate(
            status=ProcessingStatusEnum.FAILED,
            message="Failed to enqueue processing job",
            finished_at=datetime.now(),
        )
        await ProcessingLogRepository.update(
            db, processing_log.id, **log_update.model_dump(exclude_unset=True)
        )
        raise RuntimeError("Failed to enqueue processing job")

    logger.info(
        "Файл успешно загружен: log_id=%s, filename=%s, mode=%s",
        processing_log.id,
        filename,
        mode,
    )

    return UploadResponse(
        task_id=processing_log.id,
        filename=filename,
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.UPLOADED,
        message="File uploaded successfully, processing started",
        uploaded_at=uploaded_at,
    )


async def upload_file(
    filename: str,
    file_path: Path,
    content_type: str | None,
    dashboard_id: UUID,
    user_id: int,
    mode: UploadMode = UploadMode.OVERWRITE,
    db: AsyncSession | None = None,
) -> UploadResponse:
    """Загружает файл для дашборда.

    Валидирует файл, проверяет права доступа, сохраняет файл
    и создает запись о задаче обработки.

    Args:
        filename: Имя загружаемого файла.
        file_path: Путь к сохраненному файлу.
        content_type: MIME-type файла из заголовков запроса.
        dashboard_id: ID дашборда.
        user_id: ID пользователя, загружающего файл.
        db: Асинхронная сессия базы данных.

    Returns:
        UploadResponse: Модель с информацией о загрузке.

    Raises:
        ValueError: Если файл невалиден или дашборд не найден.
        PermissionError: Если у пользователя нет прав на загрузку.
    """
    logger.info(
        "Начало загрузки файла: filename=%s, file_path=%s, content_type=%s, dashboard_id=%s, user_id=%d",
        filename,
        file_path,
        content_type,
        dashboard_id,
        user_id,
    )

    if db is not None:
        return await _upload_file_logic(filename, file_path, content_type, dashboard_id, user_id, db, mode=mode)

    async with get_session() as db_session:
        async with db_session.begin():
            return await _upload_file_logic(filename, file_path, content_type, dashboard_id, user_id, db_session, mode=mode)
