"""Сервис обработки данных.

Предоставляет бизнес-логику для загрузки, обработки и отслеживания статуса
обработки данных для дашбордов.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import Float, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.utils import secure_filename

from mko_bi.config import get_config, get_redis_client
from mko_bi.core.permissions import check_dashboard_access
from mko_bi.core.security import RateLimiter
from mko_bi.core.task_queue import enqueue_job
from mko_bi.data.loaders.loader import CSVLoader
from mko_bi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.processing_log_repo import ProcessingLogRepository
from mko_bi.db.session import get_session
from mko_bi.data.processing.transformations import (
    apply_transformations,
    calculate_aggregations,
)
from mko_bi.models.data import (
    AggregatedData,
    ProcessingConfig,
    ProcessingResult,
    ProcessingStatusResponse,
    UploadResponse,
)
from mko_bi.models.processing_logs import ProcessingLogCreate, ProcessingLogUpdate
from mko_bi.models.user_roles import (
    MimeTypeEnum,
    ProcessingStatusEnum,
)
from mko_bi.models.types import (
    ProcessingResultData,
)

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
    allowed_extensions = [ext.value for ext in config.allowed_file_types]
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


def _save_uploaded_file(filename: str, file_content: bytes, dashboard_id: UUID | None = None) -> Path:
    """Сохраняет загруженный файл во временную директорию.

    Выполняет валидацию пути для защиты от directory traversal атак.
    Использует secure_filename для очистки имени файла и Path.resolve()
    для проверки, что путь находится в разрешенной директории.

    Args:
        filename: Имя файла.
        file_content: Содержимое файла.
        dashboard_id: Опциональный ID дашборда для идентификации файла.

    Returns:
        Path: Путь к сохраненному файлу.

    Raises:
        ValueError: Если путь содержит попытку directory traversal.
    """
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    resolved_upload_dir = upload_dir.resolve()

    # Очистка имени файла от недопустимых символов
    secured_filename = secure_filename(filename)

    # Генерируем уникальное имя файла с учетом dashboard_id для поиска
    if dashboard_id:
        unique_filename = f"{uuid.uuid4()}_{dashboard_id}_{secured_filename}"
    else:
        unique_filename = f"{uuid.uuid4()}_{secured_filename}"

    file_path = upload_dir / unique_filename

    # Проверка, что путь находится в разрешенной директории (защита от directory traversal)
    resolved_file_path = file_path.resolve()
    if not str(resolved_file_path).startswith(str(resolved_upload_dir)):
        logger.error("Обнаружена попытка directory traversal: %s", filename)
        raise ValueError(f"Недопустимый путь к файлу: {filename}")

    with open(file_path, "wb") as f:
        f.write(file_content)

    logger.info("Файл сохранен: %s", file_path)
    return file_path


def _process_csv_file_sync(
    file_path: Path,
    processing_config: ProcessingConfig | None = None,
) -> ProcessingResultData:
    """Synchronous processing of CSV file using Polars.

    This function is called via asyncio.to_thread() to avoid blocking the event loop.
    """
    logger.info("Начало обработки файла: %s", file_path)

    # Чтение файла через CSVLoader
    loader = CSVLoader()
    df = loader.load_csv(file_path)

    logger.info("Файл прочитан: %d строк, %d колонок", df.shape[0], df.shape[1])

    # Применяем обработку если задана конфигурация
    if processing_config:
        logger.info("Применение конфигурации обработки")

        # Применяем трансформации (фильтры, сортировка, лимит, базовая группировка)
        df = apply_transformations(
            df,
            filters=processing_config.filters,
            groupby=processing_config.groupby if not processing_config.aggregations else None,
            sort_by=processing_config.sort_by,
            descending=processing_config.descending,
            limit=processing_config.limit,
        )

        # Применяем агрегации, YoY, доли, кастомные метрики
        if (
            processing_config.aggregations
            or processing_config.yoy_config
            or processing_config.share_config
            or processing_config.custom_metrics
        ):
            df = calculate_aggregations(
                df,
                groupby=processing_config.groupby,
                aggregations=processing_config.aggregations,
                yoy_config=processing_config.yoy_config,
                share_config=processing_config.share_config,
                custom_metrics=processing_config.custom_metrics,
            )

    # Формируем результат
    result_data: ProcessingResultData = {
        "columns": df.columns,
        "rows": df.shape[0],
        "preview": df.head(10).to_dicts(),
        "processed_rows": df.shape[0],
        "processed_columns": df.columns,
    }

    logger.info("Обработка завершена: %d строк", df.shape[0])

    return result_data


async def _process_csv_file(
    file_path: Path,
    processing_config: ProcessingConfig | None = None,
    dashboard_id: UUID | None = None,
    db: AsyncSession | None = None,
) -> ProcessingResultData:
    """Обрабатывает CSV файл с использованием Polars.

    Читает gzipped CSV файл через CSVLoader, применяет трансформации и агрегации.
    При передаче dashboard_id и db сохраняет агрегированные данные в БД.

    Args:
        file_path: Путь к файлу.
        processing_config: Конфигурация обработки.
        dashboard_id: Опциональный ID дашборда для сохранения агрегатов.
        db: Опциональная сессия базы данных для сохранения агрегатов.

    Returns:
        ProcessingResultData: Результаты обработки.
    """
    return await asyncio.to_thread(
        _process_csv_file_sync,
        file_path,
        processing_config,
    )


async def _upload_file_logic(
    filename: str,
    file_content: bytes,
    content_type: str | None,
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession,
) -> UploadResponse:
    """Внутренняя логика загрузки файла с использованием переданной сессии.

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.
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

    # Валидация файла (включая MIME-type)
    _validate_file(filename, file_content, content_type)

    # Сохранение файла
    _save_uploaded_file(filename, file_content, dashboard_id)

    # Создание задачи
    uploaded_at = datetime.now()

    # Создаем запись лога обработки в БД
    log_create = ProcessingLogCreate(
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.uploaded,
        message=f"Файл {filename} успешно загружен",
        started_at=uploaded_at,
    )
    processing_log = await ProcessingLogRepository.create(db, **log_create.model_dump())
    logger.info("Лог обработки создан в БД: id=%s", processing_log.id)

    task_id = processing_log.id  # Используем ID лога как task_id

    logger.info("Файл успешно загружен: task_id=%s, filename=%s", task_id, filename)

    return UploadResponse(
        task_id=task_id,
        filename=filename,
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.uploaded,
        message="File uploaded successfully",
        uploaded_at=uploaded_at,
    )


