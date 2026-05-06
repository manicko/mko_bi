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
from mkobi.models.data import (
    ProcessingConfig,
    ProcessingResult,
    ProcessingResultData,
    ProcessingStatusResponse,
    UploadResponse,
)
from mkobi.models.processing_logs import ProcessingLogCreate, ProcessingLogUpdate
from mkobi.models.enums import UploadMode
from mkobi.models.enums import MimeTypeEnum, ProcessingStatusEnum
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


async def trigger_processing(
    task_id: UUID,
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession,
    processing_config: ProcessingConfig | None = None,
) -> ProcessingStatusResponse:
    """Запускает обработку загруженного файла.

    Args:
        task_id: ID задачи (processing_log.id).
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.
        processing_config: Конфигурация обработки (опционально).

    Returns:
        ProcessingStatusResponse: Статус обработки.

    Raises:
        ValueError: Если задача не найдена.
        PermissionError: Если у пользователя нет прав.
    """
    from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository

    # Проверяем существование задачи
    processing_log = await ProcessingLogRepository.get(task_id, db)
    if processing_log is None:
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверяем, что задача принадлежит указанному дашборду
    if processing_log.dashboard_id != dashboard_id:
        raise ValueError(f"Задача не принадлежит дашборду {dashboard_id}")

    # Проверяем права на запись (требуется editor или admin)
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    )
    if not has_access:
        raise PermissionError("Недостаточно прав для запуска обработки")

    # Если задача уже в процессе или завершена, не запускаем повторно
    if processing_log.status in [ProcessingStatusEnum.PROCESSING, ProcessingStatusEnum.SUCCESS, ProcessingStatusEnum.COMPLETED]:
        logger.info("Задача уже обрабатывается или завершена: task_id=%s, status=%s", task_id, processing_log.status)
        return ProcessingStatusResponse(
            task_id=processing_log.id,
            filename=processing_log.message.replace("Файл ", "").replace(" успешно загружен", ""),
            dashboard_id=processing_log.dashboard_id,
            status=processing_log.status,
            progress=100 if processing_log.status in [ProcessingStatusEnum.SUCCESS, ProcessingStatusEnum.COMPLETED] else 0,
            message=processing_log.message,
            started_at=processing_log.started_at,
            completed_at=processing_log.finished_at,
        )

    # Обновляем статус на processing
    from mkobi.db.repositories.processing_log_repo import ProcessingLogUpdate
    log_update = ProcessingLogUpdate(
        status=ProcessingStatusEnum.PROCESSING,
        message="Запуск обработки данных",
    )
    await ProcessingLogRepository.update(db, task_id, **log_update.model_dump(exclude_unset=True))

    # Получаем путь к файлу (если он еще существует)
    config = get_config()
    temp_dir = Path(config.upload_temp_dir)
    
    # Ищем файл, связанный с этой задачей
    file_path = None
    try:
        files = list(temp_dir.glob(f"*{task_id}*.csv*"))
        if files:
            file_path = files[0]
    except Exception as e:
        logger.warning("Не удалось найти файл для задачи %s: %s", task_id, e)

    # Если файл найден, обрабатываем его через воркер
    if file_path and file_path.exists():
        from mkobi.core.task_queue import enqueue_job
        
        processing_config_dict = None
        if processing_config:
            processing_config_dict = processing_config.model_dump(exclude_none=True)

        job_id = await enqueue_job(
            "mkobi.workers.data_worker.process_csv_background",
            str(file_path),
            str(task_id),
            str(dashboard_id),
            processing_config_dict,
            job_timeout=3600,
        )

        if not job_id:
            logger.error("Не удалось запланировать задачу обработки для task_id=%s", task_id)
            log_update = ProcessingLogUpdate(
                status=ProcessingStatusEnum.FAILED,
                message="Не удалось запланировать задачу обработки",
                finished_at=datetime.now(),
            )
            await ProcessingLogRepository.update(db, task_id, **log_update.model_dump(exclude_unset=True))
            raise RuntimeError("Не удалось запланировать задачу обработки")

        logger.info("Задача обработки запланирована: job_id=%s, task_id=%s", job_id, task_id)
    else:
        # Если файла нет, обновляем статус
        log_update = ProcessingLogUpdate(
            status=ProcessingStatusEnum.FAILED,
            message="Файл для обработки не найден",
            finished_at=datetime.now(),
        )
        await ProcessingLogRepository.update(db, task_id, **log_update.model_dump(exclude_unset=True))
        logger.warning("Файл для обработки не найден: task_id=%s", task_id)

    # Возвращаем обновленный статус
    updated_log = await ProcessingLogRepository.get(task_id, db)
    return ProcessingStatusResponse(
        task_id=updated_log.id,
        filename=updated_log.message.replace("Файл ", "").replace(" успешно загружен", ""),
        dashboard_id=updated_log.dashboard_id,
        status=updated_log.status,
        progress=50 if updated_log.status == ProcessingStatusEnum.PROCESSING else 0,
        message=updated_log.message,
        started_at=updated_log.started_at,
        completed_at=updated_log.finished_at,
    )


