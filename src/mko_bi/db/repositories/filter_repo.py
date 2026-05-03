"""Репозиторий для работы с фильтрами.

Предоставляет методы CRUD для модели Filter.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import filters as filter_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FilterRepository:
    """Репозиторий для операций с фильтрами.
    
    Предоставляет методы для создания, чтения, обновления и удаления
    фильтров в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """
    
    @classmethod
    async def get(cls, filter_id: UUID, db: AsyncSession) -> filter_model.Filter | None:
        """Получить фильтр по ID.
        
        Args:
            filter_id: Идентификатор фильтра (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Модель фильтра или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.id == filter_id
                )
            )
            filter_obj = result.scalar_one_or_none()
            if filter_obj:
                logger.info("Фильтр получен: id=%s", filter_id)
            else:
                logger.warning("Фильтр не найден: id=%s", filter_id)
            return filter_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении фильтра id=%s: %s", filter_id, e)
            raise
    
    @classmethod
    async def get_by_name(cls, name: str, db: AsyncSession) -> filter_model.Filter | None:
        """Получить фильтр по имени.
        
        Args:
            name: Имя фильтра.
            db: Асинхронная сессия базы данных.
        
        Returns:
            Модель фильтра или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.name == name
                )
            )
            filter_obj = result.scalar_one_or_none()
            if filter_obj:
                logger.info("Фильтр получен по имени: %s", name)
            else:
                logger.warning("Фильтр не найден по имени: %s", name)
            return filter_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении фильтра name=%s: %s", name, e)
            raise
    
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> filter_model.Filter | None:
        """Создать новый фильтр.
        
        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры фильтра (name, type, config).
        
        Returns:
            Модель созданного фильтра с ID или None при ошибке.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            filter_obj = filter_model.Filter(**kwargs)
            db.add(filter_obj)
            await db.flush()
            await db.refresh(filter_obj)
            logger.info(
                "Фильтр создан: id=%s, name=%s", filter_obj.id, filter_obj.name
            )
            return filter_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании фильтра: %s", e)
            raise
    
    @classmethod
    async def update(
        cls, filter_id: UUID, db: AsyncSession, **kwargs
    ) -> filter_model.Filter | None:
        """Обновить данные фильтра.
        
        Args:
            filter_id: Идентификатор фильтра (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.
        
        Returns:
            Обновленная модель фильтра или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.id == filter_id
                )
            )
            filter_obj = result.scalar_one_or_none()
            if not filter_obj:
                logger.warning("Фильтр не найден для обновления: id=%s", filter_id)
                return None
            for key, value in kwargs.items():
                if hasattr(filter_obj, key):
                    setattr(filter_obj, key, value)
            await db.flush()
            await db.refresh(filter_obj)
            logger.info("Фильтр обновлен: id=%s", filter_id)
            return filter_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении фильтра id=%s: %s", filter_id, e)
            raise
    
    @classmethod
    async def delete(cls, filter_id: UUID, db: AsyncSession) -> bool:
        """Удалить фильтр.
        
        Args:
            filter_id: Идентификатор фильтра (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            True, если удаление успешно, False - если фильтр не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.id == filter_id
                )
            )
            filter_obj = result.scalar_one_or_none()
            if not filter_obj:
                logger.warning("Фильтр не найден для удаления: id=%s", filter_id)
                return False
            db.delete(filter_obj)  # type: ignore[unused-coroutine]
            await db.flush()
            logger.info("Фильтр удален: id=%s", filter_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении фильтра id=%s: %s", filter_id, e)
            raise
    
    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[filter_model.Filter]:
        """Получить все фильтры.
        
        Args:
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список всех фильтров.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(filter_model.Filter))
            filters = list(result.scalars().all())
            logger.info("Получен список фильтров, количество: %s", len(filters))
            return filters
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка фильтров: %s", e)
            raise