async def upload_file(
    filename: str,
    file_content: bytes,
    content_type: str | None,
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession | None = None,
) -> UploadResponse:
    """Загружает файл для дашборда.

    Валидирует файл (включая MIME-type), сохраняет его во временную директорию
    и создает запись о задаче обработки.

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.
        content_type: MIME-type файла из заголовков запроса.
        dashboard_id: ID дашборда.
        user_id: ID пользователя, загружающего файл.
        db: Асинхронная сессия базы данных.

    Returns:
        UploadResponse: Модель с информацией о загрузке.

    Raises:
        ValueError: Если файл не валиден или дашборд не найден.
        PermissionError: Если у пользователя нет прав на загрузку.
    """
    logger.info(
        "Начало загрузки файла: filename=%s, content_type=%s, dashboard_id=%s, user_id=%d",
        filename,
        content_type,
        dashboard_id,
        user_id,
    )

    if db is not None:
        return await _upload_file_logic(filename, file_content, content_type, dashboard_id, user_id, db)

    async with get_session() as db_session:
        async with db_session.begin():
            return await _upload_file_logic(filename, file_content, content_type, dashboard_id, user_id, db_session)


async def _trigger_processing_logic(
    task_id: uuid.UUID,
    dashboard_id: UUID,
    user_id: int,
    processing_config: ProcessingConfig | None,
    db: AsyncSession,
) -> ProcessingStatusResponse:
    """Внутренняя логика запуска обработки с использованием переданной сессии.

    Args:
        task_id: ID задачи загрузки.
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        processing_config: Конфигурация обработки.
        db: Асинхронная сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.
    """
    logger.info(
        "Запуск обработки (внутренняя логика): task_id=%s, dashboard_id=%s, user_id=%d",
        task_id,
        dashboard_id,
        user_id,
    )

    # Проверка прав доступа
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на обработку: user_id=%d, dashboard_id=%s",
            user_id,
            dashboard_id,
        )
        raise PermissionError("Недостаточно прав для обработки данных")

    # Проверяем, есть ли лог обработки для этого дашборда
    logs = await ProcessingLogRepository.get_by_dashboard_and_status(
        db, dashboard_id, [ProcessingStatusEnum.uploaded, ProcessingStatusEnum.processing]
    )

    if not logs:
        logger.warning("Задача не найдена: dashboard_id=%s", dashboard_id)
        raise ValueError(f"Задача для дашборда с id={dashboard_id} не найдена")

    # Берем последний лог
    processing_log = logs[-1]

    # Проверяем статус
    if processing_log.status in [ProcessingStatusEnum.processing, ProcessingStatusEnum.success]:
        logger.warning(
            "Невозможно запустить обработку: задача уже %s", processing_log.status
        )
        raise ValueError(f"Задача уже находится в статусе '{processing_log.status}'")

    # Обновление статуса в логе (до начала обработки)
    started_at = datetime.now()
    log_update = ProcessingLogUpdate(
        status=ProcessingStatusEnum.processing,
        message="Запуск обработки задачи (background)",
        started_at=started_at,
    )
    await ProcessingLogRepository.update(
        db, processing_log.id, **log_update.model_dump(exclude_unset=True)
    )
    logger.info("Обработка запущена: log_id=%s", processing_log.id)

    # Находим файл для обработки
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)

    # Ищем файлы для этого дашборда
    csv_files = list(upload_dir.glob(f"*_{dashboard_id}_*.csv.gz"))
    if not csv_files:
        # Ищем любые недавние CSV файлы
        csv_files = list(upload_dir.glob("*.csv.gz"))
        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not csv_files:
        raise FileNotFoundError(f"Файл для дашборда {dashboard_id} не найден")

    file_path = csv_files[0]

    # Подготавливаем конфигурацию для передачи в RQ worker
    processing_config_dict = None
    if processing_config:
        processing_config_dict = processing_config.model_dump(exclude_none=True)

    # Enqueue job to RQ for background processing
    job_id = enqueue_job(
        "mko_bi.workers.data_worker.process_csv_background",
        str(file_path),
        str(task_id),
        str(dashboard_id),
        processing_config_dict,
        job_timeout=3600,  # 1 hour timeout for large files
    )

    if job_id:
        logger.info("Job enqueued to RQ: job_id=%s, task_id=%s", job_id, task_id)
    else:
        # Failed to enqueue, update status to failed
        log_update = ProcessingLogUpdate(
            status=ProcessingStatusEnum.failed,
            message="Failed to enqueue job to RQ",
            finished_at=datetime.now(),
        )
        await ProcessingLogRepository.update(
            db, processing_log.id, **log_update.model_dump(exclude_unset=True)
        )
        raise RuntimeError("Failed to enqueue processing job")

    # Получаем имя файла из сообщения лога
    filename = "unknown"
    if processing_log.message and "Файл" in processing_log.message:
        try:
            filename = processing_log.message.split("Файл ")[-1].split(" успешно")[0]
        except (IndexError, AttributeError):
            filename = file_path.name

    logger.info(
        "Обработка запущена в фоне: dashboard_id=%s, task_id=%s",
        dashboard_id,
        task_id,
    )

    return ProcessingStatusResponse(
        task_id=task_id,
        filename=filename,
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.processing,
        progress=0,
        message="Processing started in background",
        started_at=started_at,
        completed_at=None,
    )


