"""Репозиторий для работы с layout-ами.

Предоставляет методы CRUD для модели Layout.
Все методы используют асинхронную сессию и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import layout as layout_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class LayoutRepository:
    """Репозиторий для операций с layout-ами.

    Предоставляет методы для создания, чтения, обновления и удаления
    layout-ов в базе данных. Все операции выполняются в рамках
    асинхронной сессии с обработкой ошибок.
    """

    @classmethod
    async def get(cls, layout_id: UUID, db: AsyncSession) -> layout_model.Layout | None:
        """Получить layout по ID.

        Args:
            layout_id: Идентификатор layout (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            Модель layout или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(layout_model.Layout).where(layout_model.Layout.id == layout_id)
            )
            layout = result.scalar_one_or_none()
            if layout:
                logger.info("Layout получен: id=%s", layout_id)
            else:
                logger.warning("Layout не найден: id=%s", layout_id)
            return layout
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении layout id=%s: %s", layout_id, e)
            raise

    @classmethod
    async def get_by_name(cls, name: str, db: AsyncSession) -> layout_model.Layout | None:
        """Получить layout по имени.

        Args:
            name: Имя layout.
            db: Асинхронная сессия базы данных.

        Returns:
            Модель layout или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(layout_model.Layout).where(layout_model.Layout.name == name)
            )
            layout = result.scalar_one_or_none()
            if layout:
                logger.info("Layout получен по имени: name=%s", name)
            else:
                logger.warning("Layout не найден по имени: name=%s", name)
            return layout
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении layout по имени %s: %s", name, e)
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[layout_model.Layout]:
        """Получить все layout-ы.

        Args:
            db: Асинхронная сессия базы данных.

        Returns:
            Список всех layout-ов.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(layout_model.Layout))
            layouts = list(result.scalars().all())
            logger.info("Получен список layout-ов, количество: %s", len(layouts))
            return layouts
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка layout-ов: %s", e)
            raise

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> layout_model.Layout | None:
        """Создать новый layout.

        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры layout (name, definition).

        Returns:
            Модель созданного layout с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            layout_obj = layout_model.Layout(**kwargs)
            db.add(layout_obj)
            await db.flush()
            await db.refresh(layout_obj)
            logger.info("Layout создан: id=%s, name=%s", layout_obj.id, layout_obj.name)
            return layout_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании layout: %s", e)
            raise

    @classmethod
    async def update(
        cls, layout_id: UUID, db: AsyncSession, **kwargs
    ) -> layout_model.Layout | None:
        """Обновить данные layout.

        Args:
            layout_id: Идентификатор layout (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель layout или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(layout_model.Layout).where(layout_model.Layout.id == layout_id)
            )
            layout_obj = result.scalar_one_or_none()
            if not layout_obj:
                logger.warning("Layout не найден для обновления: id=%s", layout_id)
                return None
            for key, value in kwargs.items():
                if hasattr(layout_obj, key):
                    setattr(layout_obj, key, value)
            await db.flush()
            await db.refresh(layout_obj)
            logger.info("Layout обновлен: id=%s", layout_id)
            return layout_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении layout id=%s: %s", layout_id, e)
            raise

    @classmethod
    async def delete(cls, layout_id: UUID, db: AsyncSession) -> bool:
        """Удалить layout.

        Args:
            layout_id: Идентификатор layout (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            True, если удаление успешно, False - если layout не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(layout_model.Layout).where(layout_model.Layout.id == layout_id)
            )
            layout_obj = result.scalar_one_or_none()
            if not layout_obj:
                logger.warning("Layout не найден для удаления: id=%s", layout_id)
                return False
            await db.delete(layout_obj)
            await db.flush()
            logger.info("Layout удален: id=%s", layout_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении layout id=%s: %s", layout_id, e)
            raise
