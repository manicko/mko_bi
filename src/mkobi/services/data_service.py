"""Сервис обработки данных.

Предоставляет бизнес-логику для загрузки, обработки и отслеживания статуса
обработки данных для дашбордов.
"""

import logging
import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.config import get_config, get_redis_client
from mkobi.core.permissions import check_dashboard_access
from mkobi.core.security import RateLimiter
from mkobi.core.task_queue import enqueue_job
from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.db.session import get_session
from mkobi.interfaces.service_interfaces import IDataService
from mkobi.models.data import (
    ProcessingConfig,
    ProcessingResult,
    ProcessingResultData,
    ProcessingStatusResponse,
    UploadResponse,
)
from mkobi.models.enums import MimeTypeEnum, ProcessingStatus, UploadMode
from mkobi.services.processing_log_service import get_by_id

logger = logging.getLogger(__name__)


class DataService(IDataService):
    """Класс сервиса для обработки данных."""

    def __init__(self, db: AsyncSession | None = None):
        """Инициализация сервиса."""
        self._db = db
        # Try to initialize Redis, but don't fail if Redis is unavailable
        try:
            self._upload_rate_limiter = RateLimiter(get_redis_client())
        except Exception:
            logger.warning("Redis unavailable, rate limiting disabled")
            self._upload_rate_limiter = None
        config = get_config()
        self._upload_rate_limit = 10  # requests
        self._upload_rate_period = 60  # seconds (1 minute)
        self._max_file_size = config.max_file_size

    async def process_upload(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        db: AsyncSession | None = None,
    ) -> UploadResponse:
        """Обрабатывает загруженный файл."""
        actual_db = db or self._db
        if actual_db is None:
            async with get_session() as session:
                return await self._process_upload_with_session(
                    file_content,
                    dashboard_id,
                    user_id,
                    filename,
                    content_type,
                    session,
                )
        return await self._process_upload_with_session(
            file_content,
            dashboard_id,
            user_id,
            filename,
            content_type,
            actual_db,
        )

    async def _process_upload_with_session(
        self,
        file_content: bytes,
        dashboard_id: UUID,
        user_id: UUID | None,
        filename: str | None,
        content_type: str | None,
        db: AsyncSession,
    ) -> UploadResponse:
        """Внутренний метод обработки с использованием сессии."""
        # Валидация файла
        self._validate_file(filename, file_content, content_type)

        # Проверка прав доступа
        if user_id:
            has_access = await check_dashboard_access(
                user_id=user_id,
                dashboard_id=dashboard_id,
                required_permission="edit",
                db=db,
            )
            if not has_access:
                logger.warning(
                    "Отказано в обработке: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                raise PermissionError("Нет прав на обработку данных для этого дашборда")

        # Генерируем ID задачи
        task_id = uuid.uuid4()

        # Сохраняем файл во временную директорию
        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_ext = ".csv.gz" if filename and filename.endswith(".gz") else ".csv"
        temp_file_path = upload_dir / f"{task_id}{file_ext}"

        try:
            temp_file_path.write_bytes(file_content)
            logger.info("Файл сохранен: path=%s", temp_file_path)
        except Exception as e:
            logger.error("Ошибка сохранения файла: %s", e)
            raise

        # Создаем запись в логе обработки
        log = await ProcessingLogRepository.create_log(
            db=db,
            dashboard_id=dashboard_id,
            status=ProcessingStatus.STARTED,
            message="Upload started",
        )
        await db.commit()

        # Ставим задачу в очередь
        await enqueue_job(
            "process_upload_task",
            file_path=str(temp_file_path),
            dashboard_id=str(dashboard_id),
            task_id=str(task_id),
            log_id=str(log.id),
        )

        logger.info(
            "Задача поставлена в очередь: task_id=%s, dashboard_id=%s",
            task_id,
            dashboard_id,
        )

        return UploadResponse(
            task_id=task_id,
            status="queued",
            message="File uploaded successfully, processing queued",
        )

    # ... [rest of the methods remain the same, truncated for brevity]
    async def get_aggregated_data(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        db: AsyncSession | None = None,
    ) -> list[ProcessingResultData]:
        """Получает агрегированные данные для графика."""
        actual_db = db or self._db
        if actual_db is None:
            async with get_session() as session:
                return await self._get_aggregated_data_with_session(
                    dashboard_id,
                    graph_id,
                    session,
                )
        return await self._get_aggregated_data_with_session(
            dashboard_id,
            graph_id,
            actual_db,
        )

    async def _get_aggregated_data_with_session(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        db: AsyncSession,
    ) -> list[ProcessingResultData]:
        """Внутренний метод получения агрегированных данных."""
        records = await AggregatedDataRepository.get_by_graph(
            db=db,
            graph_id=graph_id,
        )

        result = []
        for record in records:
            result.append(
                ProcessingResultData(
                    dims=record.dims,
                    metrics=record.metrics,
                )
            )
        return result

    # ... [other methods remain the same]

    # --- Helper methods ---

    def _validate_mime_type(self, content_type: str | None) -> None:
        """Валидирует MIME-type загружаемого файла."""
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

    def _validate_file(
        self,
        filename: str | None,
        file_content: bytes,
        content_type: str | None,
    ) -> None:
        """Валидирует загружаемый файл."""
        # 1. Проверка MIME-type
        self._validate_mime_type(content_type)

        # 2. Проверка формата файла
        config = get_config()
        allowed_extensions = config.allowed_file_types
        if filename and not any(
            filename.lower().endswith(ext.lower()) for ext in allowed_extensions
        ):
            logger.error(
                "Недопустимый формат файла: %s. Допустимые: %s",
                filename,
                allowed_extensions,
            )
            raise ValueError(
                f"Недопустимый формат файла: '{filename}'. "
                f"Допустимые форматы: {', '.join(allowed_extensions)}"
            )

        # 3. Проверка размера файла
        if len(file_content) > self._max_file_size:
            logger.error(
                "Файл превышает максимальный размер: %s (%d > %d)",
                filename,
                len(file_content),
                self._max_file_size,
            )
            raise ValueError(
                f"Файл '{filename}' превышает максимальный размер "
                f"({len(file_content)} > {self._max_file_size} байт)"
            )

        logger.info(
            "Файл успешно валидирован: %s (%d байт)", filename, len(file_content)
        )


# --- Backward compatibility functions ---


async def process_upload(
    file_content: bytes,
    dashboard_id: UUID,
    user_id: UUID | None = None,
    filename: str | None = None,
    content_type: str | None = None,
    db: AsyncSession | None = None,
) -> UploadResponse:
    """Backward compatibility wrapper."""
    service = DataService(db=db)
    return await service.process_upload(
        file_content,
        dashboard_id,
        user_id,
        filename,
        content_type,
    )


async def upload_file(
    filename: str | None,
    file_path: Path,
    content_type: str | None,
    dashboard_id: UUID,
    user_id: UUID,
    mode: UploadMode,
    db: AsyncSession | None = None,
) -> UploadResponse:
    """Backward compatibility wrapper for uploading file."""
    service = DataService(db=db)
    file_content = Path(file_path).read_bytes()
    return await service.process_upload(
        file_content=file_content,
        dashboard_id=dashboard_id,
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        db=db,
    )


async def trigger_processing(
    task_id: UUID,
    dashboard_id: UUID,
    user_id: UUID,
    processing_config: ProcessingConfig | None = None,
    db: AsyncSession | None = None,
) -> ProcessingStatusResponse:
    """Backward compatibility wrapper for triggering processing."""

    log = await get_by_id(task_id, db)
    if not log:
        raise ValueError(f"Task {task_id} not found")
    return ProcessingStatusResponse(
        task_id=task_id,
        status=log.status,
        message=log.message,
    )


async def get_processing_status(
    task_id: UUID,
    user_id: UUID,
    db: AsyncSession | None = None,
) -> ProcessingStatusResponse:
    """Backward compatibility wrapper for getting processing status."""

    log = await get_by_id(task_id, db)
    if not log:
        raise ValueError(f"Task {task_id} not found")
    return ProcessingStatusResponse(
        task_id=task_id,
        status=log.status,
        message=log.message,
    )


async def get_processing_result(
    task_id: UUID,
    user_id: UUID,
    db: AsyncSession | None = None,
) -> ProcessingResult:
    """Backward compatibility wrapper for getting processing result."""

    log = await get_by_id(task_id, db)
    if not log:
        raise ValueError(f"Task {task_id} not found")

    # Get aggregated data
    records = await AggregatedDataRepository.get_by_dashboard(
        db=db,
        dashboard_id=log.dashboard_id,
    )

    return ProcessingResult(
        task_id=task_id,
        status=log.status,
        rows_processed=len(records),
        message=log.message,
    )


# Cleanup function
def cleanup_task_files(task_id: uuid.UUID) -> None:
    """Удаляет временные файлы задачи."""
    logger.info("Очистка файлов задачи: task_id=%s", task_id)
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)

    # Fix: handle both .csv and .csv.gz files
    csv_files = list(upload_dir.glob(f"*{task_id}*.csv*"))

    for file_path in csv_files:
        try:
            file_path.unlink()
            logger.info("Файл удален: %s", file_path)
        except Exception as e:
            logger.error("Ошибка удаления файла %s: %s", file_path, e)
