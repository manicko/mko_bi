"""Сервис управления настройками обработки.

Предоставляет бизнес-логику для операций с настройками обработки данных.
Все операции выполняются через ProcessingConfigRepository с валидацией,
проверкой прав и логированием.
"""

import json
import logging
from typing import Any
from uuid import UUID

from mko_bi.db.repositories.processing_config_repo import ProcessingConfigRepository
from mko_bi.core.permissions import check_dashboard_access
from sqlalchemy.orm import Session
from mko_bi.db.session import get_session
from mko_bi.models.processing_configs import (
    ProcessingConfigRead,
)
from mko_bi.models.dashboard import DashboardRead

logger = logging.getLogger(__name__)


def _validate_settings(settings: dict[str, Any]) -> None:
    """Проверяет валидность структуры настроек обработки.

    Проверяет наличие обязательных полей и корректность значений.

    Args:
        settings: Настройки обработки для проверки.

    Raises:
        ValueError: Если структура настроек некорректна.
    """
    if not isinstance(settings, dict):
        logger.error("Настройки должны быть словарем")
        raise ValueError("Настройки должны быть словарем")

    if not settings:
        logger.error("Настройки не могут быть пустыми")
        raise ValueError("Настройки не могут быть пустыми")

    # Проверка обязательных полей
    required_fields = ["loader", "date_column", "timezone"]
    missing_fields = [field for field in required_fields if field not in settings]
    if missing_fields:
        logger.error("Отсутствуют обязательные поля: %s", missing_fields)
        raise ValueError(
            f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
        )

    # Проверка типа значений обязательных полей
    for field in required_fields:
        if not isinstance(settings.get(field), str) or not settings[field].strip():
            logger.error("Поле '%s' должно быть непустой строкой", field)
            raise ValueError(f"Поле '{field}' должно быть непустой строкой")

    logger.debug("Структура настроек валидна: %s", list(settings.keys()))


def _validate_dashboard_exists(
    dashboard_id: UUID, db: "Session"
) -> DashboardRead | None:
    """Проверяет существование дашборда.

    Args:
        dashboard_id: Идентификатор дашборда.
        db: Сессия базы данных.

    Returns:
        Модель дашборда или None, если не найден.
    """
    from mko_bi.db.repositories.dashboard_repo import DashboardRepository

    dashboard_obj = DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        logger.warning("Дашборд не найден: dashboard_id=%s", dashboard_id)
        return None

    # Преобразуем в Pydantic модель
    dashboard_dict = dashboard_obj.__dict__.copy()
    if isinstance(dashboard_dict.get("config"), str):
        dashboard_dict["config"] = json.loads(dashboard_dict["config"])
    return DashboardRead.model_validate(dashboard_dict)


def _check_write_permission(
    user_id: UUID, dashboard_id: UUID, db: "Session"
) -> bool:
    """Проверяет право на изменение настроек дашборда.

    Для изменения настроек требуется роль editor или admin.

    Args:
        user_id: Идентификатор пользователя.
        dashboard_id: Идентификатор дашборда.
        db: Сессия базы данных.

    Returns:
        True, если у пользователя есть права на запись.
    """
    has_access: bool = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на изменение настроек: user_id=%s, dashboard_id=%s",
            user_id,
            dashboard_id,
        )
    return has_access


def _check_read_permission(
    user_id: UUID, dashboard_id: UUID, db: "Session"
) -> bool:
    """Проверяет право на чтение настроек дашборда.

    Для чтения настроек требуется роль viewer, editor или admin.

    Args:
        user_id: Идентификатор пользователя.
        dashboard_id: Идентификатор дашборда.
        db: Сессия базы данных.

    Returns:
        True, если у пользователя есть права на чтение.
    """
    has_access: bool = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на чтение настроек: user_id=%s, dashboard_id=%s",
            user_id,
            dashboard_id,
        )
    return has_access


