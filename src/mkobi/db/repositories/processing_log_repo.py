"""Репозиторий для работы с логами обработки.

Предоставляет методы для работы с логами обработки данных.
Наследуется от BaseRepository для получения базовых CRUD операций.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.core.base_repository import BaseRepository
from mkobi.db.models import processing_logs as processing_log_model
from mkobi.db.models.processing_logs import ProcessingLog
from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead

logger = logging.getLogger(__name__)


class ProcessingLogRepository(BaseRepository[ProcessingLog]):
    """Репозиторий для операций с логами обработки.

    Предоставляет методы для создания, чтения и обновления
    логов обработки в базе данных.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Инициализация репозитория.

        Args:
            db: Асинхронная сессия базы данных.
        """
        super().__init__(processing_log_model.ProcessingLog, db)

    async def create_log(
        self,
        dashboard_id: UUID | None,
        status: ProcessingStatus,
        message: str | None = None,
    ) -> ProcessingLog:
        """Создать новый лог обработки.

        Args:
            dashboard_id: Идентификатор дашборда (опционально).
            status: Статус обработки.
            message: Сообщение об ошибке или успехе (опционально).

        Returns:
            Созданная модель лога обработки.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            log_data = {
                "dashboard_id": dashboard_id,
                "status": status,
                "message": message,
                "started_at": datetime.now(),
            }
            log_obj = processing_log_model.ProcessingLog(**log_data)
            self.db.add(log_obj)
            await self.db.flush()
            await self.db.refresh(log_obj)
            logger.info(
                "Лог обработки создан: id=%s, dashboard_id=%s, status=%s",
                log_obj.id,
                dashboard_id,
                status,
            )
            return log_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании лога: %s", e)
            raise

    async def update_status(
        self,
        log_id: UUID,
        status: ProcessingStatus,
        message: str | None = None,
    ) -> None:
        """Обновить статус лога обработки.

        Args:
            log_id: Идентификатор лога.
            status: Новый статус.
            message: Сообщение (опционально).

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await self.db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            )
            log_obj = result.scalar_one_or_none()
            if not log_obj:
                logger.warning("Лог не найден для обновления: id=%s", log_id)
                return

            log_obj.status = status
            if message is not None:
                log_obj.message = message

            # Устанавливаем finished_at при успешном завершении или ошибке
            if status in (ProcessingStatus.SUCCESS, ProcessingStatus.FAILED):
                log_obj.finished_at = datetime.now()

            await self.db.flush()
            logger.info("Статус лога обновлен: id=%s, status=%s", log_id, status)
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении статуса лога id=%s: %s", log_id, e)
            raise

    async def get_by_dashboard(
        self,
        dashboard_id: UUID | None,
    ) -> list[ProcessingLogRead]:
        """Получить все логи обработки для дашборда.

        Args:
            dashboard_id: Идентификатор дашборда (может быть None).

        Returns:
            Список логов обработки для дашборда в формате Pydantic моделей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            query = select(processing_log_model.ProcessingLog)
            if dashboard_id is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.dashboard_id == dashboard_id
                )
            else:
                query = query.where(
                    processing_log_model.ProcessingLog.dashboard_id.is_(None)
                )
            query = query.order_by(processing_log_model.ProcessingLog.started_at.desc())
            result = await self.db.execute(query)
            logs = list(result.scalars().all())
            logger.info(
                "Получены логи для dashboard_id=%s, количество: %s",
                dashboard_id,
                len(logs),
            )
            return [ProcessingLogRead.model_validate(log) for log in logs]
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении логов dashboard_id=%s: %s", dashboard_id, e
            )
            raise

    async def get_filtered(
        self,
        filters: ProcessingLogFilter,
    ) -> list[ProcessingLogRead]:
        """Получить логи обработки с фильтрацией.

        Args:
            filters: Параметры фильтрации.

        Returns:
            Список логов обработки в формате Pydantic моделей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            query = select(processing_log_model.ProcessingLog)

            if filters.dashboard_id is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.dashboard_id == filters.dashboard_id
                )

            if filters.status is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.status == filters.status
                )

            if filters.date_from is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.started_at >= filters.date_from
                )

            if filters.date_to is not None:
                query = query.where(
                    processing_log_model.ProcessingLog.started_at <= filters.date_to
                )

            query = query.order_by(processing_log_model.ProcessingLog.started_at.desc())

            if filters.skip > 0:
                query = query.offset(filters.skip)

            if filters.limit > 0:
                query = query.limit(filters.limit)

            result = await self.db.execute(query)
            logs = list(result.scalars().all())
            logger.info(
                "Получены отфильтрованные логи, количество: %s",
                len(logs),
            )
            return [ProcessingLogRead.model_validate(log) for log in logs]
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении отфильтрованных логов: %s", e)
            raise

    async def get_latest_by_dashboard(
        self,
        dashboard_id: UUID,
    ) -> ProcessingLogRead | None:
        """Получить последний лог обработки для дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.

        Returns:
            Последний лог обработки или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await self.db.execute(
                select(processing_log_model.ProcessingLog)
                .where(processing_log_model.ProcessingLog.dashboard_id == dashboard_id)
                .order_by(processing_log_model.ProcessingLog.started_at.desc())
                .limit(1)
            )
            log = result.scalar_one_or_none()
            if log:
                logger.info(
                    "Получен последний лог для dashboard_id=%s: id=%s",
                    dashboard_id,
                    log.id,
                )
                return ProcessingLogRead.model_validate(log)
            else:
                logger.info("Логи для dashboard_id=%s не найдены", dashboard_id)
                return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении последнего лога dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
