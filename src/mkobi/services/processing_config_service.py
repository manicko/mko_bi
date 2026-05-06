"""Сервис управления настройками обработки.

Предоставляет бизнес-логику для операций с настройками обработки данных.
Все операции выполняются асинхронно через ProcessingConfigRepository.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.repositories.processing_config_repo import ProcessingConfigRepository
from mkobi.interfaces.service_interfaces import IProcessingConfigService
from mkobi.models.processing_configs import (
    ProcessingConfigRead,
)
from mkobi.models.types import ProcessingSettingsDict

logger = logging.getLogger(__name__)


class ProcessingConfigService(IProcessingConfigService):
    """Сервис управления настройками обработки.

    Реализует интерфейс IProcessingConfigService и предоставляет
    методы для создания, получения, обновления и удаления настроек.

    Attributes:
        db: Асинхронная сессия базы данных.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Инициализация сервиса.

        Args:
            db: Асинхронная сессия базы данных.
        """
        self.db = db

    async def get_by_dashboard_id(
        self,
        dashboard_id: UUID,
    ) -> ProcessingConfigRead | None:
        """Получает настройки обработки по ID дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.

        Returns:
            ProcessingConfigRead или None, если не найдены.
        """
        logger.info("Запрос настроек: dashboard_id=%s", dashboard_id)
        config_obj = await ProcessingConfigRepository.get(dashboard_id, self.db)
        if config_obj is None:
            logger.warning("Настройки не найдены: dashboard_id=%s", dashboard_id)
            return None

        logger.info("Настройки предоставлены: dashboard_id=%s", dashboard_id)
        return ProcessingConfigRead.model_validate(config_obj.__dict__)

    async def upsert(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
    ) -> ProcessingConfigRead:
        """Создает или обновляет настройки обработки.

        Args:
            dashboard_id: Идентификатор дашборда.
            settings: Настройки обработки.

        Returns:
            ProcessingConfigRead: Модель настроек.

        Raises:
            ValueError: Если структура настроек некорректна.
        """
        logger.info("Upsert настроек: dashboard_id=%s", dashboard_id)
        _validate_settings(settings)

        existing = await ProcessingConfigRepository.get(dashboard_id, self.db)
        if existing:
            updated = await ProcessingConfigRepository.update(
                dashboard_id=dashboard_id,
                db=self.db,
                settings=settings,
            )
            if updated is None:
                raise ValueError(f"Не удалось обновить настройки для дашборда {dashboard_id}")
            logger.info("Настройки обновлены: dashboard_id=%s", dashboard_id)
            return ProcessingConfigRead.model_validate(updated.__dict__)
        else:
            created = await ProcessingConfigRepository.create(
                db=self.db,
                dashboard_id=dashboard_id,
                settings=settings,
            )
            if created is None:
                raise ValueError(f"Не удалось создать настройки для дашборда {dashboard_id}")
            logger.info("Настройки созданы: dashboard_id=%s", dashboard_id)
            return ProcessingConfigRead.model_validate(created.__dict__)

    async def delete(
        self,
        dashboard_id: UUID,
    ) -> bool:
        """Удаляет настройки обработки.

        Args:
            dashboard_id: Идентификатор дашборда.

        Returns:
            True, если удаление успешно.
        """
        logger.info("Удаление настроек: dashboard_id=%s", dashboard_id)
        result: bool = await ProcessingConfigRepository.delete(dashboard_id, self.db)
        if result:
            logger.info("Настройки удалены: dashboard_id=%s", dashboard_id)
        else:
            logger.warning("Настройки не найдены для удаления: dashboard_id=%s", dashboard_id)
        return result

    # ========== Методы интерфейса IProcessingConfigService ==========

    async def create_processing_config(
        self, dashboard_id: UUID, settings: ProcessingSettingsDict
    ) -> ProcessingConfigRead:
        """Создает настройки обработки для дашборда."""
        return await self.upsert(dashboard_id, settings)

    async def get_processing_config_by_dashboard(
        self, dashboard_id: UUID
    ) -> ProcessingConfigRead | None:
        """Получает настройки обработки по ID дашборда."""
        return await self.get_by_dashboard_id(dashboard_id)

    async def update_processing_config(
        self, dashboard_id: UUID, settings: ProcessingSettingsDict
    ) -> ProcessingConfigRead | None:
        """Обновляет настройки обработки."""
        return await self.upsert(dashboard_id, settings)

    async def delete_processing_config(self, dashboard_id: UUID) -> bool:
        """Удаляет настройки обработки."""
        return await self.delete(dashboard_id)


# ========== Функции для обратной совместимости ==========

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
    service = ProcessingConfigService(db)
    return await service.get_by_dashboard_id(dashboard_id)


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
    service = ProcessingConfigService(db)
    return await service.upsert(dashboard_id, settings)


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
    service = ProcessingConfigService(db)
    return await service.delete(dashboard_id)


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
