"""Сервис управления глобальными фильтрами.

Предоставляет бизнес-логику для CRUD операций с фильтрами.
Все операции выполняются через FilterRepository с валидацией,
проверкой прав и логированием.

Реализует интерфейс IFilterService для внедрения зависимостей.
"""

from typing import Any

import logging
import re

from sqlalchemy.orm import Session

from mkobi.db.models import filters as filter_model
from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.db.session import get_session
from mkobi.interfaces.service_interfaces import IFilterService
from mkobi.models.filters import FilterRead
from mkobi.models.enums import FilterType

logger = logging.getLogger(__name__)


class FilterService(IFilterService):
    """Класс сервиса для управления фильтрами."""

    def __init__(self, db: Session | None = None):
        """Инициализация сервиса.

        Args:
            db: Сессия базы данных (опционально).
        """
        self._db = db

    def _validate_filter_type(self, filter_type: str) -> None:
        """Проверяет, что тип фильтра является допустимым."""
        try:
            FilterType(filter_type)
        except ValueError:
            logger.error(
                "Недопустимый тип фильтра: '%s'. Допустимые: %s",
                filter_type,
                sorted([e.value for e in FilterType]),
            )
            raise ValueError(
                f"Недопустимый тип фильтра: '{filter_type}'. "
                f"Допустимые значения: {', '.join(sorted([e.value for e in FilterType]))}"
            ) from None

    def _validate_filter_name(self, name: str) -> None:
        """Проверяет валидность имени фильтра."""
        if not name or not name.strip():
            logger.error("Имя фильтра не может быть пустым")
            raise ValueError("Имя фильтра не может быть пустым")

        if len(name) > 255:
            logger.error("Имя фильтра слишком длинное: %s (длина: %s)", name, len(name))
            raise ValueError("Имя фильтра не должно превышать 255 символов")

        if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_.]+$', name):
            logger.error("Некорректные символы в имени фильтра: %s", name)
            raise ValueError(
                "Имя фильтра может содержать только буквы, цифры, "
                "пробелы, дефисы, подчеркивания и точки"
            )

    def _validate_filter_config(self, config: dict[str, Any]) -> None:
        """Проверяет валидность конфигурации фильтра."""
        if not isinstance(config, dict):
            logger.error("Конфигурация фильтра должна быть словарем")
            raise ValueError("Конфигурация фильтра должна быть словарем")

        if not config:
            logger.error("Конфигурация фильтра не может быть пустой")
            raise ValueError("Конфигурация фильтра не может быть пустой")

        if 'field' not in config:
            logger.error("В конфигурации фильтра отсутствует обязательное поле 'field'")
            raise ValueError(
                "Конфигурация фильтра должна содержать поле 'field' "
                "с указанием поля для фильтрации"
            )

    def _validate_filter_exists(
        self, filter_id: int, db: Session
    ) -> filter_model.Filter | None:
        """Проверяет существование фильтра."""
        filter_obj = FilterRepository.get(filter_id, db)
        if filter_obj is None:
            logger.warning("Фильтр не найден: id=%s", filter_id)
        return filter_obj

    def _check_filter_name_uniqueness(
        self, name: str, db: Session, exclude_id: int | None = None
    ) -> None:
        """Проверяет уникальность имени фильтра."""
        existing = FilterRepository.get_by_name(name, db)
        if existing and (exclude_id is None or existing.id != exclude_id):
            logger.warning("Фильтр с таким именем уже существует: name=%s", name)
            raise ValueError(f"Фильтр с именем '{name}' уже существует")

    def create_filter(
        self,
        name: str,
        type_: str,
        config: dict[str, Any],
        db: Session | None = None,
    ) -> FilterRead:
        """Создает новый глобальный фильтр."""
        actual_db = db or self._db
        if actual_db is None:
            with get_session() as session:
                return self._create_filter_with_session(name, type_, config, session)
        return self._create_filter_with_session(name, type_, config, actual_db)

    def _create_filter_with_session(
        self, name: str, type_: str, config: dict[str, Any], db: Session
    ) -> FilterRead:
        """Внутренний метод создания фильтра."""
        self._validate_filter_name(name)
        self._validate_filter_type(type_)
        self._validate_filter_config(config)
        self._check_filter_name_uniqueness(name, db)

        try:
            filter_obj = FilterRepository.create(
                db=db,
                name=name,
                type=type_,
                config=config,
            )
            logger.info(
                "Фильтр успешно создан: id=%s, name=%s, type=%s",
                filter_obj.id,
                filter_obj.name,
                filter_obj.type,
            )
            return FilterRead.model_validate(filter_obj)
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Ошибка при создании фильтра name=%s, type=%s: %s",
                name,
                type_,
                e,
            )
            raise

    def get_filter(
        self, filter_id: int, db: Session | None = None
    ) -> FilterRead | None:
        """Получает фильтр по ID."""
        actual_db = db or self._db
        if actual_db is None:
            with get_session() as session:
                return self._get_filter_with_session(filter_id, session)
        return self._get_filter_with_session(filter_id, actual_db)

    def _get_filter_with_session(
        self, filter_id: int, db: Session
    ) -> FilterRead | None:
        """Внутренний метод получения фильтра."""
        filter_obj = FilterRepository.get(filter_id, db)
        if filter_obj is None:
            return None
        return FilterRead.model_validate(filter_obj)

    def get_filters(self, db: Session | None = None) -> list[FilterRead]:
        """Получает все фильтры."""
        actual_db = db or self._db
        if actual_db is None:
            with get_session() as session:
                return self._get_filters_with_session(session)
        return self._get_filters_with_session(actual_db)

    def _get_filters_with_session(self, db: Session) -> list[FilterRead]:
        """Внутренний метод получения всех фильтров."""
        filters = FilterRepository.get_all(db)
        return [FilterRead.model_validate(f) for f in filters]

    def update_filter(
        self,
        filter_id: int,
        name: str | None = None,
        type_: str | None = None,
        config: dict[str, Any] | None = None,
        db: Session | None = None,
    ) -> FilterRead | None:
        """Обновляет фильтр."""
        actual_db = db or self._db
        if actual_db is None:
            with get_session() as session:
                return self._update_filter_with_session(
                    filter_id, name, type_, config, session
                )
        return self._update_filter_with_session(
            filter_id, name, type_, config, actual_db
        )

    def _update_filter_with_session(
        self,
        filter_id: int,
        name: str | None,
        type_: str | None,
        config: dict[str, Any] | None,
        db: Session,
    ) -> FilterRead | None:
        """Внутренний метод обновления фильтра."""
        filter_obj = self._validate_filter_exists(filter_id, db)
        if filter_obj is None:
            return None

        if name is not None:
            self._validate_filter_name(name)
            self._check_filter_name_uniqueness(name, db, exclude_id=filter_id)
            FilterRepository.update(filter_id, {"name": name}, db)

        if type_ is not None:
            self._validate_filter_type(type_)
            FilterRepository.update(filter_id, {"type": type_}, db)

        if config is not None:
            self._validate_filter_config(config)
            FilterRepository.update(filter_id, {"config": config}, db)

        db.commit()

        updated = FilterRepository.get(filter_id, db)
        if updated:
            return FilterRead.model_validate(updated)
        return None

    def delete_filter(
        self, filter_id: int, db: Session | None = None
    ) -> bool:
        """Удаляет фильтр."""
        actual_db = db or self._db
        if actual_db is None:
            with get_session() as session:
                return self._delete_filter_with_session(filter_id, session)
        return self._delete_filter_with_session(filter_id, actual_db)

    def _delete_filter_with_session(self, filter_id: int, db: Session) -> bool:
        """Внутренний метод удаления фильтра."""
        result = FilterRepository.delete(filter_id, db)
        db.commit()
        if result:
            logger.info("Фильтр успешно удален: id=%s", filter_id)
        else:
            logger.warning("Фильтр не найден для удаления: id=%s", filter_id)
        return bool(result)


# --- Backward compatibility functions ---

def create_filter(
    name: str, type_: str, config: dict[str, Any], db: Session | None = None
) -> FilterRead:
    """Backward compatibility wrapper."""
    service = FilterService()
    return service.create_filter(name, type_, config, db)


def get_filter(
    filter_id: int, db: Session | None = None
) -> FilterRead | None:
    """Backward compatibility wrapper."""
    service = FilterService()
    return service.get_filter(filter_id, db)


def get_filters(db: Session | None = None) -> list[FilterRead]:
    """Backward compatibility wrapper."""
    service = FilterService()
    return service.get_filters(db)


def update_filter(
    filter_id: int,
    name: str | None = None,
    type_: str | None = None,
    config: dict[str, Any] | None = None,
    db: Session | None = None,
) -> FilterRead | None:
    """Backward compatibility wrapper."""
    service = FilterService()
    return service.update_filter(filter_id, name, type_, config, db)


def delete_filter(
    filter_id: int, db: Session | None = None
) -> bool:
    """Backward compatibility wrapper."""
    service = FilterService()
    return service.delete_filter(filter_id, db)
