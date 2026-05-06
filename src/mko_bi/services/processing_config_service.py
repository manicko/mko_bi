"""Сервис управления настройками обработки.

Предоставляет бизнес-логику для операций с настройками обработки данных.
Все операции выполняются асинхронно через ProcessingConfigRepository.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.db.repositories.processing_config_repo import ProcessingConfigRepository
from mko_bi.models.processing_configs import (
    ProcessingConfigRead,
)
from mko_bi.models.types import ProcessingSettingsDict

logger = logging.getLogger(__name__)


async def get_by_dashboard_id(
    dashboard_id: UUID,
    db: AsyncSession,
) -> ProcessingConfigRead | None:
    """Получает настройки обработки по ID дашборда.

    Args:
        dashboard_id: Идентификатор дашборда.
        db: Асинхронная сессия БД.

    Returns:
        ProcessingConfigRead или None, если не найдены.
    """
    logger.info("Запрос настроек: dashboard_id=%s", dashboard_id)
    config_obj = await ProcessingConfigRepository.get(dashboard_id, db)
    if config_obj is None:
        logger.warning("Настройки не найдены: dashboard_id=%s", dashboard_id)
        return None

    logger.info("Настройки предоставлены: dashboard_id=%s", dashboard_id)
    return ProcessingConfigRead.model_validate(config_obj.__dict__)


async def upsert(
    dashboard_id: UUID,
    settings: ProcessingSettingsDict,
    db: AsyncSession,
) -> ProcessingConfigRead:
    """Создает или обновляет настройки обработки.

    Args:
        dashboard_id: Идентификатор дашборда.
        settings: Настройки обработки.
        db: Асинхронная сессия БД.

    Returns:
        ProcessingConfigRead: Модель настроек.

    Raises:
        ValueError: Если структура настроек некорректна.
    """
    logger.info("Upsert настроек: dashboard_id=%s", dashboard_id)
    _validate_settings(settings)

    existing = await ProcessingConfigRepository.get(dashboard_id, db)
    if existing:
        updated = await ProcessingConfigRepository.update(
            dashboard_id=dashboard_id,
            db=db,
            settings=settings,
        )
        if updated is None:
            raise ValueError(f"Не удалось обновить настройки для дашборда {dashboard_id}")
        logger.info("Настройки обновлены: dashboard_id=%s", dashboard_id)
        return ProcessingConfigRead.model_validate(updated.__dict__)
    else:
        created = await ProcessingConfigRepository.create(
            db=db,
            dashboard_id=dashboard_id,
            settings=settings,
        )
        if created is None:
            raise ValueError(f"Не удалось создать настройки для дашборда {dashboard_id}")
        logger.info("Настройки созданы: dashboard_id=%s", dashboard_id)
        return ProcessingConfigRead.model_validate(created.__dict__)


async def delete(
    dashboard_id: UUID,
    db: AsyncSession,
) -> bool:
    """Удаляет настройки обработки.

    Args:
        dashboard_id: Идентификатор дашборда.
        db: Асинхронная сессия БД.

    Returns:
        True, если удаление успешно.
    """
    logger.info("Удаление настроек: dashboard_id=%s", dashboard_id)
    result: bool = await ProcessingConfigRepository.delete(dashboard_id, db)
    if result:
        logger.info("Настройки удалены: dashboard_id=%s", dashboard_id)
    else:
        logger.warning("Настройки не найдены для удаления: dashboard_id=%s", dashboard_id)
    return result


def _validate_settings(settings: ProcessingSettingsDict) -> None:
    """Проверяет валидность структуры настроек.

    Args:
        settings: Настройки обработки.

    Raises:
        ValueError: Если структура настроек некорректна.
    """
    if not isinstance(settings, dict):
        raise ValueError("Настройки должны быть словарем")

    if not settings:
        raise ValueError("Настройки не могут быть пустыми")

    required_fields = ["loader", "date_column", "timezone"]
    missing_fields = [field for field in required_fields if field not in settings]
    if missing_fields:
        raise ValueError(f"Отсутствуют обязательные поля: {', '.join(missing_fields)}")

    for field in required_fields:
        if not isinstance(settings.get(field), str) or not settings[field].strip():
            raise ValueError(f"Поле '{field}' должно быть непустой строкой")
