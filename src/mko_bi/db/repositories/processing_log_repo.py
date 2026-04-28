"""Репозиторий для работы с логами обработки.

Предоставляет методы CRUD для модели ProcessingLog.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import processing_logs as processing_log_model
from mko_bi.db.session import SessionLocal

logger = logging.getLogger(__name__)


class ProcessingLogRepository:
    """Репозиторий для операций с логами обработки.

    Предоставляет методы для создания, чтения, обновления и удаления
    логов обработки в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def get(cls, log_id: UUID, db: SessionLocal) -> processing_log_model.ProcessingLog | None:
        """Получить лог обработки по ID.

        Args:
            log_id: Идентификатор лога (UUID).
            db: Сессия базы данных.

        Returns:
            Модель лога обработки или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            ).scalar_one_or_none()
            if result:
                logger.info("Лог обработки получен: id=%s", log_id)
            else:
                logger.warning("Лог обработки не найден: id=%s", log_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении лога обработки id=%s: %s", log_id, e)
            raise

    @classmethod
    def get_by_dashboard(
        cls, dashboard_id: UUID, db: SessionLocal
    ) -> list[processing_log_model.ProcessingLog]:
        """Получить все логи обработки для дашборда.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            Список логов обработки для дашборда.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.dashboard_id == dashboard_id
                )
            ).scalars().all()
            logger.info(
                "Получены логи обработки для дашборда dashboard_id=%s, количество: %s",
                dashboard_id,
                len(result),
            )
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении логов обработки для dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def get_all(cls, db: SessionLocal) -> list[processing_log_model.ProcessingLog]:
        """Получить все логи обработки.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех логов обработки.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(processing_log_model.ProcessingLog)).scalars().all()
            logger.info("Получен список логов обработки, количество: %s", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка логов обработки: %s", e)
            raise

    @classmethod
    def create(cls, db: SessionLocal, **kwargs) -> processing_log_model.ProcessingLog | None:
        """Создать новый лог обработки.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры лога обработки (dashboard_id, status, message и т.д.).

        Returns:
            Модель созданного лога обработки или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            log_obj = processing_log_model.ProcessingLog(**kwargs)
            db.add(log_obj)
            db.flush()
            db.refresh(log_obj)
            logger.info(
                "Лог обработки создан: id=%s, status=%s, dashboard_id=%s",
                log_obj.id,
                log_obj.status,
                log_obj.dashboard_id,
            )
            return log_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании лога обработки: %s", e)
            raise

    @classmethod
    def update(
        cls, log_id: UUID, db: SessionLocal, **kwargs
    ) -> processing_log_model.ProcessingLog | None:
        """Обновить данные лога обработки.

        Args:
            log_id: Идентификатор лога (UUID).
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель лога обработки или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            log_obj = db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            ).scalar_one_or_none()
            if not log_obj:
                logger.warning("Лог обработки не найден для обновления: id=%s", log_id)
                return None
            for key, value in kwargs.items():
                if hasattr(log_obj, key):
                    setattr(log_obj, key, value)
            db.flush()
            db.refresh(log_obj)
            logger.info("Лог обработки обновлен: id=%s", log_id)
            return log_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении лога обработки id=%s: %s", log_id, e)
            raise

    @classmethod
    def delete(cls, log_id: UUID, db: SessionLocal) -> bool:
        """Удалить лог обработки.

        Args:
            log_id: Идентификатор лога (UUID).
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если лог не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            log_obj = db.execute(
                select(processing_log_model.ProcessingLog).where(
                    processing_log_model.ProcessingLog.id == log_id
                )
            ).scalar_one_or_none()
            if not log_obj:
                logger.warning("Лог обработки не найден для удаления: id=%s", log_id)
                return False
            db.delete(log_obj)
            db.flush()
            logger.info("Лог обработки удален: id=%s", log_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении лога обработки id=%s: %s", log_id, e)
            raise

    @classmethod
    def get_session(cls) -> SessionLocal:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия SessionLocal.
        """
        return SessionLocal()