async def trigger_processing(
    task_id: uuid.UUID,
    dashboard_id: UUID,
    user_id: int,
    processing_config: ProcessingConfig | None = None,
    db: AsyncSession | None = None,
) -> ProcessingStatusResponse:
    """Запускает обработку загруженного файла.

    Args:
        task_id: ID задачи загрузки.
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        processing_config: Конфигурация обработки.
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.

    Raises:
        ValueError: Если задача не найдена или уже обработана.
        PermissionError: Если у пользователя нет прав.
    """
    logger.info(
        "Запуск обработки: task_id=%s, dashboard_id=%s, user_id=%d",
        task_id,
        dashboard_id,
        user_id,
    )

    if db is not None:
        return await _trigger_processing_logic(task_id, dashboard_id, user_id, processing_config, db)

    async with get_session() as db_session:
        async with db_session.begin():
            return await _trigger_processing_logic(task_id, dashboard_id, user_id, processing_config, db_session)


async def _get_processing_status_logic(
    task_id: uuid.UUID,
    user_id: int,
    db: AsyncSession,
) -> ProcessingStatusResponse:
    """Внутренняя логика получения статуса обработки с использованием переданной сессии.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя (для проверки прав).
        db: Асинхронная сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.
    """
    logger.info("Запрос статуса (внутренняя логика): task_id=%s, user_id=%d", task_id, user_id)

    # Получаем лог напрямую по task_id (является ID лога)
    task_log = await ProcessingLogRepository.get(task_id, db)
    if task_log is None:
        logger.warning("Задача не найдена: task_id=%s", task_id)
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверка прав доступа к дашборду
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=task_log.dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на просмотр статуса: user_id=%d, dashboard_id=%s",
            user_id,
            task_log.dashboard_id,
        )
        raise PermissionError("Недостаточно прав для просмотра статуса")

    # Извлекаем имя файла из сообщения
    filename = "unknown"
    if task_log.message and "Файл" in task_log.message:
        try:
            filename = task_log.message.split("Файл ")[-1].split(" успешно")[0]
        except (IndexError, AttributeError):
            filename = "unknown"

    logger.info(
        "Статус получен: task_id=%s, status=%s", task_id, task_log.status
    )

    return ProcessingStatusResponse(
        task_id=task_id,
        filename=filename,
        dashboard_id=task_log.dashboard_id,
        status=ProcessingStatusEnum(task_log.status),
        progress=100 if task_log.status == ProcessingStatusEnum.success else 0,
        message=task_log.message or "",
        started_at=task_log.started_at,
        completed_at=task_log.finished_at,
    )


