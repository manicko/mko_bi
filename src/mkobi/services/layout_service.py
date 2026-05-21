"""Layout management service.

Provides business logic for layout CRUD operations.
All operations are performed through injected LayoutRepository
with validation, checks and logging.

Implements ILayoutService interface for dependency injection.
"""

import logging
from uuid import UUID
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.interfaces.repository_interfaces import ILayoutRepository
from mkobi.interfaces.service_interfaces import ILayoutService
from mkobi.models.layout import LayoutRead, LayoutUpdate


logger = logging.getLogger(__name__)


class LayoutService(ILayoutService):
    """Layout management service implementing ILayoutService."""

    def __init__(self, layout_repo: ILayoutRepository) -> None:
        """Initialize service with injected repository.

        Args:
            layout_repo: Layout repository instance implementing ILayoutRepository.
        """
        self.layout_repo = layout_repo
        logger.debug("LayoutService initialized with injected repository")

    async def create_layout(
        self,
        name: str,
        definition: dict[str, Any],
        db: AsyncSession,
    ) -> LayoutRead:
        """Create a new layout.

        Args:
            name: Layout name.
            definition: Layout structure (grid, graphs, filters, bindings).
            db: Async database session.

        Returns:
            LayoutRead: Model of the created layout.

        Raises:
            ValueError: If layout with this name already exists.
        """
        logger.info("Creating layout: name=%s", name)

        existing = await self.layout_repo.get_by_name(name, db)
        if existing:
            logger.error("Layout with this name already exists: name=%s", name)
            raise ValueError(f"Layout with name '{name}' already exists")

        try:
            layout_obj = await self.layout_repo.create(db=db, name=name, definition=definition)
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
        self, layout_id: UUID, db: AsyncSession
    ) -> LayoutRead | None:
        """Get layout by ID.

        Args:
            layout_id: Layout identifier.
            db: Async database session.

        Returns:
            LayoutRead or None if not found.
        """
        logger.info("Getting layout: layout_id=%s", layout_id)

        layout_obj = await self.layout_repo.get(layout_id, db)
        if not layout_obj:
            logger.warning("Layout not found: id=%s", layout_id)
            return None
        return cast(LayoutRead, LayoutRead.model_validate(layout_obj))

    async def get_all_layouts(
        self, db: AsyncSession
    ) -> list[LayoutRead]:
        """Get all layouts.

        Args:
            db: Async database session.

        Returns:
            List of all layouts.
        """
        logger.info("Getting all layouts")

        layout_objs = await self.layout_repo.get_all(db)
        return [LayoutRead.model_validate(layout_obj) for layout_obj in layout_objs]

    async def update_layout(
        self,
        layout_id: UUID,
        update_data: LayoutUpdate,
        db: AsyncSession,
    ) -> LayoutRead | None:
        """Update layout.

        Uses Pydantic's model_dump(exclude_unset=True) for partial updates
        to prevent NOT NULL violations when optional fields are not provided.

        Args:
            layout_id: Layout identifier.
            update_data: Data to update (LayoutUpdate model).
            db: Async database session.

        Returns:
            LayoutRead: Updated layout model, or None if not found.
        """
        logger.info("Updating layout: layout_id=%s", layout_id)

        # Check existence
        existing = await self.layout_repo.get(layout_id, db)
        if not existing:
            logger.warning("Layout not found for update: id=%s", layout_id)
            return None

        # Check name uniqueness on update
        if update_data.name and update_data.name != existing.name:
            name_check = await self.layout_repo.get_by_name(update_data.name, db)
            if name_check:
                logger.error("Layout with this name already exists: name=%s", update_data.name)
                raise ValueError(f"Layout with name '{update_data.name}' already exists")

        # Use Pydantic v2's exclude_unset=True for partial updates
        update_data_dict = update_data.model_dump(exclude_unset=True)

        # Filter out None values to prevent NOT NULL violations
        update_data_dict = {k: v for k, v in update_data_dict.items() if v is not None}

        if not update_data_dict:
            logger.info("No fields to update for layout: id=%s", layout_id)
            return cast(LayoutRead, LayoutRead.model_validate(existing))

        logger.info("Updating layout: id=%s, update_data=%s", layout_id, update_data_dict)
        
        try:
            updated = await self.layout_repo.update(id=layout_id, db=db, **update_data_dict)
            if not updated:
                return None
            await db.commit()
            logger.info("Layout updated: id=%s", layout_id)
            return cast(LayoutRead, LayoutRead.model_validate(updated))
        except Exception as e:
            await db.rollback()
            logger.error("Error updating layout id=%s: %s", layout_id, e, exc_info=True)
            raise

    async def delete_layout(
        self, layout_id: UUID, db: AsyncSession
    ) -> bool:
        """Delete layout.

        Args:
            layout_id: Layout identifier.
            db: Async database session.

        Returns:
            True if deletion successful, False if not found.
        """
        logger.info("Deleting layout: layout_id=%s", layout_id)

        try:
            result: bool = await self.layout_repo.delete(layout_id, db)
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
