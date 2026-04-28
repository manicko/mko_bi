"""Репозиторий для работы с настройками обработки.

Предоставляет методы CRUD для модели ProcessingConfig.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import processing_configs as processing_config_model
from mko_bi.db.session import SessionLocal

logger = logging.getLogger(__name__)


class ProcessingConfigRepository:
    """Репозиторий для операций с настройками обработки.

    Предоставляет методы для создания, чтения, обновления и удаления
    настроек обработки в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def get(cls, dashboard_id: UUID, db: SessionLocal) -> processing_config_model.ProcessingConfig | None:
        """Получить настройки обработки по ID дашборда.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            Модель настроек обработки или None, если не найдена.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id == dashboard_id
                )
            ).scalar_one_or_none()
            if result:
                logger.info("Настройки обработки получены: dashboard_id=%s", dashboard_id)
            else:
                logger.warning("Настройки обработки не найдены: dashboard_id=%s", dashboard_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении настроек обработки dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def get_all(cls, db: SessionLocal) -> list[processing_config_model.ProcessingConfig]:
        """Получить все настройки обработки.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех настроек обработки.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(processing_config_model.ProcessingConfig)).scalars().all()
            logger.info("Получен список настроек обработки, количество: %s", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка настроек обработки: %s", e)
            raise

    @classmethod
    def create(cls, db: SessionLocal, **kwargs) -> processing_config_model.ProcessingConfig | None:
        """Создать новые настройки обработки.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры настроек обработки (dashboard_id, settings).

        Returns:
            Модель созданных настроек обработки или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            config_obj = processing_config_model.ProcessingConfig(**kwargs)
            db.add(config_obj)
            db.commit()
            db.refresh(config_obj)
            logger.info(
                "Настройки обработки созданы: dashboard_id=%s", config_obj.dashboard_id
            )
            return config_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при создании настроек обработки: %s", e)
            raise

    @classmethod
    def update(
        cls, dashboard_id: UUID, db: SessionLocal, **kwargs
    ) -> processing_config_model.ProcessingConfig | None:
        """Обновить настройки обработки.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель настроек обработки или None, если не найдена.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            config_obj = db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id == dashboard_id
                )
            ).scalar_one_or_none()
            if not config_obj:
                logger.warning("Настройки обработки не найдены для обновления: dashboard_id=%s", dashboard_id)
                return None
            for key, value in kwargs.items():
                if hasattr(config_obj, key):
                    setattr(config_obj, key, value)
            db.commit()
            db.refresh(config_obj)
            logger.info("Настройки обработки обновлены: dashboard_id=%s", dashboard_id)
            return config_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при обновлении настроек обработки dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def delete(cls, dashboard_id: UUID, db: SessionLocal) -> bool:
        """Удалить настройки обработки.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если настройки не найдены.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            config_obj = db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id == dashboard_id
                )
            ).scalar_one_or_none()
            if not config_obj:
                logger.warning("Настройки обработки не найдены для удаления: dashboard_id=%s", dashboard_id)
                return False
            db.delete(config_obj)
            db.commit()
            logger.info("Настройки обработки удалены: dashboard_id=%s", dashboard_id)
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при удалении настроек обработки dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def get_session(cls) -> SessionLocal:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия SessionLocal.
        """
        return SessionLocal()
