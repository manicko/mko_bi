"""Репозиторий для работы с пользователями.

Предоставляет методы CRUD для модели User.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import user as user_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для операций с пользователями.

    Предоставляет методы для создания, чтения, обновления и удаления
    пользователей в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    async def get(cls, user_id: UUID, db: AsyncSession) -> user_model.User | None:
        """Получить пользователя по ID.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            Модель пользователя или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(user_model.User).where(user_model.User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                logger.info("Пользователь получен: id=%s", user_id)
            else:
                logger.warning("Пользователь не найден: id=%s", user_id)
            return user
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении пользователя id=%s: %s", user_id, e)
            raise

    @classmethod
    async def get_by_email(cls, email: str, db: AsyncSession) -> user_model.User | None:
        """Получить пользователя по email.

        Args:
            email: Email пользователя.
            db: Асинхронная сессия базы данных.

        Returns:
            Модель пользователя или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(user_model.User).where(user_model.User.email == email)
            )
            user = result.scalar_one_or_none()
            if user:
                logger.info("Пользователь получен по email: %s", email)
            else:
                logger.warning("Пользователь не найден по email: %s", email)
            return user
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении пользователя email=%s: %s", email, e)
            raise

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> user_model.User | None:
        """Создать нового пользователя.

        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры пользователя (email, password_hash, role).

        Returns:
            Модель созданного пользователя с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            user_obj = user_model.User(**kwargs)
            db.add(user_obj)
            await db.flush()
            await db.refresh(user_obj)
            logger.info(
                "Пользователь создан: id=%s, email=%s", user_obj.id, user_obj.email
            )
            return user_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании пользователя: %s", e)
            raise

    @classmethod
    async def update(cls, user_id: UUID, db: AsyncSession, **kwargs) -> user_model.User | None:
        """Обновить данные пользователя.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель пользователя или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(user_model.User).where(user_model.User.id == user_id)
            )
            user_obj = result.scalar_one_or_none()
            if not user_obj:
                logger.warning("Пользователь не найден для обновления: id=%s", user_id)
                return None
            for key, value in kwargs.items():
                if hasattr(user_obj, key):
                    setattr(user_obj, key, value)
            await db.flush()
            await db.refresh(user_obj)
            logger.info("Пользователь обновлен: id=%s", user_id)
            return user_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении пользователя id=%s: %s", user_id, e)
            raise

    @classmethod
    async def delete(cls, user_id: UUID, db: AsyncSession) -> bool:
        """Удалить пользователя.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            True, если удаление успешно, False - если пользователь не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(user_model.User).where(user_model.User.id == user_id)
            )
            user_obj = result.scalar_one_or_none()
            if not user_obj:
                logger.warning("Пользователь не найден для удаления: id=%s", user_id)
                return False
            db.delete(user_obj)  # type: ignore[unused-coroutine]
            await db.flush()
            logger.info("Пользователь удален: id=%s", user_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении пользователя id=%s: %s", user_id, e)
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[user_model.User]:
        """Получить всех пользователей.

        Args:
            db: Асинхронная сессия базы данных.

        Returns:
            Список всех пользователей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(user_model.User))
            users = list(result.scalars().all())
            logger.info("Получен список пользователей, количество: %s", len(users))
            return users
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка пользователей: %s", e)
            raise