async def get_processing_status(
    task_id: uuid.UUID,
    user_id: int,
    db: AsyncSession | None = None,
) -> ProcessingStatusResponse:
    """Получает статус обработки.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя (для проверки прав).
        db: Асинхронная сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.

    Raises:
        ValueError: Если задача не найдена.
    """
    logger.info("Запрос статуса: task_id=%s, user_id=%d", task_id, user_id)

    if db is not None:
        return await _get_processing_status_logic(task_id, user_id, db)

    async with get_session() as db_session:
        return await _get_processing_status_logic(task_id, user_id, db_session)


async def _get_processing_result_logic(
    task_id: uuid.UUID,
    user_id: int,
    db: AsyncSession,
) -> ProcessingResult:
    """Внутренняя логика получения результата обработки с использованием переданной сессии.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.

    Returns:
        ProcessingResult: Результат обработки.
    """
    logger.info("Запрос результата (внутренняя логика): task_id=%s, user_id=%d", task_id, user_id)

    # Получаем лог напрямую по task_id (ID лога)
    task_log = await ProcessingLogRepository.get(task_id, db)
    if task_log is None:
        logger.warning("Задача не найдена: task_id=%s", task_id)
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверка прав доступа
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=task_log.dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на просмотр результата: user_id=%d, dashboard_id=%s",
            user_id,
            task_log.dashboard_id,
        )
        raise PermissionError("Недостаточно прав для просмотра результата")

    # Проверка статуса
    if task_log.status != "success":
        logger.warning(
            "Задача не завершена: task_id=%s, status=%s",
            task_id,
            task_log.status,
        )
        raise ValueError(f"Задача не завершена (статус: {task_log.status})")

    # Получаем агрегированные данные
    aggregates = await AggregatedDataRepository.get_by_dashboard(
        db, task_log.dashboard_id
    )

    result_data = {
        "rows": len(aggregates) if aggregates else 0,
        "dashboard_id": task_log.dashboard_id,
    }

    logger.info("Результат получен: task_id=%s", task_id)

    return ProcessingResult(
        success=True,
        task_id=task_id,
        dashboard_id=task_log.dashboard_id,
        rows_processed=result_data.get("rows", 0),
        message=task_log.message or "Processing completed",
        data=result_data,
    )


