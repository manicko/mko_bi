"""Base repository with common async CRUD operations.

Provides generic class for typical database operations using async SQLAlchemy.
All repositories can inherit from this class to reduce duplication.
"""

import logging
from typing import Any, cast

from pydantic import BaseModel
from sqlalchemy import select, delete as sa_delete, update as sa_update, insert as sa_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.db.base import Base

logger = logging.getLogger(__name__)


class BaseRepository[T: Base]:
    """Base repository with async CRUD operations.

    Generic class for working with SQLAlchemy async models.
    Provides standard methods for creating, reading, updating, and deleting objects.

    Attributes:
        model: SQLAlchemy model class.
        db: Async SQLAlchemy session.
    """

    def __init__(self, model: type[T], db: AsyncSession) -> None:
        """Initialize repository.

        Args:
            model: SQLAlchemy model class.
            db: Async SQLAlchemy session.
        """
        self.model = model
        self.db = db

    async def get_by_id(self, id: Any) -> T | None:
        """Get object by ID.

        Args:
            id: Object identifier.

        Returns:
            Model instance or None if not found.
        """
        try:
            result = await self.db.execute(
                select(self.model).where(self.model.id == id)
            )
            obj = cast(T | None, result.scalar_one_or_none())
            if obj:
                logger.info("Object retrieved: model=%s, id=%s", self.model.__name__, id)
            else:
                logger.warning("Object not found: model=%s, id=%s", self.model.__name__, id)
            return obj
        except SQLAlchemyError as e:
            logger.error("Error retrieving object id=%s: %s", id, e)
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all objects with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of model instances.
        """
        try:
            result = await self.db.execute(
                select(self.model).offset(skip).limit(limit)
            )
            objs = list(result.scalars().all())
            logger.info(
                "Retrieved objects: model=%s, count=%s",
                self.model.__name__,
                len(objs),
            )
            return objs
        except SQLAlchemyError as e:
            logger.error("Error retrieving objects: %s", e)
            raise

    async def create(self, obj_in: dict[str, Any] | BaseModel) -> T:
        """Create new object.

        Args:
            obj_in: Dictionary or Pydantic model with object data.

        Returns:
            Created model instance with ID.
        """
        try:
            if isinstance(obj_in, BaseModel):
                obj_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_data = obj_in
            stmt = sa_insert(self.model).values(**obj_data).returning(self.model)
            result = await self.db.execute(stmt)
            obj = cast(T, result.scalar_one())
            await self.db.flush()
            await self.db.refresh(obj)
            logger.info(
                "Object created: model=%s, id=%s", self.model.__name__, obj.id
            )
            return obj
        except SQLAlchemyError as e:
            logger.error("Error creating object: %s", e)
            raise

    async def update(self, id: Any, obj_in: dict[str, Any] | BaseModel) -> T | None:
        """Update object by ID.

        Args:
            id: Object identifier.
            obj_in: Dictionary or Pydantic model with fields to update.

        Returns:
            Updated model instance or None if not found.
        """
        try:
            if isinstance(obj_in, BaseModel):
                obj_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_data = obj_in
            stmt = (
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**obj_data)
                .returning(self.model)
            )
            result = await self.db.execute(stmt)
            obj = cast(T | None, result.scalar_one_or_none())
            if not obj:
                logger.warning(
                    "Object not found for update: model=%s, id=%s",
                    self.model.__name__,
                    id,
                )
                return None
            await self.db.flush()
            await self.db.refresh(obj)
            logger.info("Object updated: model=%s, id=%s", self.model.__name__, id)
            return obj
        except SQLAlchemyError as e:
            logger.error("Error updating object id=%s: %s", id, e)
            raise

    async def delete(self, id: Any) -> bool:
        """Delete object by ID.

        Args:
            id: Object identifier.

        Returns:
            True if deletion successful, False if object not found.
        """
        try:
            stmt = (
                sa_delete(self.model)
                .where(self.model.id == id)
                .returning(self.model.id)
            )
            result = await self.db.execute(stmt)
            deleted = result.scalar_one_or_none()
            if not deleted:
                logger.warning(
                    "Object not found for deletion: model=%s, id=%s",
                    self.model.__name__,
                    id,
                )
                return False
            await self.db.flush()
            logger.info("Object deleted: model=%s, id=%s", self.model.__name__, id)
            return True
        except SQLAlchemyError as e:
            logger.error("Error deleting object id=%s: %s", id, e)
            raise

    async def exists(self, **kwargs: Any) -> bool:
        """Check if object exists with given filters.

        Args:
            **kwargs: Fields and values to filter by.

        Returns:
            True if object exists, False otherwise.
        """
        try:
            query = select(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
            result = await self.db.execute(query)
            obj = result.scalar_one_or_none()
            return obj is not None
        except SQLAlchemyError as e:
            logger.error("Error checking object existence: %s", e)
            raise
