"""Сервис управления layout-ами.

Предоставляет бизнес-логику для CRUD операций с layout-ами.
Все операции выполняются через LayoutRepository
с валидацией, проверкой и логированием.

Реализует интерфейс ILayoutService для внедрения зависимостей.
"""

import logging
from uuid import UUID
from typing import Any, cast

from mkobi.db.repositories.layout_repo import LayoutRepository
from mkobi.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from mkobi.models.layout import LayoutRead, LayoutUpdate

logger = logging.getLogger(__name__)


async def create_layout(
    name: str, definition: dict[str, Any], db: AsyncSession | None = None
) -> LayoutRead:
    """Создает новый layout.

    Args:
        name: Название layout-а.
        definition: Структура layout-а (grid, graphs, filters, bindings).
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        LayoutRead: Модель созданного layout-а.

    Raises:
        ValueError: Если layout с таким именем уже существует.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Начало создания layout: name=%s", name)

    # Проверка уникальности имени
    if db is None:
        async with get_session() as db:
            return await _create_layout_with_session(name, definition, db)
    else:
        return await _create_layout_with_session(name, definition, db)


async def _create_layout_with_session(
    name: str, definition: dict[str, Any], db: AsyncSession
) -> LayoutRead:
    """Внутренняя функция для создания layout с использованием сессии."""
    layout_repo = LayoutRepository()
    existing = await layout_repo.get_by_name(name, db)
    if existing:
        logger.error("Layout с таким именем уже существует: name=%s", name)
        raise ValueError(f"Layout с именем '{name}' уже существует")

    try:
        layout_obj = await layout_repo.create(db=db, name=name, definition=definition)
        await db.commit()

        if layout_obj is None:
            raise ValueError("Failed to create layout")

        logger.info("Layout создан: id=%s, name=%s", layout_obj.id, layout_obj.name)
        return cast(LayoutRead, LayoutRead.model_validate(layout_obj))
    except Exception as e:
        await db.rollback()
        logger.error("Ошибка при создании layout name=%s: %s", name, e)
        raise


async def get_layout(
    layout_id: UUID, db: AsyncSession | None = None
) -> LayoutRead | None:
    """Получает layout по ID.

    Args:
        layout_id: Идентификатор layout-а.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        LayoutRead: Модель layout-а, если найден, иначе None.
    """
    logger.info("Запрос layout: layout_id=%s", layout_id)

    if db is None:
        async with get_session() as db:
            return await _get_layout_with_session(layout_id, db)
    else:
        return await _get_layout_with_session(layout_id, db)


async def _get_layout_with_session(
    layout_id: UUID, db: AsyncSession
) -> LayoutRead | None:
    """Внутренняя функция для получения layout с использованием сессии."""
    layout_repo = LayoutRepository()
    layout_obj = await layout_repo.get(layout_id, db)
    if not layout_obj:
        return None
    return cast(LayoutRead, LayoutRead.model_validate(layout_obj))


async def get_all_layouts(db: AsyncSession | None = None) -> list[LayoutRead]:
    """Получает все layout-ы.

    Args:
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        list[LayoutRead]: Список всех layout-ов.
    """
    logger.info("Получение всех layout-ов")

    if db is None:
        async with get_session() as db:
            return await _get_all_layouts_with_session(db)
    else:
        return await _get_all_layouts_with_session(db)


async def _get_all_layouts_with_session(db: AsyncSession) -> list[LayoutRead]:
    """Внутренняя функция для получения всех layout-ов с использованием сессии."""
    layout_repo = LayoutRepository()
    layout_objs = await layout_repo.get_all(db)
    return [LayoutRead.model_validate(layout_obj) for layout_obj in layout_objs]


async def update_layout(
    layout_id: UUID, update_data: LayoutUpdate, db: AsyncSession | None = None
) -> LayoutRead | None:
    """Обновляет layout.

    Args:
        layout_id: Идентификатор layout-а.
        update_data: Данные для обновления.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        LayoutRead: Обновленная модель layout-а, или None если не найден.
    """
    logger.info("Обновление layout: layout_id=%s", layout_id)

    if db is None:
        async with get_session() as db:
            return await _update_layout_with_session(layout_id, update_data, db)
    else:
        return await _update_layout_with_session(layout_id, update_data, db)


async def _update_layout_with_session(
    layout_id: UUID, update_data: LayoutUpdate, db: AsyncSession
) -> LayoutRead | None:
    """Внутренняя функция для обновления layout с использованием сессии."""
    # Проверка существования
    layout_repo = LayoutRepository()
    existing = await layout_repo.get(layout_id, db)
    if not existing:
        logger.warning("Layout не найден для обновления: id=%s", layout_id)
        return None

    # Проверка уникальности имени при обновлении
    if update_data.name and update_data.name != existing.name:
        name_check = await layout_repo.get_by_name(update_data.name, db)
        if name_check:
            logger.error("Layout с таким именем уже существует: name=%s", update_data.name)
            raise ValueError(f"Layout с именем '{update_data.name}' уже существует")

    # Подготовка данных для обновления
    update_kwargs: dict[str, Any] = {}
    if update_data.name is not None:
        update_kwargs["name"] = update_data.name
    if update_data.definition is not None:
        update_kwargs["definition"] = update_data.definition

    try:
        updated = await layout_repo.update(db=db, layout_id=layout_id, **update_kwargs)
        if not updated:
            return None
        await db.commit()
        logger.info("Layout обновлен: id=%s", layout_id)
        return cast(LayoutRead, LayoutRead.model_validate(updated))
    except Exception as e:
        await db.rollback()
        logger.error("Ошибка при обновлении layout id=%s: %s", layout_id, e)
        raise


async def delete_layout(layout_id: UUID, db: AsyncSession | None = None) -> bool:
    """Удаляет layout.

    Args:
        layout_id: Идентификатор layout-а.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        bool: True, если удаление успешно, False - если layout не найден.
    """
    logger.info("Удаление layout: layout_id=%s", layout_id)

    if db is None:
        async with get_session() as db:
            return await _delete_layout_with_session(layout_id, db)
    else:
        return await _delete_layout_with_session(layout_id, db)


async def _delete_layout_with_session(layout_id: UUID, db: AsyncSession) -> bool:
    """Внутренняя функция для удаления layout с использованием сессии."""
    try:
        layout_repo = LayoutRepository()
        result: bool = await layout_repo.delete(layout_id, db)
        if result:
            await db.commit()
            logger.info("Layout успешно удален: id=%s", layout_id)
        else:
            logger.warning("Layout не найден для удаления: id=%s", layout_id)
        return result
    except Exception as e:
        await db.rollback()
        logger.error("Ошибка при удалении layout id=%s: %s", layout_id, e)
        raise
