"""Репозиторий для работы с пользователями.

Предоставляет методы CRUD для модели User.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import user as user_model
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для операций с пользователями.

    Предоставляет методы для создания, чтения, обновления и удаления
    пользователей в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def get(cls, user_id: UUID, db: Session) -> user_model.User | None:
        """Получить пользователя по ID.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Сессия базы данных.

        Returns:
            Модель пользователя или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(user_model.User).where(user_model.User.id == user_id)
            ).scalar_one_or_none()
            if result:
                logger.info("Пользователь получен: id=%s", user_id)
            else:
                logger.warning("Пользователь не найден: id=%s", user_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении пользователя id=%s: %s", user_id, e)
            raise

    @classmethod
    def get_by_email(cls, email: str, db: Session) -> user_model.User | None:
        """Получить пользователя по email.

        Args:
            email: Email пользователя.
            db: Сессия базы данных.

        Returns:
            Модель пользователя или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(user_model.User).where(user_model.User.email == email)
            ).scalar_one_or_none()
            if result:
                logger.info("Пользователь получен по email: %s", email)
            else:
                logger.warning("Пользователь не найден по email: %s", email)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении пользователя email=%s: %s", email, e)
            raise

    @classmethod
    def create(cls, db: Session, **kwargs) -> user_model.User | None:
        """Создать нового пользователя.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры пользователя (email, password_hash, role).

        Returns:
            Модель созданного пользователя с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            user_obj = user_model.User(**kwargs)
            db.add(user_obj)
            db.flush()
            db.refresh(user_obj)
            logger.info(
                "Пользователь создан: id=%s, email=%s", user_obj.id, user_obj.email
            )
            return user_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании пользователя: %s", e)
            raise

    @classmethod
    def update(cls, user_id: UUID, db: Session, **kwargs) -> user_model.User | None:
        """Обновить данные пользователя.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель пользователя или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            user_obj = db.execute(
                select(user_model.User).where(user_model.User.id == user_id)
            ).scalar_one_or_none()
            if not user_obj:
                logger.warning("Пользователь не найден для обновления: id=%s", user_id)
                return None
            for key, value in kwargs.items():
                if hasattr(user_obj, key):
                    setattr(user_obj, key, value)
            db.flush()
            db.refresh(user_obj)
            logger.info("Пользователь обновлен: id=%s", user_id)
            return user_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении пользователя id=%s: %s", user_id, e)
            raise

    @classmethod
    def delete(cls, user_id: UUID, db: Session) -> bool:
        """Удалить пользователя.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если пользователь не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            user_obj = db.execute(
                select(user_model.User).where(user_model.User.id == user_id)
            ).scalar_one_or_none()
            if not user_obj:
                logger.warning("Пользователь не найден для удаления: id=%s", user_id)
                return False
            db.delete(user_obj)
            db.flush()
            logger.info("Пользователь удален: id=%s", user_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении пользователя id=%s: %s", user_id, e)
            raise

    @classmethod
    def get_session(cls) -> Session:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия.
        """
        from mko_bi.db.session import get_session
        return get_session()

    @classmethod
    def get_all(cls, db: Session) -> list[user_model.User]:
        """Получить всех пользователей.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех пользователей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(user_model.User)).scalars().all()
            logger.info("Получен список пользователей, количество: %s", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка пользователей: %s", e)
            raise