async def get_processing_status(
    task_id: UUID,
    user_id: int,
    db: AsyncSession,
) -> ProcessingStatusResponse:
    """Получает текущий статус обработки.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.

    Returns:
        ProcessingStatusResponse: Статус обработки.

    Raises:
        ValueError: Если задача не найдена.
        PermissionError: Если у пользователя нет прав.
    """
    from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository

    processing_log = await ProcessingLogRepository.get(task_id, db)
    if processing_log is None:
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверяем, что пользователь имеет доступ к дашборду
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=processing_log.dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("Нет прав на просмотр статуса этой задачи")

    # Вычисляем прогресс
    progress = 0
    if processing_log.status == ProcessingStatusEnum.UPLOADED:
        progress = 10
    elif processing_log.status == ProcessingStatusEnum.PROCESSING:
        progress = 50
    elif processing_log.status in [ProcessingStatusEnum.SUCCESS, ProcessingStatusEnum.COMPLETED]:
        progress = 100
    elif processing_log.status == ProcessingStatusEnum.FAILED:
        progress = 0

    return ProcessingStatusResponse(
        task_id=processing_log.id,
        filename=processing_log.message.replace("Файл ", "").replace(" успешно загружен", ""),
        dashboard_id=processing_log.dashboard_id,
        status=processing_log.status,
        progress=progress,
        message=processing_log.message,
        started_at=processing_log.started_at,
        completed_at=processing_log.finished_at,
    )