async def get_processing_result(
    task_id: uuid.UUID,
    user_id: int,
    db: AsyncSession | None = None,
) -> ProcessingResult:
    """Получает результат обработки.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.

    Returns:
        ProcessingResult: Результат обработки.

    Raises:
        ValueError: Если задача не найдена или не завершена.
        PermissionError: Если у пользователя нет прав.
    """
    logger.info("Запрос результата: task_id=%s, user_id=%d", task_id, user_id)

    if db is not None:
        return await _get_processing_result_logic(task_id, user_id, db)

    async with get_session() as db_session:
        return await _get_processing_result_logic(task_id, user_id, db_session)


async def _get_dashboard_aggregates_logic(
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[AggregatedData]]:
    """Внутренняя логика получения агрегатов дашборда с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.
        limit: Максимальное количество записей (по умолчанию 100).
        offset: Смещение (по умолчанию 0).

    Returns:
        Кортеж (общее количество записей, список агрегированных данных для всех графиков дашборда).
    """
    logger.info(
        "Получение агрегатов дашборда (внутренняя логика): dashboard_id=%s, user_id=%s, limit=%d, offset=%d",
        dashboard_id,
        user_id,
        limit,
        offset,
    )

    # Проверка существования дашборда и прав доступа
    dashboard_obj = await DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверка прав доступа
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("У вас нет доступа к этому дашборду")

    # Получение всех графиков дашборда
    from sqlalchemy import select
    from mko_bi.db.models import (
        graphs as graphs_model,
    )

    graphs = (
        await db.execute(
            select(graphs_model.Graph).where(
                graphs_model.Graph.dashboard_id == dashboard_id
            )
        )
    ).scalars().all()

    # Получение пагинированных агрегированных данных
    total, agg_data = await AggregatedDataRepository.get_by_dashboard(
        db, dashboard_id, limit, offset
    )

    # Группировка данных по графику
    result = []
    for graph in graphs:
        # Фильтруем данные для текущего графика
        graph_agg = [agg for agg in agg_data if agg.graph_id == graph.id]
        if not graph_agg:
            continue

        graph_data = []
        for agg in graph_agg:
            graph_data.append({
                "dims": agg.dims,
                "metrics": agg.metrics,
            })

        result.append(
            AggregatedData(
                dashboard_id=dashboard_id,
                chart_type=graph.type,
                data=graph_data,
                metadata={
                    "graph_id": str(graph.id),
                    "graph_name": graph.name,
                    "count": len(graph_data),
                },
            )
        )

    logger.info(
        "Агрегаты получены: dashboard_id=%s, charts_count=%s, total=%d",
        dashboard_id,
        len(result),
        total,
    )
    return total, result


