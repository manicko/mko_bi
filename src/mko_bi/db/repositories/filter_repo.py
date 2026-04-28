"""Репозиторий для работы с фильтрами.

Предоставляет методы CRUD для модели Filter.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import filters as filter_model
from mko_bi.db.session import SessionLocal

logger = logging.getLogger(__name__)


class FilterRepository:
    """Репозиторий для операций с фильтрами.

    Предоставляет методы для создания, чтения, обновления и удаления
    фильтров в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def get(cls, filter_id: UUID, db: SessionLocal) -> filter_model.Filter | None:
        """Получить фильтр по ID.

        Args:
            filter_id: Идентификатор фильтра (UUID).
            db: Сессия базы данных.

        Returns:
            Модель фильтра или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.id == filter_id
                )
            ).scalar_one_or_none()
            if result:
                logger.info("Фильтр получен: id=%s", filter_id)
            else:
                logger.warning("Фильтр не найден: id=%s", filter_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении фильтра id=%s: %s", filter_id, e)
            raise

    @classmethod
    def get_by_name(cls, name: str, db: SessionLocal) -> filter_model.Filter | None:
        """Получить фильтр по имени.

        Args:
            name: Имя фильтра.
            db: Сессия базы данных.

        Returns:
            Модель фильтра или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.name == name
                )
            ).scalar_one_or_none()
            if result:
                logger.info("Фильтр получен по имени: name=%s", name)
            else:
                logger.warning("Фильтр не найден по имени: name=%s", name)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении фильтра name=%s: %s", name, e)
            raise

    @classmethod
    def get_all(cls, db: SessionLocal) -> list[filter_model.Filter]:
        """Получить все фильтры.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех фильтров.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(filter_model.Filter)).scalars().all()
            logger.info("Получен список фильтров, количество: %s", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка фильтров: %s", e)
            raise

    @classmethod
    def create(cls, db: SessionLocal, **kwargs) -> filter_model.Filter | None:
        """Создать новый фильтр.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры фильтра (name, type, config).

        Returns:
            Модель созданного фильтра с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            filter_obj = filter_model.Filter(**kwargs)
            db.add(filter_obj)
            db.commit()
            db.refresh(filter_obj)
            logger.info(
                "Фильтр создан: id=%s, name=%s", filter_obj.id, filter_obj.name
            )
            return filter_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при создании фильтра: %s", e)
            raise

    @classmethod
    def update(
        cls, filter_id: UUID, db: SessionLocal, **kwargs
    ) -> filter_model.Filter | None:
        """Обновить данные фильтра.

        Args:
            filter_id: Идентификатор фильтра (UUID).
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель фильтра или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            filter_obj = db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.id == filter_id
                )
            ).scalar_one_or_none()
            if not filter_obj:
                logger.warning("Фильтр не найден для обновления: id=%s", filter_id)
                return None
            for key, value in kwargs.items():
                if hasattr(filter_obj, key):
                    setattr(filter_obj, key, value)
            db.commit()
            db.refresh(filter_obj)
            logger.info("Фильтр обновлен: id=%s", filter_id)
            return filter_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при обновлении фильтра id=%s: %s", filter_id, e)
            raise

    @classmethod
    def delete(cls, filter_id: UUID, db: SessionLocal) -> bool:
        """Удалить фильтр.

        Args:
            filter_id: Идентификатор фильтра (UUID).
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если фильтр не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            filter_obj = db.execute(
                select(filter_model.Filter).where(
                    filter_model.Filter.id == filter_id
                )
            ).scalar_one_or_none()
            if not filter_obj:
                logger.warning("Фильтр не найден для удаления: id=%s", filter_id)
                return False
            db.delete(filter_obj)
            db.commit()
            logger.info("Фильтр удален: id=%s", filter_id)
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при удалении фильтра id=%s: %s", filter_id, e)
            raise

    @classmethod
    def get_session(cls) -> SessionLocal:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия SessionLocal.
        """
        return SessionLocal()
