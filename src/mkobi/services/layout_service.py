"""Layout management service.

Provides business logic for layout CRUD operations.
All operations are performed through LayoutRepository
with validation, checks and logging.

Implements ILayoutService interface for dependency injection.
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
    """Create a new layout.

    Args:
        name: Layout name.
        definition: Layout structure (grid, graphs, filters, bindings).
        db: Optional database session. If not provided, a new session is created.

    Returns:
        LayoutRead: Model of the created layout.

    Raises:
        ValueError: If layout with this name already exists.
        SQLAlchemyError: On database error.
    """
    logger.info("Creating layout: name=%s", name)

    if db is None:
        async with get_session() as db_session:
            return await _create_layout_with_session(name, definition, db_session)
    else:
        return await _create_layout_with_session(name, definition, db)


async def _create_layout_with_session(
    name: str, definition: dict[str, Any], db: AsyncSession
) -> LayoutRead:
    """Internal function to create layout using a session."""
    layout_repo = LayoutRepository()
    existing = await layout_repo.get_by_name(name, db)
    if existing:
        logger.error("Layout with this name already exists: name=%s", name)
        raise ValueError(f"Layout with name '{name}' already exists")

    try:
        layout_obj = await layout_repo.create(db=db, name=name, definition=definition)
        await db.commit()

        if layout_obj is None:
            raise ValueError("Failed to create layout")

        logger.info("Layout created: id=%s, name=%s", layout_obj.id, layout_obj.name)
        return cast(LayoutRead, LayoutRead.model_validate(layout_obj))
    except Exception as e:
        await db.rollback()
        logger.error("Error creating layout name=%s: %s", name, e, exc_info=True)
        raise


async def get_layout(
    layout_id: UUID, db: AsyncSession | None = None
) -> LayoutRead | None:
    """Get layout by ID.

    Args:
        layout_id: Layout identifier.
        db: Optional database session. If not provided, a new session is created.

    Returns:
        LayoutRead: Layout model if found, otherwise None.
    """
    logger.info("Getting layout: layout_id=%s", layout_id)

    if db is None:
        async with get_session() as db_session:
            return await _get_layout_with_session(layout_id, db_session)
    else:
        return await _get_layout_with_session(layout_id, db)


async def _get_layout_with_session(
    layout_id: UUID, db: AsyncSession
) -> LayoutRead | None:
    """Internal function to get layout using a session."""
    layout_repo = LayoutRepository()
    layout_obj = await layout_repo.get(layout_id, db)
    if not layout_obj:
        return None
    return cast(LayoutRead, LayoutRead.model_validate(layout_obj))


async def get_all_layouts(db: AsyncSession | None = None) -> list[LayoutRead]:
    """Get all layouts.

    Args:
        db: Optional database session. If not provided, a new session is created.

    Returns:
        list[LayoutRead]: List of all layouts.
    """
    logger.info("Getting all layouts")

    if db is None:
        async with get_session() as db_session:
            return await _get_all_layouts_with_session(db_session)
    else:
        return await _get_all_layouts_with_session(db)


async def _get_all_layouts_with_session(db: AsyncSession) -> list[LayoutRead]:
    """Internal function to get all layouts using a session."""
    layout_repo = LayoutRepository()
    layout_objs = await layout_repo.get_all(db)
    return [LayoutRead.model_validate(layout_obj) for layout_obj in layout_objs]


async def update_layout(
    layout_id: UUID, update_data: LayoutUpdate, db: AsyncSession | None = None
) -> LayoutRead | None:
    """Update layout.

    Uses Pydantic's model_dump(exclude_unset=True) for partial updates
    to prevent NOT NULL violations when optional fields are not provided.

    Args:
        layout_id: Layout identifier.
        update_data: Data to update (LayoutUpdate model).
        db: Optional database session. If not provided, a new session is created.

    Returns:
        LayoutRead: Updated layout model, or None if not found.
    """
    logger.info("Updating layout: layout_id=%s", layout_id)

    if db is None:
        async with get_session() as db_session:
            return await _update_layout_with_session(layout_id, update_data, db_session)
    else:
        return await _update_layout_with_session(layout_id, update_data, db)


async def _update_layout_with_session(
    layout_id: UUID, update_data: LayoutUpdate, db: AsyncSession
) -> LayoutRead | None:
    """Internal function to update layout using a session."""
    layout_repo = LayoutRepository()
    
    # Check existence
    existing = await layout_repo.get(layout_id, db)
    if not existing:
        logger.warning("Layout not found for update: id=%s", layout_id)
        return None

    # Check name uniqueness on update
    if update_data.name and update_data.name != existing.name:
        name_check = await layout_repo.get_by_name(update_data.name, db)
        if name_check:
            logger.error("Layout with this name already exists: name=%s", update_data.name)
            raise ValueError(f"Layout with name '{update_data.name}' already exists")

    # Use Pydantic v2's exclude_unset=True for partial updates
    # This ensures only fields explicitly set by the client are updated
    update_data_dict = update_data.model_dump(exclude_unset=True)
    
    # Filter out None values to prevent NOT NULL violations
    # (client might explicitly send null for optional fields)
    update_data_dict = {k: v for k, v in update_data_dict.items() if v is not None}
    
    if not update_data_dict:
        logger.info("No fields to update for layout: id=%s", layout_id)
        return cast(LayoutRead, LayoutRead.model_validate(existing))

    logger.info("Updating layout: id=%s, update_data=%s", layout_id, update_data_dict)

    try:
        updated = await layout_repo.update(db=db, layout_id=layout_id, **update_data_dict)
        if not updated:
            return None
        await db.commit()
        logger.info("Layout updated: id=%s", layout_id)
        return cast(LayoutRead, LayoutRead.model_validate(updated))
    except Exception as e:
        await db.rollback()
        logger.error("Error updating layout id=%s: %s", layout_id, e, exc_info=True)
        raise


async def delete_layout(layout_id: UUID, db: AsyncSession | None = None) -> bool:
    """Delete layout.

    Args:
        layout_id: Layout identifier.
        db: Optional database session. If not provided, a new session is created.

    Returns:
        bool: True if deletion successful, False if layout not found.
    """
    logger.info("Deleting layout: layout_id=%s", layout_id)

    if db is None:
        async with get_session() as db_session:
            return await _delete_layout_with_session(layout_id, db_session)
    else:
        return await _delete_layout_with_session(layout_id, db)


async def _delete_layout_with_session(layout_id: UUID, db: AsyncSession) -> bool:
    """Internal function to delete layout using a session."""
    try:
        layout_repo = LayoutRepository()
        result: bool = await layout_repo.delete(layout_id, db)
        if result:
            await db.commit()
            logger.info("Layout deleted: id=%s", layout_id)
        else:
            logger.warning("Layout not found for deletion: id=%s", layout_id)
        return result
    except Exception as e:
        await db.rollback()
        logger.error("Error deleting layout id=%s: %s", layout_id, e, exc_info=True)
        raise
