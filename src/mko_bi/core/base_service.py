"""Базовый сервис с общей логикой.

Предоставляет базовый класс для сервисов с общими методами
валидации, обработки транзакций и управления репозиториями.
"""

import logging
from typing import TypeVar, Any

from sqlalchemy.orm import Session

from mko_bi.core.base_repository import BaseRepository
from mko_bi.db.session import get_session

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)

class BaseService[ModelType, RepositoryType]:
    """Базовый сервис с общей логикой.

    Generic класс для сервисов. Предоставляет общие методы
    для работы с репозиториями и управления транзакциями.

    Attributes:
        repository: Экземпляр репозитория для работы с данными.
    """

    def __init__(self, repository: RepositoryType) -> None:
        """Инициализация сервиса.

        Args:
            repository: Экземпляр репозитория.
        """
        self.repository = repository

    def get_by_id(
        self, obj_id: Any, db: Session | None = None
    ) -> dict[str, Any] | None:
        """Получить объект по ID.

        Args:
            obj_id: Идентификатор объекта.
            db: Опциональная сессия базы данных.

        Returns:
            Данные объекта в виде словаря или None.
        """
        local_session = False
        if db is None:
            db = get_session().__enter__()
            local_session = True

        try:
            obj = self.repository.get(obj_id, db)
            if obj:
                logger.info(
                    "Объект получен через сервис: model=%s, id=%s",
                    self.repository.model.__name__,
                    obj_id,
                )
                return self._to_dict(obj)
            else:
                logger.warning(
                    "Объект не найден через сервис: model=%s, id=%s",
                    self.repository.model.__name__,
                    obj_id,
                )
                return None
        except Exception as e:
            logger.error("Ошибка при получении объекта id=%s: %s", obj_id, e)
            raise
        finally:
            if local_session:
                db.close()

    def get_all(
        self, db: Session | None = None, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Получить список всех объектов.

        Args:
            db: Опциональная сессия базы данных.
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.

        Returns:
            Список объектов в виде словарей.
        """
        local_session = False
        if db is None:
            db = get_session().__enter__()
            local_session = True

        try:
            objs = self.repository.get_all(db, skip, limit)
            logger.info(
                "Получен список объектов через сервис: model=%s, count=%s",
                self.repository.model.__name__,
                len(objs),
            )
            return [self._to_dict(obj) for obj in objs]
        except Exception as e:
            logger.error("Ошибка при получении списка объектов: %s", e)
            raise
        finally:
            if local_session:
                db.close()

    def create(self, db: Session, **kwargs) -> dict[str, Any] | None:
        """Создать новый объект.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры объекта.

        Returns:
            Данные созданного объекта в виде словаря.
        """
        try:
            obj = self.repository.create(db, **kwargs)
            if obj:
                logger.info(
                    "Объект создан через сервис: model=%s, id=%s",
                    self.repository.model.__name__,
                    obj.id,
                )
                return self._to_dict(obj)
            return None
        except Exception as e:
            logger.error("Ошибка при создании объекта: %s", e)
            raise

    def update(
        self, obj_id: Any, db: Session, **kwargs
    ) -> dict[str, Any] | None:
        """Обновить объект.

        Args:
            obj_id: Идентификатор объекта.
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Данные обновленного объекта в виде словаря.
        """
        try:
            obj = self.repository.update(obj_id, db, **kwargs)
            if obj:
                logger.info(
                    "Объект обновлен через сервис: model=%s, id=%s",
                    self.repository.model.__name__,
                    obj_id,
                )
                return self._to_dict(obj)
            return None
        except Exception as e:
            logger.error("Ошибка при обновлении объекта id=%s: %s", obj_id, e)
            raise

    def delete(self, obj_id: Any, db: Session) -> bool:
        """Удалить объект.

        Args:
            obj_id: Идентификатор объекта.
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно.
        """
        try:
            result = self.repository.delete(obj_id, db)
            if result:
                logger.info(
                    "Объект удален через сервис: model=%s, id=%s",
                    self.repository.model.__name__,
                    obj_id,
                )
            return result
        except Exception as e:
            logger.error("Ошибка при удалении объекта id=%s: %s", obj_id, e)
            raise

    def _to_dict(self, obj: ModelType) -> dict[str, Any]:
        """Преобразовать объект модели в словарь.

        Может быть переопределен в дочерних классах для
        использования Pydantic моделей или других методов.

        Args:
            obj: Объект модели.

        Returns:
            Словарь с данными объекта.
        """
        if hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return {}

    def validate_data(self, **kwargs) -> None:
        """Валидация данных перед созданием/обновлением.

        Должен быть переопределен в дочерних классах.

        Args:
            **kwargs: Данные для валидации.

        Raises:
            ValueError: Если данные некорректны.
        """
        pass
