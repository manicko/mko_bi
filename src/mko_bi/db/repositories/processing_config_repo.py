"""Репозиторий для работы с настройками обработки.

Предоставляет методы CRUD для модели ProcessingConfig.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import processing_configs as processing_config_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ProcessingConfigRepository:
    """Репозиторий для операций с настройками обработки.
    
    Предоставляет методы для создания, чтения, обновления и удаления
    настроек обработки в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением
    транзакциями.
    """
    
    @classmethod
    async def get(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> processing_config_model.ProcessingConfig | None:
        """Получить настройки обработки по ID дашборда.
        
        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Модель настроек обработки или None, если не найдена.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id == dashboard_id
                )
            )
            config = result.scalar_one_or_none()
            if config:
                logger.info("Настройки обработки получены: dashboard_id=%s", dashboard_id)
            else:
                logger.warning("Настройки обработки не найдены: dashboard_id=%s", dashboard_id)
            return config
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении настроек dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> processing_config_model.ProcessingConfig | None:
        """Создать новые настройки обработки.
        
        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры настроек (dashboard_id, settings).
        
        Returns:
            Модель созданных настроек с ID или None при ошибке.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            config_obj = processing_config_model.ProcessingConfig(**kwargs)
            db.add(config_obj)
            await db.flush()
            await db.refresh(config_obj)
            logger.info(
                "Настройки обработки созданы: dashboard_id=%s", config_obj.dashboard_id
            )
            return config_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании настроек обработки: %s", e)
            raise

    @classmethod
    async def update(
        cls, dashboard_id: UUID, db: AsyncSession, **kwargs
    ) -> processing_config_model.ProcessingConfig | None:
        """Обновить настройки обработки.
        
        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.
        
        Returns:
            Обновленная модель настроек или None, если не найдена.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id == dashboard_id
                )
            )
            config_obj = result.scalar_one_or_none()
            if not config_obj:
                logger.warning("Настройки не найдены для обновления: dashboard_id=%s", dashboard_id)
                return None
            for key, value in kwargs.items():
                if hasattr(config_obj, key):
                    setattr(config_obj, key, value)
            await db.flush()
            await db.refresh(config_obj)
            logger.info("Настройки обновлены: dashboard_id=%s", dashboard_id)
            return config_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении настроек dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    async def delete(cls, dashboard_id: UUID, db: AsyncSession) -> bool:
        """Удалить настройки обработки.
        
        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            True, если удаление успешно, False - если настройки не найдены.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id == dashboard_id
                )
            )
            config_obj = result.scalar_one_or_none()
            if not config_obj:
                logger.warning("Настройки не найдены для удаления: dashboard_id=%s", dashboard_id)
                return False
            await db.delete(config_obj)
            await db.flush()
            logger.info("Настройки удалены: dashboard_id=%s", dashboard_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении настроек dashboard_id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[processing_config_model.ProcessingConfig]:
        """Получить все настройки обработки.
        
        Args:
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список всех настроек обработки.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(processing_config_model.ProcessingConfig))
            configs = list(result.scalars().all())
            logger.info("Получен список настроек, количество: %s", len(configs))
            return configs
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка настроек: %s", e)
            raise
