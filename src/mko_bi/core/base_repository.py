"""Базовый репозиторий с общими CRUD операциями.

Предоставляет generic класс для типичных операций с базой данных.
Все репозитории могут наследоваться от этого класса для уменьшения дублирования.
"""

import logging
from typing import TypeVar, Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.db.session import get_session

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class BaseRepository[ModelType]:
    """Базовый репозиторий с CRUD операциями.

    Generic класс для работы с моделями SQLAlchemy.
    Предоставляет стандартные методы для создания, чтения,
    обновления и удаления объектов.

    Attributes:
        model: Класс модели SQLAlchemy.
    """

    def __init__(self, model: type[ModelType]) -> None:
        """Инициализация репозитория.

        Args:
            model: Класс модели SQLAlchemy.
        """
        self.model = model

    def get(self, obj_id: Any, db: Session | None = None) -> ModelType | None:
        """Получить объект по ID.

        Args:
            obj_id: Идентификатор объекта.
            db: Опциональная сессия базы данных.

        Returns:
            Объект модели или None, если не найден.
        """
        local_session = False
        if db is None:
            db = get_session().__enter__()
            local_session = True

        try:
            result = db.execute(
                select(self.model).where(self.model.id == obj_id)
            ).scalar_one_or_none()
            if result:
                logger.info("Объект получен: model=%s, id=%s", self.model.__name__, obj_id)
            else:
                logger.warning("Объект не найден: model=%s, id=%s", self.model.__name__, obj_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении объекта id=%s: %s", obj_id, e)
            raise
        finally:
            if local_session:
                db.close()

    def get_all(
        self, db: Session | None = None, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Получить список всех объектов с пагинацией.

        Args:
            db: Опциональная сессия базы данных.
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            Список объектов модели.
        """
        local_session = False
        if db is None:
            db = get_session().__enter__()
            local_session = True

        try:
            result = (
                db.execute(select(self.model).offset(skip).limit(limit))
                .scalars()
                .all()
            )
            logger.info(
                "Получен список объектов: model=%s, count=%s",
                self.model.__name__,
                len(result),
            )
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка объектов: %s", e)
            raise
        finally:
            if local_session:
                db.close()

    def create(self, db: Session, **kwargs) -> ModelType | None:
        """Создать новый объект.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры объекта.

        Returns:
            Созданный объект модели с ID или None при ошибке.
        """
        try:
            obj = self.model(**kwargs)
            db.add(obj)
            db.flush()
            db.refresh(obj)
            logger.info(
                "Объект создан: model=%s, id=%s", self.model.__name__, obj.id
            )
            return obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании объекта: %s", e)
            raise

    def update(self, obj_id: Any, db: Session, **kwargs) -> ModelType | None:
        """Обновить объект по ID.

        Args:
            obj_id: Идентификатор объекта.
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленный объект модели или None, если не найден.
        """
        try:
            obj = db.execute(
                select(self.model).where(self.model.id == obj_id)
            ).scalar_one_or_none()
            if not obj:
                logger.warning(
                    "Объект не найден для обновления: model=%s, id=%s",
                    self.model.__name__,
                    obj_id,
                )
                return None
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            db.flush()
            db.refresh(obj)
            logger.info("Объект обновлен: model=%s, id=%s", self.model.__name__, obj_id)
            return obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении объекта id=%s: %s", obj_id, e)
            raise

    def delete(self, obj_id: Any, db: Session) -> bool:
        """Удалить объект по ID.

        Args:
            obj_id: Идентификатор объекта.
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если объект не найден.
        """
        try:
            obj = db.execute(
                select(self.model).where(self.model.id == obj_id)
            ).scalar_one_or_none()
            if not obj:
                logger.warning(
                    "Объект не найден для удаления: model=%s, id=%s",
                    self.model.__name__,
                    obj_id,
                )
                return False
            db.delete(obj)
            db.flush()
            logger.info("Объект удален: model=%s, id=%s", self.model.__name__, obj_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении объекта id=%s: %s", obj_id, e)
            raise

    def filter_by(self, db: Session, **filters) -> list[ModelType]:
        """Получить объекты по фильтрам.

        Args:
            db: Сессия базы данных.
            **filters: Поля и значения для фильтрации.

        Returns:
            Список объектов, соответствующих фильтрам.
        """
        try:
            query = select(self.model)
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
            result = db.execute(query).scalars().all()
            logger.info(
                "Фильтрация объектов: model=%s, filters=%s, count=%s",
                self.model.__name__,
                filters,
                len(result),
            )
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при фильтрации объектов: %s", e)
            raise
