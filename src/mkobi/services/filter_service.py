"""Filter management service.

Provides business logic for CRUD operations with filters.

All operations are performed through injected FilterRepository with validation,
permission checking, and logging.

Implements IFilterService interface for dependency injection.
"""

import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.interfaces.repository_interfaces import IFilterRepository
from mkobi.interfaces.service_interfaces import IFilterService
from mkobi.models.enums import FilterType
from mkobi.models.filters import FilterRead
from mkobi.models.types import FilterConfigDict

logger = logging.getLogger(__name__)


class FilterService(IFilterService):
    """Service class for managing filters.

    Implements IFilterService interface for working with filters.
    Uses injected FilterRepository for data access.
    """

    def __init__(self, filter_repo: IFilterRepository | None = None) -> None:
        """Initialize service with injected repository.

        Args:
            filter_repo: Filter repository instance implementing IFilterRepository.
                        If None, creates a new FilterRepository().
        """
        self.filter_repo = filter_repo if filter_repo is not None else FilterRepository()
        logger.debug("FilterService initialized with injected repository")

    async def create_filter(
        self,
        name: str,
        type_: str,
        config: FilterConfigDict,
        db: AsyncSession | None = None,
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
        if db is None:
            raise ValueError("db session is required for create_filter")

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

            return FilterRead.model_validate(filter_obj)

        except ValueError:
            raise
        except Exception as e:
            logger.error("Error creating filter name=%s: %s", name, e)
            raise

    async def get_filter_by_id(
        self,
        filter_id: UUID,
        db: AsyncSession | None = None,
    ) -> FilterRead | None:
        """Get filter by ID.

        Args:
            filter_id: Filter identifier.
            db: Async database session.

        Returns:
            FilterRead or None if not found.
        """
        if db is None:
            raise ValueError("db session is required for get_filter_by_id")

        try:
            filter_obj = await self.filter_repo.get(filter_id, db)
            if filter_obj is None:
                logger.warning("Filter not found: id=%s", filter_id)
                return None
            return FilterRead.model_validate(filter_obj)
        except Exception as e:
            logger.error("Error getting filter id=%s: %s", filter_id, e)
            raise

    async def get_filter_by_name(
        self,
        name: str,
        db: AsyncSession | None = None,
    ) -> FilterRead | None:
        """Get filter by name.

        Args:
            name: Filter name.
            db: Async database session.

        Returns:
            FilterRead or None if not found.
        """
        if db is None:
            raise ValueError("db session is required for get_filter_by_name")

        try:
            filter_obj = await self.filter_repo.get_by_name(name, db)
            if filter_obj is None:
                logger.warning("Filter not found by name: name=%s", name)
                return None
            return FilterRead.model_validate(filter_obj)
        except Exception as e:
            logger.error("Error getting filter by name %s: %s", name, e)
            raise

    async def get_all_filters(
        self,
        db: AsyncSession | None = None,
    ) -> list[FilterRead]:
        """Get all filters.

        Args:
            db: Async database session.

        Returns:
            list[FilterRead]: List of all filters.
        """
        if db is None:
            raise ValueError("db session is required for get_all_filters")

        try:
            filters = await self.filter_repo.get_all(db)
            return [FilterRead.model_validate(f) for f in filters]
        except Exception as e:
            logger.error("Error getting all filters: %s", e)
            raise

    async def update_filter(
        self,
        filter_id: UUID,
        name: str | None = None,
        type_: str | None = None,
        config: FilterConfigDict | None = None,
        db: AsyncSession | None = None,
    ) -> FilterRead | None:
        """Update filter.

        Args:
            filter_id: Filter identifier.
            name: New name (optional).
            type_: New type (optional).
            config: New config (optional).
            db: Async database session.

        Returns:
            FilterRead or None if not found.
        """
        if db is None:
            raise ValueError("db session is required for update_filter")

        # Check if filter exists
        existing = await self.filter_repo.get(filter_id, db)
        if existing is None:
            logger.warning("Filter not found for update: id=%s", filter_id)
            return None

        # Validate inputs
        if name is not None:
            self._validate_filter_name(name)
            # Check name uniqueness (excluding current filter)
            name_check = await self.filter_repo.get_by_name(name, db)
            if name_check and name_check.id != filter_id:
                raise ValueError(f"Filter with name '{name}' already exists")

        if type_ is not None:
            self._validate_filter_type(type_)

        if config is not None:
            self._validate_filter_config(config)

        # Build update data
        update_data: dict[str, Any] = {}
        if name is not None:
            update_data["name"] = name
        if type_ is not None:
            update_data["type"] = type_
        if config is not None:
            update_data["config"] = config

        if not update_data:
            logger.warning("No data for filter update: id=%s", filter_id)
            return FilterRead.model_validate(existing)

        try:
            updated = await self.filter_repo.update(filter_id, db, **update_data)
            if updated is None:
                return None

            await db.commit()

            logger.info("Filter updated: id=%s", filter_id)
            return FilterRead.model_validate(updated)

        except Exception as e:
            await db.rollback()
            logger.error("Error updating filter id=%s: %s", filter_id, e)
            raise

    async def delete_filter(
        self,
        filter_id: UUID,
        db: AsyncSession | None = None,
    ) -> bool:
        """Delete filter.

        Args:
            filter_id: Filter identifier.
            db: Async database session.

        Returns:
            bool: True if deletion successful.
        """
        if db is None:
            raise ValueError("db session is required for delete_filter")

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

    def _validate_filter_config(self, config: dict[str, Any]) -> None:
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


# --- Backward compatibility functions ---


async def create_filter(
    name: str,
    type_: str,
    config: dict[str, Any],
    db: AsyncSession | None = None,
) -> FilterRead:
    """Backward compatibility wrapper."""
    service = FilterService()
    return await service.create_filter(name, type_, config, db)


async def get_filter_by_id(
    filter_id: UUID,
    db: AsyncSession | None = None,
) -> FilterRead | None:
    """Backward compatibility wrapper."""
    service = FilterService()
    return await service.get_filter_by_id(filter_id, db)


async def get_filter_by_name(
    name: str,
    db: AsyncSession | None = None,
) -> FilterRead | None:
    """Backward compatibility wrapper."""
    service = FilterService()
    return await service.get_filter_by_name(name, db)


async def get_all_filters(
    db: AsyncSession | None = None,
) -> list[FilterRead]:
    """Backward compatibility wrapper."""
    service = FilterService()
    return await service.get_all_filters(db)


async def update_filter(
    filter_id: UUID,
    name: str | None = None,
    type_: str | None = None,
    config: dict[str, Any] | None = None,
    db: AsyncSession | None = None,
) -> FilterRead | None:
    """Backward compatibility wrapper."""
    service = FilterService()
    return await service.update_filter(filter_id, name, type_, config, db)


async def delete_filter(
    filter_id: UUID,
    db: AsyncSession | None = None,
) -> bool:
    """Backward compatibility wrapper."""
    service = FilterService()
    return await service.delete_filter(filter_id, db)
