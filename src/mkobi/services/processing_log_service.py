"""Сервис для работы с логами обработки.

Предоставляет бизнес-логику для создания, обновления и чтения логов обработки.
Все методы асинхронные, соответствуют требованиям задачи 011_processing_logs.md.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.models.enums import ProcessingStatusEnum
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead

logger = logging.getLogger(__name__)


class ProcessingLogService:
    """Сервис для бизнес-логики логов обработки.

    Предоставляет методы для управления жизненным циклом логов обработки данных.
    Вызывается из DataPipeline на каждом этапе обработки.
    """

    @staticmethod
    async def create_started_log(
        dashboard_id: UUID | None, db: AsyncSession
    ) -> ProcessingLogRead:
        """Создать лог со статусом STARTED.

        Args:
            dashboard_id: Идентификатор дашборда (опционально).
            db: Асинхронная сессия базы данных.

        Returns:
            Созданный лог в формате Pydantic модели.
        """
        logger.info(
            "Создание лога STARTED: dashboard_id=%s",
            dashboard_id,
        )
        repo = ProcessingLogRepository(db)
        log = await repo.create_log(
            dashboard_id=dashboard_id,
            status=ProcessingStatusEnum.STARTED,
            message="Processing started",
        )
        return ProcessingLogRead.model_validate(log)

    @staticmethod
    async def update_to_uploaded(
        log_id: UUID, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Обновить статус лога на UPLOADED.

        Args:
            log_id: Идентификатор лога.
            db: Асинхронная сессия базы данных.

        Returns:
            Обновленный лог или None, если не найден.
        """
        logger.info("Обновление лога на UPLOADED: log_id=%s", log_id)
        repo = ProcessingLogRepository(db)
        await repo.update_status(
            log_id=log_id,
            status=ProcessingStatusEnum.UPLOADED,
            message="File uploaded successfully",
        )
        log = await repo.get_by_id(log_id)
        return ProcessingLogRead.model_validate(log) if log else None

    @staticmethod
    async def update_to_processing(
        log_id: UUID, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Обновить статус лога на PROCESSING.

        Args:
            log_id: Идентификатор лога.
            db: Асинхронная сессия базы данных.

        Returns:
            Обновленный лог или None, если не найден.
        """
        logger.info("Обновление лога на PROCESSING: log_id=%s", log_id)
        repo = ProcessingLogRepository(db)
        await repo.update_status(
            log_id=log_id,
            status=ProcessingStatusEnum.PROCESSING,
            message="Processing data",
        )
        log = await repo.get_by_id(log_id)
        return ProcessingLogRead.model_validate(log) if log else None

    @staticmethod
    async def update_to_success(
        log_id: UUID, message: str | None, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Обновить статус лога на SUCCESS.

        Args:
            log_id: Идентификатор лога.
            message: Сообщение об успешном завершении (опционально).
            db: Асинхронная сессия базы данных.

        Returns:
            Обновленный лог или None, если не найден.
        """
        logger.info("Обновление лога на SUCCESS: log_id=%s", log_id)
        repo = ProcessingLogRepository(db)
        await repo.update_status(
            log_id=log_id,
            status=ProcessingStatusEnum.SUCCESS,
            message=message or "Processing completed successfully",
        )
        log = await repo.get_by_id(log_id)
        return ProcessingLogRead.model_validate(log) if log else None

    @staticmethod
    async def update_to_failed(
        log_id: UUID, error: str, db: AsyncSession
    ) -> ProcessingLogRead | None:
        """Обновить статус лога на FAILED.

        Args:
            log_id: Идентификатор лога.
            error: Сообщение об ошибке.
            db: Асинхронная сессия базы данных.

        Returns:
            Обновленный лог или None, если не найден.
        """
        logger.error(
            "Обновление лога на FAILED: log_id=%s, error=%s",
            log_id,
            error,
        )
        repo = ProcessingLogRepository(db)
        await repo.update_status(
            log_id=log_id,
            status=ProcessingStatusEnum.FAILED,
            message=error,
        )
        log = await repo.get_by_id(log_id)
        return ProcessingLogRead.model_validate(log) if log else None

    @staticmethod
    async def get_filtered(
        filters: ProcessingLogFilter, db: AsyncSession
    ) -> list[ProcessingLogRead]:
        """Получить отфильтрованные логи обработки.

        Args:
            filters: Параметры фильтрации.
            db: Асинхронная сессия базы данных.

        Returns:
            Список логов в формате Pydantic моделей.
        """
        logger.info("Получение отфильтрованных логов: filters=%s", filters)
        repo = ProcessingLogRepository(db)
        result = await repo.get_filtered(filters)
        return result  # type: ignore[no-any-return]
