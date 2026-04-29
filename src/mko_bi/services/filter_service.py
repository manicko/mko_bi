"""Сервис управления глобальными фильтрами.

Предоставляет бизнес-логику для CRUD операций с фильтрами.
Все операции выполняются через FilterRepository с валидацией,
проверкой прав и логированием.
"""

from typing import Any

import logging
import re

from mko_bi.db.models import filters as filter_model
from mko_bi.db.repositories.filter_repo import FilterRepository
from sqlalchemy.orm import Session
from mko_bi.db.session import get_session
from mko_bi.models.filters import FilterRead
from mko_bi.models.user_roles import FilterTypeEnum

logger = logging.getLogger(__name__)

# Допустимые типы фильтров (берем из FilterTypeEnum)


def _validate_filter_type(filter_type: str) -> None:
    """Проверяет, что тип фильтра является допустимым.

    Args:
        filter_type: Тип фильтра для проверки.

    Raises:
        ValueError: Если тип фильтра не входит в список допустимых.
    """
    try:
        FilterTypeEnum(filter_type)
    except ValueError:
        logger.error(
            "Недопустимый тип фильтра: '%s'. Допустимые: %s",
            filter_type,
            sorted([e.value for e in FilterTypeEnum]),
        )
        raise ValueError(
            f"Недопустимый тип фильтра: '{filter_type}'. "
            f"Допустимые значения: {', '.join(sorted([e.value for e in FilterTypeEnum]))}"
        ) from None


def _validate_filter_name(name: str) -> None:
    """Проверяет валидность имени фильтра.

    Имя должно быть непустой строкой, не превышать 255 символов
    и содержать только допустимые символы.

    Args:
        name: Имя фильтра для проверки.

    Raises:
        ValueError: Если имя некорректно.
    """
    if not name or not name.strip():
        logger.error("Имя фильтра не может быть пустым")
        raise ValueError("Имя фильтра не может быть пустым")

    if len(name) > 255:
        logger.error("Имя фильтра слишком длинное: %s (длина: %s)", name, len(name))
        raise ValueError("Имя фильтра не должно превышать 255 символов")

    # Проверяем, что имя содержит только допустимые символы
    # (буквы, цифры, пробелы, дефисы, подчеркивания, точки)
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_.]+$', name):
        logger.error("Некорректные символы в имени фильтра: %s", name)
        raise ValueError(
            "Имя фильтра может содержать только буквы, цифры, "
            "пробелы, дефисы, подчеркивания и точки"
        )


def _validate_filter_config(config: dict[str, Any]) -> None:
    """Проверяет валидность конфигурации фильтра.

    Args:
        config: Конфигурация фильтра для проверки.

    Raises:
        ValueError: Если конфигурация некорректна.
    """
    if not isinstance(config, dict):
        logger.error("Конфигурация фильтра должна быть словарем")
        raise ValueError("Конфигурация фильтра должна быть словарем")

    # Базовая проверка: конфиг должен содержать хотя бы одно поле
    if not config:
        logger.error("Конфигурация фильтра не может быть пустой")
        raise ValueError("Конфигурация фильтра не может быть пустой")

    # Проверяем наличие обязательных полей в зависимости от типа фильтра
    # Для всех типов требуется хотя бы поле 'field'
    if 'field' not in config:
        logger.error("В конфигурации фильтра отсутствует обязательное поле 'field'")
        raise ValueError(
            "Конфигурация фильтра должна содержать поле 'field' "
            "с указанием поля для фильтрации"
        )


def _validate_filter_exists(
    filter_id: int, db: Session
) -> filter_model.Filter | None:
    """Проверяет существование фильтра и возвращает его модель.

    Args:
        filter_id: ID фильтра.
        db: Сессия базы данных.

    Returns:
        Модель фильтра или None, если не найден.
    """
    filter_obj = FilterRepository.get(filter_id, db)
    if filter_obj is None:
        logger.warning("Фильтр не найден: id=%s", filter_id)
    return filter_obj


def _check_filter_name_uniqueness(name: str, db: Session, exclude_id: int | None = None) -> None:
    """Проверяет уникальность имени фильтра.

    Args:
        name: Имя фильтра для проверки.
        db: Сессия базы данных.
        exclude_id: ID фильтра, который нужно исключить из проверки
            (используется при обновлении фильтра).

    Raises:
        ValueError: Если фильтр с таким именем уже существует.
    """
    existing = FilterRepository.get_by_name(name, db)
    if existing and (exclude_id is None or existing.id != exclude_id):
        logger.warning("Фильтр с таким именем уже существует: name=%s", name)
        raise ValueError(f"Фильтр с именем '{name}' уже существует")