async def get_dashboard_aggregates(
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[AggregatedData]]:
    """Получает все агрегированные данные для дашборда с пагинацией.

    Возвращает все агрегаты (данные для всех графиков) указанного дашборда.
    Проверяет права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        db: Опциональная асинхронная сессия базы данных.
        limit: Максимальное количество записей (по умолчанию 100).
        offset: Смещение (по умолчанию 0).

    Returns:
        Кортеж (общее количество записей, список агрегированных данных для всех графиков дашборда).

    Raises:
        ValueError: Если дашборд не найден или у пользователя нет доступа.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Получение агрегатов дашборда: dashboard_id=%s, user_id=%s, limit=%d, offset=%d",
        dashboard_id,
        user_id,
        limit,
        offset,
    )

    if db is not None:
        return await _get_dashboard_aggregates_logic(dashboard_id, user_id, db, limit, offset)

    async with get_session() as db_session:
        return await _get_dashboard_aggregates_logic(dashboard_id, user_id, db_session, limit, offset)


async def _get_chart_data_logic(
    dashboard_id: UUID,
    user_id: int,
    chart_ids: list[UUID] | None,
    db: AsyncSession,
) -> list[AggregatedData]:
    """Внутренняя логика получения данных для графиков с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        chart_ids: Опциональный список ID графиков для фильтрации.
        db: Асинхронная сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для запрошенных графиков.
    """
    logger.info(
        "Получение данных для графиков (внутренняя логика): dashboard_id=%s, chart_ids=%s, user_id=%s",
        dashboard_id,
        chart_ids,
        user_id,
    )

    # Проверка существования дашборда и прав доступа
    dashboard_obj = await DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверка прав доступа
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("У вас нет доступа к этому дашборду")

    # Формирование запроса для графиков
    from sqlalchemy import select
    from mko_bi.db.models import (
        aggregated_data as aggregated_data_model,
        graphs as graphs_model,
    )

    query = select(graphs_model.Graph).where(
        graphs_model.Graph.dashboard_id == dashboard_id
    )

    if chart_ids:
        query = query.where(graphs_model.Graph.id.in_(chart_ids))

    graphs = list((await db.execute(query)).scalars().all())

    if chart_ids and len(graphs) != len(chart_ids):
        found_ids = {str(g.id) for g in graphs}
        missing_ids = [str(cid) for cid in chart_ids if str(cid) not in found_ids]
        raise ValueError(f"Графики не найдены: {', '.join(missing_ids)}")

    if not graphs:
        return []

    # Получение агрегированных данных для графиков
    result = []
    for graph in graphs:
        aggregates = (
            await db.execute(
                select(aggregated_data_model.AggregatedData).where(
                    aggregated_data_model.AggregatedData.graph_id == graph.id
                )
            )
        ).scalars().all()

        graph_data = []
        for agg in aggregates:
            graph_data.append({
                "dims": agg.dims,
                "metrics": agg.metrics,
            })

        if graph_data:
            result.append(
                AggregatedData(
                    dashboard_id=dashboard_id,
                    chart_type=graph.type,
                    data=graph_data,
                    metadata={
                        "graph_id": str(graph.id),
                        "graph_name": graph.name,
                        "count": len(graph_data),
                    },
                )
            )

    logger.info(
        "Данные для графиков получены: dashboard_id=%s, charts_count=%s",
        dashboard_id,
        len(result),
    )
    return result


async def get_chart_data(
    dashboard_id: UUID,
    user_id: int,
    chart_ids: list[UUID] | None = None,
    db: AsyncSession | None = None,
) -> list[AggregatedData]:
    """Получает данные для конкретных графиков дашборда.

    Если chart_ids не указан, возвращает данные для всех графиков дашборда.
    Проверяет права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        chart_ids: Опциональный список ID графиков для фильтрации.
        db: Опциональная асинхронная сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для запрошенных графиков.

    Raises:
        ValueError: Если дашборд или графики не найдены, или у пользователя нет доступа.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Получение данных для графиков: dashboard_id=%s, chart_ids=%s, user_id=%s",
        dashboard_id,
        chart_ids,
        user_id,
    )

    if db is not None:
        return await _get_chart_data_logic(dashboard_id, user_id, chart_ids, db)

    async with get_session() as db_session:
        return await _get_chart_data_logic(dashboard_id, user_id, chart_ids, db_session)