async def get_processing_result(
    task_id: UUID,
    user_id: int,
    db: AsyncSession,
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
    from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
    from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository

    processing_log = await ProcessingLogRepository.get(task_id, db)
    if processing_log is None:
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверяем, что пользователь имеет доступ к дашборду
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=processing_log.dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("Нет прав на просмотр результата этой задачи")

    # Проверяем, что обработка завершена успешно
    if processing_log.status not in [ProcessingStatusEnum.SUCCESS, ProcessingStatusEnum.COMPLETED]:
        raise ValueError(f"Обработка еще не завершена или завершилась с ошибкой. Статус: {processing_log.status}")

    # Получаем агрегированные данные
    aggregates = await AggregatedDataRepository.get_by_dashboard(processing_log.dashboard_id, db)

    # Формируем результат
    result_data = ProcessingResultData(
        columns=list(set([col for agg in aggregates for col in agg.dims.keys()] + [col for agg in aggregates for col in agg.metrics.keys()])),
        rows=len(aggregates),
    )

    return ProcessingResult(
        success=True,
        task_id=task_id,
        dashboard_id=processing_log.dashboard_id,
        rows_processed=len(aggregates),
        message="Обработка завершена успешно",
        data=result_data,
    )


async def _process_csv_file(
    file_path: Path,
    config: dict[str, Any] | ProcessingConfig | None = None,
) -> dict[str, Any]:
    """Обрабатывает CSV файл и возвращает результат.

    Используется для тестирования и синхронной обработки.

    Args:
        file_path: Путь к CSV файлу.
        config: Конфигурация обработки (опционально).

    Returns:
        dict: Результат обработки.
    """
    from mkobi.data.loaders.loader import CSVLoader
    from mkobi.data.processing.transformations import apply_transformations, calculate_aggregations
    from mkobi.models.data import ProcessingConfig

    loader = CSVLoader()
    df = loader.load_csv(file_path)

    result = {
        "columns": df.columns,
        "rows": df.shape[0],
    }

    if config:
        if isinstance(config, ProcessingConfig):
            processing_config = config
        else:
            processing_config = ProcessingConfig(**config)

        # Применяем трансформации
        df = apply_transformations(
            df,
            filters=processing_config.filters,
            groupby=processing_config.groupby if not processing_config.aggregations else None,
            sort_by=processing_config.sort_by,
            descending=processing_config.descending,
            limit=processing_config.limit,
        )

        # Применяем агрегации
        if processing_config.aggregations or processing_config.yoy_config or processing_config.share_config or processing_config.custom_metrics:
            df = calculate_aggregations(
                df,
                groupby=processing_config.groupby,
                aggregations=processing_config.aggregations,
                yoy_config=processing_config.yoy_config,
                share_config=processing_config.share_config,
                custom_metrics=processing_config.custom_metrics,
            )

        result["processed_rows"] = df.shape[0]
    else:
        result["processed_rows"] = df.shape[0]

    return result


async def get_dashboard_aggregates(
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Получает агрегированные данные для дашборда.

    Args:
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.
        limit: Максимальное количество записей.
        offset: Смещение для пагинации.

    Returns:
        dict: Словарь с данными и метаданными.

    Raises:
        ValueError: Если дашборд не найден.
        PermissionError: Если у пользователя нет прав.
    """
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository

    # Проверяем существование дашборда
    dashboard = await DashboardRepository.get(dashboard_id, db)
    if dashboard is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверяем права на чтение
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("Нет прав на чтение этого дашборда")

    # Получаем агрегированные данные
    aggregates = await AggregatedDataRepository.get_by_dashboard(
        dashboard_id=dashboard_id,
        db=db,
        limit=limit,
        offset=offset,
    )

    # Получаем графики для дашборда
    from mkobi.db.repositories.graph_repo import GraphRepository
    graphs = await GraphRepository.get_by_dashboard(dashboard_id, db)

    # Формируем ответ
    charts = []
    for graph in graphs:
        chart_data = {
            "graph_id": str(graph.id),
            "name": graph.name,
            "type": graph.type,
            "config": graph.config,
            "dimensions": graph.dimensions,
            "metrics": graph.metrics,
        }
        charts.append(chart_data)

    return {
        "dashboard_id": str(dashboard_id),
        "charts": charts,
        "aggregates": [
            {
                "id": str(agg.id),
                "graph_id": str(agg.graph_id),
                "dims": agg.dims,
                "metrics": agg.metrics,
            }
            for agg in aggregates
        ],
        "total": len(aggregates),
        "limit": limit,
        "offset": offset,
    }


async def get_chart_data(
    dashboard_id: UUID,
    user_id: int,
    db: AsyncSession,
) -> dict[str, Any]:
    """Получает данные для графиков дашборда.

    Args:
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.

    Returns:
        dict: Словарь с данными для графиков.

    Raises:
        ValueError: Если дашборд не найден.
        PermissionError: Если у пользователя нет прав.
    """
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
    from mkobi.db.repositories.graph_repo import GraphRepository

    # Проверяем существование дашборда
    dashboard = await DashboardRepository.get(dashboard_id, db)
    if dashboard is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверяем права на чтение
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("Нет прав на чтение этого дашборда")

    # Получаем графики
    graphs = await GraphRepository.get_by_dashboard(dashboard_id, db)

    # Получаем агрегированные данные
    aggregates = await AggregatedDataRepository.get_by_dashboard(dashboard_id, db)

    # Группируем данные по графикам
    charts = []
    for graph in graphs:
        graph_aggregates = [a for a in aggregates if str(a.graph_id) == str(graph.id)]
        charts.append({
            "graph_id": str(graph.id),
            "name": graph.name,
            "type": graph.type,
            "data": [
                {
                    "dims": agg.dims,
                    "metrics": agg.metrics,
                }
                for agg in graph_aggregates
            ],
        })

    return {
        "dashboard_id": str(dashboard_id),
        "charts": charts,
        "total": len(aggregates),
    }


async def apply_data_filters(
    dashboard_id: UUID,
    filters: list[dict[str, Any]],
    user_id: int,
    db: AsyncSession,
) -> dict[str, Any]:
    """Применяет фильтры к агрегированным данным дашборда.

    Args:
        dashboard_id: ID дашборда.
        filters: Список фильтров.
        user_id: ID пользователя.
        db: Асинхронная сессия базы данных.

    Returns:
        dict: Отфильтрованные данные.

    Raises:
        ValueError: Если дашборд не найден.
        PermissionError: Если у пользователя нет прав.
    """
    from mkobi.db.repositories.dashboard_repo import DashboardRepository
    from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository

    # Проверяем существование дашборда
    dashboard = await DashboardRepository.get(dashboard_id, db)
    if dashboard is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверяем права на чтение
    has_access = await check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("Нет прав на чтение этого дашборда")

    # Получаем агрегированные данные
    aggregates = await AggregatedDataRepository.get_by_dashboard(dashboard_id, db)

    # Применяем фильтры
    filtered_aggregates = []
    for agg in aggregates:
        match = True
        for filter_item in filters:
            field = filter_item.get("field")
            operator = filter_item.get("operator", "==")
            value = filter_item.get("value")

            if field in agg.dims:
                field_value = agg.dims[field]
            elif field in agg.metrics:
                field_value = agg.metrics[field]
            else:
                match = False
                break

            if operator == "==":
                if field_value != value:
                    match = False
                    break
            elif operator == "!=":
                if field_value == value:
                    match = False
                    break
            elif operator == ">":
                if not (field_value > value):
                    match = False
                    break
            elif operator == "<":
                if not (field_value < value):
                    match = False
                    break
            elif operator == ">=":
                if not (field_value >= value):
                    match = False
                    break
            elif operator == "<=":
                if not (field_value <= value):
                    match = False
                    break

        if match:
            filtered_aggregates.append(agg)

    return {
        "dashboard_id": str(dashboard_id),
        "aggregates": [
            {
                "id": str(agg.id),
                "graph_id": str(agg.graph_id),
                "dims": agg.dims,
                "metrics": agg.metrics,
            }
            for agg in filtered_aggregates
        ],
        "total": len(filtered_aggregates),
        "filters_applied": len(filters),
    }