def create_filter(
    name: str, type: str,     config: dict[str, Any], db: Session | None = None
) -> FilterRead:
    """Создает новый глобальный фильтр.

    Выполняет валидацию имени, типа и конфигурации фильтра,
    проверяет уникальность имени и сохраняет фильтр в базе данных.

    Args:
        name: Имя фильтра. Должно быть уникальным.
        type: Тип фильтра (select, multiselect, range, date).
        config: Конфигурация фильтра в формате JSON-совместимого dict.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        FilterRead: Модель созданного фильтра.

    Raises:
        ValueError: Если данные некорректны или фильтр с таким именем уже существует.
        SQLAlchemyError: При ошибке базы данных.

    Example:
        >>> filter_obj = create_filter(
        ...     name="Year Filter",
        ...     type="select",
        ...     config={"field": "year", "source": "dims", "multi": False},
        ... )
        >>> filter_obj.name
        'Year Filter'
    """
    logger.info("Начало создания фильтра: name=%s, type=%s", name, type)

    # Валидация данных
    _validate_filter_name(name)
    _validate_filter_type(type)
    _validate_filter_config(config)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка уникальности имени
        _check_filter_name_uniqueness(name, db)

        # Создание фильтра через репозиторий
        filter_obj = FilterRepository.create(
            db=db,
            name=name,
            type=type,
            config=config,
        )
        logger.info(
            "Фильтр успешно создан: id=%s, name=%s, type=%s",
            filter_obj.id,
            filter_obj.name,
            filter_obj.type,
        )

        # Преобразование в Pydantic модель
        return FilterRead.model_validate(filter_obj)

    except ValueError:
        # Валидационные ошибки не требуют отката (транзакция еще не начата)
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error(
            "Ошибка при создании фильтра name=%s, type=%s: %s",
            name,
            type,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


def get_filter(filter_id: int, db: Session | None = None) -> FilterRead | None:
    """Получает фильтр по ID.

    Args:
        filter_id: ID фильтра.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        FilterRead: Модель фильтра, или None если не найден.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Запрос фильтра: id=%s", filter_id)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        filter_obj = FilterRepository.get(filter_id, db)
        if filter_obj is None:
            logger.warning("Фильтр не найден: id=%s", filter_id)
            return None

        logger.info("Фильтр получен: id=%s, name=%s", filter_id, filter_obj.name)
        return FilterRead.model_validate(filter_obj)

    except Exception as e:
        logger.error("Ошибка при получении фильтра id=%s: %s", filter_id, e)
        raise
    finally:
        if local_session:
            db.close()


def get_filters(db: Session | None = None) -> list[FilterRead]:
    """Получает список всех фильтров.

    Args:
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        list[FilterRead]: Список моделей фильтров.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Получение списка всех фильтров")

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        filters = FilterRepository.get_all(db)
        logger.info("Получено фильтров: %s", len(filters))

        # Преобразование в Pydantic модели
        return [FilterRead.model_validate(f) for f in filters]

    except Exception as e:
        logger.error("Ошибка при получении списка фильтров: %s", e)
        raise
    finally:
        if local_session:
            db.close()


def update_filter(
    filter_id: int,
    name: str | None = None,
    type: str | None = None,
    config: dict[str, Any] | None = None,
    db: Session | None = None,
) -> FilterRead | None:
    """Обновляет данные фильтра.

    Проверяет валидность новых данных и уникальность имени (если оно изменяется).
    Обновляет только те поля, которые переданы (не None).

    Args:
        filter_id: ID фильтра для обновления.
        name: Новое имя фильтра (опционально).
        type: Новый тип фильтра (опционально).
        config: Новая конфигурация фильтра (опционально).
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        FilterRead: Модель обновленного фильтра, или None если не найден.

    Raises:
        ValueError: Если данные некорректны или имя уже занято.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Обновление фильтра: id=%s", filter_id)

    # Валидация переданных данных (если они есть)
    if name is not None:
        _validate_filter_name(name)
    if type is not None:
        _validate_filter_type(type)
    if config is not None:
        _validate_filter_config(config)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка существования фильтра
        filter_obj = _validate_filter_exists(filter_id, db)
        if filter_obj is None:
            return None

        # Проверка уникальности имени (если оно меняется)
        if name is not None and name != filter_obj.name:
            _check_filter_name_uniqueness(name, db, exclude_id=filter_id)

        # Подготовка данных для обновления
        update_data: dict[str, str | dict[str, Any]] = {}
        if name is not None:
            update_data["name"] = name
        if type is not None:
            update_data["type"] = type
        if config is not None:
            update_data["config"] = config

        # Обновление через репозиторий
        updated = FilterRepository.update(filter_id, db, **update_data)
        if updated is None:
            logger.warning("Не удалось обновить фильтр: id=%s", filter_id)
            return None

        logger.info("Фильтр успешно обновлен: id=%s", filter_id)
        return FilterRead.model_validate(updated)

    except ValueError:
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при обновлении фильтра id=%s: %s", filter_id, e)
        raise
    finally:
        if local_session:
            db.close()


def delete_filter(filter_id: int, db: Session | None = None) -> bool:
    """Удаляет фильтр.

    Args:
        filter_id: ID фильтра для удаления.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        bool: True, если удаление успешно, False - если фильтр не найден.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Удаление фильтра: id=%s", filter_id)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка существования фильтра
        filter_obj = _validate_filter_exists(filter_id, db)
        if filter_obj is None:
            return False

        # Удаление через репозиторий
        result = FilterRepository.delete(filter_id, db)

        if result:
            logger.info("Фильтр успешно удален: id=%s", filter_id)
        else:
            logger.warning("Не удалось удалить фильтр: id=%s", filter_id)

        return result

    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при удалении фильтра id=%s: %s", filter_id, e)
        raise
    finally:
        if local_session:
            db.close()