async def _apply_data_filters_logic(
    dashboard_id: UUID,
    user_id: int,
    filters: dict[str, Any] | None,
    db: AsyncSession,
) -> list[AggregatedData]:
    """Внутренняя логика применения фильтров с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        filters: Словарь с параметрами фильтрации.
        db: Асинхронная сессия базы данных.

    Returns:
        list[AggregatedData]: Отфильтрованные агрегированные данные.
    """
    logger.info(
        "Применение фильтров (внутренняя логика): dashboard_id=%s, filters=%s, user_id=%s",
        dashboard_id,
        filters,
        user_id,
    )

    # Проверка существования дашборда и прав доступа
    dashboard_obj = await DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверка прав доступа
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("У вас нет доступа к этому дашборду")

    from sqlalchemy import and_, select

    from mko_bi.db.models import (
        aggregated_data as aggregated_data_model,
        graphs as graphs_model,
    )

    # Получение всех графиков дашборда
    graphs = (
        await db.execute(
            select(graphs_model.Graph).where(
                graphs_model.Graph.dashboard_id == dashboard_id
            )
        )
    ).scalars().all()

    result = []
    for graph in graphs:
        # Формирование условий фильтрации
        filter_conditions = []

        # Фильтрация по году
        if filters and "year" in filters and filters["year"] is not None:
            filter_conditions.append(
                aggregated_data_model.AggregatedData.dims["year"].astext.cast(
                    Integer
                )
                == filters["year"]
            )

        # Фильтрация по категории
        if filters and "category" in filters and filters["category"] is not None:
            filter_conditions.append(
                aggregated_data_model.AggregatedData.dims["category"].astext
                == filters["category"]
            )

        # Фильтрация по бренду
        if filters and "brand" in filters and filters["brand"] is not None:
            filter_conditions.append(
                aggregated_data_model.AggregatedData.dims["brand"].astext
                == filters["brand"]
            )

        # Дополнительные фильтры из словаря
        if (
            filters
            and "filters" in filters
            and isinstance(filters["filters"], dict)
        ):
            for key, value in filters["filters"].items():
                if isinstance(value, str):
                    filter_conditions.append(
                        aggregated_data_model.AggregatedData.dims[key].astext
                        == value
                    )
                elif isinstance(value, (int, float)):
                    filter_conditions.append(
                        aggregated_data_model.AggregatedData.dims[key].astext.cast(
                            Float
                        )
                        == value
                    )

        # Формирование запроса с фильтрами
        query = select(aggregated_data_model.AggregatedData).where(
            aggregated_data_model.AggregatedData.graph_id == graph.id
        )

        if filter_conditions:
            query = query.where(and_(*filter_conditions))

        aggregates = list((await db.execute(query)).scalars().all())

        # Формирование результата
        graph_data = []
        for agg in aggregates:
            graph_data.append({
                "dims": agg.dims,
                "metrics": agg.metrics,
            })

        if graph_data:
            result.append(
                AggregatedData(
                    dashboard_id=dashboard_id,
                    chart_type=graph.type,
                    data=graph_data,
                    metadata={
                        "graph_id": str(graph.id),
                        "graph_name": graph.name,
                        "count": len(graph_data),
                        "filters_applied": filters,
                    },
                )
            )

    logger.info(
        "Фильтры применены: dashboard_id=%s, filtered_charts=%s",
        dashboard_id,
        len(result),
    )
    return result


async def apply_data_filters(
    dashboard_id: UUID,
    user_id: int,
    filters: dict[str, Any] | None = None,
    db: AsyncSession | None = None,
) -> list[AggregatedData]:
    """Применяет фильтры к агрегированным данным дашборда.

    Фильтрует данные по году, категории, бренду и другим параметрам,
    используя возможности PostgreSQL для фильтрации JSONB данных.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        filters: Словарь с параметрами фильтрации.
        db: Опциональная асинхронная сессия базы данных.

    Returns:
        list[AggregatedData]: Отфильтрованные агрегированные данные.

    Raises:
        ValueError: Если дашборд не найден, у пользователя нет доступа или фильтры некорректны.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Применение фильтров: dashboard_id=%s, filters=%s, user_id=%s",
        dashboard_id,
        filters,
        user_id,
    )

    if db is not None:
        return await _apply_data_filters_logic(dashboard_id, user_id, filters, db)

    async with get_session() as db_session:
        return await _apply_data_filters_logic(dashboard_id, user_id, filters, db_session)


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
