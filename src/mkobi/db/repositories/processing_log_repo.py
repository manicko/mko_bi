"""Репозиторий для работы с логами обработки.

Предоставляет методы CRUD для модели ProcessingLog.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mkobi.db.models import processing_logs as processing_log_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ProcessingLogRepository:
    """Репозиторий для операций с логами обработки.
    
    Предоставляет методы для создания, чтения, обновления и удаления
    логов обработки в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением
    транзакциями.
    """
    
    @classmethod
    async def get(
        cls, log_id: UUID, db: AsyncSession
    ) -> processing_log_model.ProcessingLog | None:
        """Получить лог обработки по ID.
        
        Args:
            log_id: Идентификатор лога (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Модель лога обработки или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            )
            log = result.scalar_one_or_none()
            if log:
                logger.info("Лог обработки получен: id=%s", log_id)
            else:
                logger.warning("Лог обработки не найден: id=%s", log_id)
            return log
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении лога id=%s: %s", log_id, e)
            raise

    @classmethod
    async def get_by_dashboard(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> list[processing_log_model.ProcessingLog]:
        """Получить все логи обработки для дашборда.
        
        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список логов обработки для дашборда.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog)
                .where(processing_log_model.ProcessingLog.dashboard_id == dashboard_id)
            )
            logs = list(result.scalars().all())
            logger.info(
                "Получены логи для dashboard_id=%s, количество: %s",
                dashboard_id,
                len(logs),
            )
            return logs
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении логов dashboard_id=%s: %s", dashboard_id, e
            )
            raise

    @classmethod
    async def create(
        cls, db: AsyncSession, **kwargs
    ) -> processing_log_model.ProcessingLog | None:
        """Создать новый лог обработки.
        
        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры лога (dashboard_id, status, message, etc.).
        
        Returns:
            Модель созданного лога с ID или None при ошибке.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            log_obj = processing_log_model.ProcessingLog(**kwargs)
            db.add(log_obj)
            await db.flush()
            await db.refresh(log_obj)
            logger.info(
                "Лог обработки создан: id=%s, dashboard_id=%s",
                log_obj.id,
                log_obj.dashboard_id,
            )
            return log_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании лога: %s", e)
            raise

    @classmethod
    async def update(
        cls, log_id: UUID, db: AsyncSession, **kwargs
    ) -> processing_log_model.ProcessingLog | None:
        """Обновить данные лога обработки.
        
        Args:
            log_id: Идентификатор лога (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.
        
        Returns:
            Обновленная модель лога или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            )
            log_obj = result.scalar_one_or_none()
            if not log_obj:
                logger.warning("Лог не найден для обновления: id=%s", log_id)
                return None
            for key, value in kwargs.items():
                if hasattr(log_obj, key):
                    setattr(log_obj, key, value)
            await db.flush()
            await db.refresh(log_obj)
            logger.info("Лог обновлен: id=%s", log_id)
            return log_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении лога id=%s: %s", log_id, e)
            raise

    @classmethod
    async def delete(cls, log_id: UUID, db: AsyncSession) -> bool:
        """Удалить лог обработки.
        
        Args:
            log_id: Идентификатор лога (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            True, если удаление успешно, False - если лог не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            )
            log_obj = result.scalar_one_or_none()
            if not log_obj:
                logger.warning("Лог не найден для удаления: id=%s", log_id)
                return False
            db.delete(log_obj)  # type: ignore[unused-coroutine]
            await db.flush()
            logger.info("Лог удален: id=%s", log_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении лога id=%s: %s", log_id, e)
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[processing_log_model.ProcessingLog]:
        """Получить все логи обработки.
        
        Args:
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список всех логов обработки.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(processing_log_model.ProcessingLog))
            logs = list(result.scalars().all())
            logger.info("Получен список логов, количество: %s", len(logs))
            return logs
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка логов: %s", e)
            raise
