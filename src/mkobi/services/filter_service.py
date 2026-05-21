"""Filter management service.

Provides business logic for CRUD operations with filters.

All operations are performed through injected FilterRepository with validation,
permission checking, and logging.

Implements IFilterService interface for dependency injection.
"""

import logging
import re
from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.interfaces.repository_interfaces import IFilterRepository
from mkobi.interfaces.service_interfaces import IFilterService
from mkobi.models.enums import FilterType
from mkobi.models.filters import FilterRead, FilterUpdate
from mkobi.models.types import FilterConfigDict

logger = logging.getLogger(__name__)


class FilterService(IFilterService):
    """Service class for managing filters.

    Implements IFilterService interface for working with filters.
    Uses injected FilterRepository for data access.
    """

    def __init__(self, filter_repo: IFilterRepository) -> None:
        """Initialize service with injected repository.

        Args:
            filter_repo: Filter repository instance implementing IFilterRepository.
        """
        self.filter_repo = filter_repo
        logger.debug("FilterService initialized with injected repository")

    async def create_filter(
        self,
        name: str,
        type_: str,
        config: FilterConfigDict,
        db: AsyncSession,
    ) -> FilterRead:
        """Create new global filter.

        Args:
            name: Filter name.
            type_: Filter type.
            config: Filter configuration.
            db: Async database session.

        Returns:
            FilterRead: Created filter model.

        Raises:
            ValueError: If validation fails.
        """
        self._validate_filter_type(type_)
        self._validate_filter_name(name)
        self._validate_filter_config(config)

        # Check name uniqueness
        existing = await self.filter_repo.get_by_name(name, db)
        if existing:
            logger.warning("Filter with name already exists: name=%s", name)
            raise ValueError(f"Filter with name '{name}' already exists")

        try:
            filter_obj = await self.filter_repo.create(
                db=db,
                name=name,
                type=type_,
                config=config,
            )

            if filter_obj is None:
                raise ValueError("Failed to create filter")

            logger.info(
                "Filter created: id=%s, name=%s, type=%s",
                filter_obj.id,
                filter_obj.name,
                filter_obj.type,
            )

            return cast(FilterRead, FilterRead.model_validate(filter_obj))

        except ValueError:
            raise
        except Exception as e:
            logger.error("Error creating filter name=%s: %s", name, e)
            raise

    async def get_filter_by_id(
        self,
        filter_id: UUID,
        db: AsyncSession,
    ) -> FilterRead | None:
        """Get filter by ID.

        Args:
            filter_id: Filter identifier.
            db: Async database session.

        Returns:
            FilterRead or None if not found.
        """
        try:
            filter_obj = await self.filter_repo.get(filter_id, db)
            if filter_obj is None:
                logger.warning("Filter not found: id=%s", filter_id)
                return None
            return cast(FilterRead, FilterRead.model_validate(filter_obj))
        except Exception as e:
            logger.error("Error getting filter id=%s: %s", filter_id, e)
            raise

    async def get_filter_by_name(
        self,
        name: str,
        db: AsyncSession,
    ) -> FilterRead | None:
        """Get filter by name.

        Args:
            name: Filter name.
            db: Async database session.

        Returns:
            FilterRead or None if not found.
        """
        try:
            filter_obj = await self.filter_repo.get_by_name(name, db)
            if filter_obj is None:
                logger.warning("Filter not found by name: name=%s", name)
                return None
            return cast(FilterRead, FilterRead.model_validate(filter_obj))
        except Exception as e:
            logger.error("Error getting filter by name %s: %s", name, e)
            raise

    async def get_all_filters(
        self,
        db: AsyncSession,
    ) -> list[FilterRead]:
        """Get all filters.

        Args:
            db: Async database session.

        Returns:
            list[FilterRead]: List of all filters.
        """
        try:
            filters = await self.filter_repo.get_all(db)
            return [FilterRead.model_validate(f) for f in filters]
        except Exception as e:
            logger.error("Error getting all filters: %s", e)
            raise

    async def update_filter(
        self,
        filter_id: UUID,
        updates: FilterUpdate,
        db: AsyncSession,
    ) -> FilterRead | None:
        """Update filter.

        Args:
            filter_id: Filter identifier.
            updates: FilterUpdate model with fields to update.
            db: Async database session.

        Returns:
            FilterRead or None if not found.
        """
        # Check if filter exists
        existing = await self.filter_repo.get(filter_id, db=db)
        if existing is None:
            logger.warning("Filter not found for update: id=%s", filter_id)
            return None

        # Validate inputs if provided
        if updates.name is not None:
            self._validate_filter_name(updates.name)
            # Check name uniqueness (excluding current filter)
            name_check = await self.filter_repo.get_by_name(updates.name, db=db)
            if name_check and name_check.id != filter_id:
                raise ValueError(f"Filter with name '{updates.name}' already exists")

        if updates.type is not None:
            self._validate_filter_type(updates.type.value)

        if updates.config is not None:
            self._validate_filter_config(updates.config)

        # Build update dict from FilterUpdate model
        update_data: dict[str, Any] = {}
        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.type is not None:
            update_data["type"] = updates.type.value
        if updates.config is not None:
            update_data["config"] = updates.config

        if not update_data:
            logger.info("No fields to update for filter: id=%s", filter_id)
            return cast(FilterRead, FilterRead.model_validate(existing))

        logger.info("Updating filter: id=%s, update_data=%s", filter_id, update_data)

        try:
            updated = await self.filter_repo.update(filter_id, db=db, **update_data)
            if not updated:
                return None
            await db.commit()
            logger.info("Filter updated: id=%s", filter_id)
            return cast(FilterRead, FilterRead.model_validate(updated))
        except Exception as e:
            await db.rollback()
            logger.error("Error updating filter id=%s: %s", filter_id, e, exc_info=True)
            raise

    async def delete_filter(
        self,
        filter_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """Delete filter.

        Args:
            filter_id: Filter identifier.
            db: Async database session.

        Returns:
            bool: True if deletion successful.
        """
        try:
            result = await self.filter_repo.delete(filter_id, db)
            await db.commit()

            if result:
                logger.info("Filter deleted: id=%s", filter_id)
            else:
                logger.warning("Filter not found for deletion: id=%s", filter_id)

            return bool(result)

        except Exception as e:
            await db.rollback()
            logger.error("Error deleting filter id=%s: %s", filter_id, e)
            raise

    def _validate_filter_type(self, filter_type: str) -> None:
        """Validate filter type.

        Args:
            filter_type: Filter type string to validate.

        Raises:
            ValueError: If filter type is invalid.
        """
        try:
            FilterType(filter_type)
        except ValueError:
            logger.error(
                "Invalid filter type: '%s'. Allowed: %s",
                filter_type,
                sorted([e.value for e in FilterType]),
            )
            raise ValueError(
                f"Invalid filter type: '{filter_type}'. "
                f"Allowed values: {', '.join(sorted([e.value for e in FilterType]))}"
            ) from None

    def _validate_filter_name(self, name: str) -> None:
        """Validate filter name.

        Args:
            name: Filter name to validate.

        Raises:
            ValueError: If name is invalid.
        """
        if not name or not name.strip():
            logger.error("Filter name cannot be empty")
            raise ValueError("Filter name cannot be empty")

        if len(name) > 255:
            logger.error("Filter name too long: %s (length: %s)", name, len(name))
            raise ValueError("Filter name must not exceed 255 characters")

        if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_.]+$', name):
            logger.error("Invalid characters in filter name: %s", name)
            raise ValueError(
                "Filter name can only contain letters, digits, "
                "spaces, hyphens, underscores and dots"
            )

    def _validate_filter_config(self, config: FilterConfigDict) -> None:
        """Validate filter config.

        Args:
            config: Filter configuration dictionary to validate.

        Raises:
            ValueError: If config is invalid.
        """
        if not isinstance(config, dict):
            logger.error("Filter config must be a dictionary")
            raise ValueError("Filter config must be a dictionary")

        if not config:
            logger.error("Filter config cannot be empty")
            raise ValueError("Filter config cannot be empty")

        if 'field' not in config:
            logger.error("Filter config missing required field 'field'")
            raise ValueError(
                "Filter config must contain 'field' "
                "specifying the field to filter"
            )