def create_or_update_config(
    dashboard_id: UUID,
    settings: dict[str, Any],
    db: "Session | None" = None,
) -> ProcessingConfigRead:
    """Создает или обновляет настройки обработки для дашборда.

    Если настройки для дашборда уже существуют - обновляет их,
    иначе создает новые. Обновляет поле updated_at.

    Args:
        dashboard_id: Идентификатор дашборда.
        settings: Настройки обработки в формате JSON-совместимого dict.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        ProcessingConfigRead: Модель настроек обработки.

    Raises:
        ValueError: Если структура настроек некорректна или дашборд не найден.
        SQLAlchemyError: При ошибке базы данных.

    Example:
        >>> config = create_or_update_config(
        ...     dashboard_id=uuid4(),
        ...     settings={
        ...         "loader": "sales_loader",
        ...         "date_column": "event_date",
        ...         "timezone": "UTC",
        ...     },
        ...     db=session
        ... )
    """
    logger.info("Создание/обновление настроек: dashboard_id=%s", dashboard_id)

    # Валидация структуры настроек
    _validate_settings(settings)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка существования дашборда
        dashboard_obj = _validate_dashboard_exists(dashboard_id, db)
        if dashboard_obj is None:
            raise ValueError(f"Дашборд с id={dashboard_id} не найден")

        # Проверяем, существуют ли уже настройки
        existing_config = ProcessingConfigRepository.get(dashboard_id, db)

        if existing_config:
            # Обновление существующих настроек
            updated = ProcessingConfigRepository.update(
                dashboard_id=dashboard_id,
                db=db,
                settings=settings,
            )
            if updated is None:
                raise ValueError(f"Не удалось обновить настройки для дашборда {dashboard_id}")
            logger.info("Настройки обновлены: dashboard_id=%s", dashboard_id)
            config_obj = updated
        else:
            # Создание новых настроек
            config_obj = ProcessingConfigRepository.create(
                db=db,
                dashboard_id=dashboard_id,
                settings=settings,
            )
            if config_obj is None:
                raise ValueError(f"Не удалось создать настройки для дашборда {dashboard_id}")
            logger.info("Настройки созданы: dashboard_id=%s", dashboard_id)

        # Преобразование в Pydantic модель
        config_dict = config_obj.__dict__.copy()
        return ProcessingConfigRead.model_validate(config_dict)

    except ValueError:
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error(
            "Ошибка при создании/обновлении настроек dashboard_id=%s: %s",
            dashboard_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


def get_config(
    dashboard_id: UUID,
    user_id: UUID,
    db: "Session | None" = None,
) -> ProcessingConfigRead | None:
    """Получает настройки обработки для дашборда с проверкой прав.

    Args:
        dashboard_id: Идентификатор дашборда.
        user_id: Идентификатор пользователя, запрашивающего настройки.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        ProcessingConfigRead: Модель настроек обработки, или None если не найдены
            или у пользователя нет прав на чтение.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Запрос настроек: dashboard_id=%s, user_id=%s",
        dashboard_id,
        user_id,
    )

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка прав на чтение
        if not _check_read_permission(user_id, dashboard_id, db):
            return None

        # Получение настроек
        config_obj = ProcessingConfigRepository.get(dashboard_id, db)
        if config_obj is None:
            logger.warning("Настройки не найдены: dashboard_id=%s", dashboard_id)
            return None

        logger.info("Настройки предоставлены: dashboard_id=%s", dashboard_id)

        # Преобразование в Pydantic модель
        config_dict = config_obj.__dict__.copy()
        return ProcessingConfigRead.model_validate(config_dict)

    except Exception as e:
        logger.error(
            "Ошибка при получении настроек dashboard_id=%s, user_id=%s: %s",
            dashboard_id,
            user_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


def update_config(
    dashboard_id: UUID,
    settings: dict[str, Any],
    user_id: UUID,
    db: "Session | None" = None,
) -> ProcessingConfigRead | None:
    """Обновляет настройки обработки для дашборда с проверкой прав.

    Args:
        dashboard_id: Идентификатор дашборда.
        settings: Новые настройки обработки.
        user_id: Идентификатор пользователя, выполняющего обновление.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        ProcessingConfigRead: Обновленная модель настроек, или None если
            настройки не найдены или у пользователя нет прав.

    Raises:
        ValueError: Если структура настроек некорректна.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Обновление настроек: dashboard_id=%s, user_id=%s",
        dashboard_id,
        user_id,
    )

    # Валидация структуры настроек
    _validate_settings(settings)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка прав на запись
        if not _check_write_permission(user_id, dashboard_id, db):
            return None

        # Проверка существования дашборда
        dashboard_obj = _validate_dashboard_exists(dashboard_id, db)
        if dashboard_obj is None:
            raise ValueError(f"Дашборд с id={dashboard_id} не найден")

        # Обновление настроек
        updated = ProcessingConfigRepository.update(
            dashboard_id=dashboard_id,
            db=db,
            settings=settings,
        )

        if updated is None:
            logger.warning("Не удалось обновить настройки: dashboard_id=%s", dashboard_id)
            return None

        logger.info("Настройки успешно обновлены: dashboard_id=%s", dashboard_id)

        # Преобразование в Pydantic модель
        config_dict = updated.__dict__.copy()
        return ProcessingConfigRead.model_validate(config_dict)

    except ValueError:
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error(
            "Ошибка при обновлении настроек dashboard_id=%s, user_id=%s: %s",
            dashboard_id,
            user_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()