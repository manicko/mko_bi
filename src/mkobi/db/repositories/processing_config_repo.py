"""Repository for processing configuration operations.

Provides CRUD methods for ProcessingConfig model.
All methods use contextual session management and handle errors.
"""

import logging
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.models import processing_configs as processing_config_model
from mkobi.interfaces.repository_interfaces import IProcessingConfigRepository

logger = logging.getLogger(__name__)


class ProcessingConfigRepository(IProcessingConfigRepository):
    """Repository for processing configuration operations.

    Provides methods for creating, reading, updating and deleting
    processing configurations in the database. All operations are performed within a
    separate database session with automatic transaction management.
    Implements IProcessingConfigRepository interface.
    """

    @classmethod
    async def get(
        cls, id: UUID, db: AsyncSession
    ) -> processing_config_model.ProcessingConfig | None:
        """Get processing config by dashboard ID.

        Args:
            id: Dashboard identifier (UUID).
            db: Async database session.

        Returns:
            Processing config model or None if not found.
        """
        try:
            result = await db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id
                    == id
                )
            )
            config = result.scalar_one_or_none()
            if config:
                logger.info(
                    "Processing config retrieved: dashboard_id=%s", id
                )
            else:
                logger.warning(
                    "Processing config not found: dashboard_id=%s", id
                )
            return cast(processing_config_model.ProcessingConfig | None, config)
        except SQLAlchemyError as e:
            logger.error(
                "Error getting config dashboard_id=%s: %s", id, e
            )
            raise

    @classmethod
    async def create(
        cls, db: AsyncSession, **kwargs
    ) -> processing_config_model.ProcessingConfig | None:
        """Create new processing config.

        Args:
            db: Async database session.
            **kwargs: Config parameters (dashboard_id, settings).

        Returns:
            Created config model with ID or None on error.
        """
        try:
            config_obj = processing_config_model.ProcessingConfig(**kwargs)
            db.add(config_obj)
            await db.flush()
            await db.refresh(config_obj)
            logger.info(
                "Processing config created: dashboard_id=%s", config_obj.dashboard_id
            )
            return cast(processing_config_model.ProcessingConfig | None, config_obj)
        except SQLAlchemyError as e:
            logger.error("Error creating processing config: %s", e)
            raise

    @classmethod
    async def update(
        cls, id: UUID, db: AsyncSession, **kwargs
    ) -> processing_config_model.ProcessingConfig | None:
        """Update processing config.

        Args:
            id: Dashboard identifier (UUID).
            db: Async database session.
            **kwargs: Fields to update.

        Returns:
            Updated config model or None if not found.
        """
        try:
            result = await db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id
                    == id
                )
            )
            config_obj = result.scalar_one_or_none()
            if not config_obj:
                logger.warning(
                    "Config not found for update: dashboard_id=%s", id
                )
                return None
            for key, value in kwargs.items():
                if hasattr(config_obj, key):
                    setattr(config_obj, key, value)
            await db.flush()
            await db.refresh(config_obj)
            logger.info("Processing config updated: dashboard_id=%s", id)
            return cast(processing_config_model.ProcessingConfig | None, config_obj)
        except SQLAlchemyError as e:
            logger.error(
                "Error updating config dashboard_id=%s: %s", id, e
            )
            raise

    @classmethod
    async def delete(cls, id: UUID, db: AsyncSession) -> bool:
        """Delete processing config.

        Args:
            id: Dashboard identifier (UUID).
            db: Async database session.

        Returns:
            True if deletion successful, False if config not found.
        """
        try:
            result = await db.execute(
                select(processing_config_model.ProcessingConfig).where(
                    processing_config_model.ProcessingConfig.dashboard_id
                    == id
                )
            )
            config_obj = result.scalar_one_or_none()
            if not config_obj:
                logger.warning(
                    "Config not found for deletion: dashboard_id=%s", id
                )
                return False
            await db.delete(config_obj)
            await db.flush()
            logger.info("Processing config deleted: dashboard_id=%s", id)
            return True
        except SQLAlchemyError as e:
            logger.error(
                "Error deleting config dashboard_id=%s: %s", id, e
            )
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[processing_config_model.ProcessingConfig]:
        """Get all processing configs.

        Args:
            db: Async database session.

        Returns:
            List of all processing configs.
        """
        try:
            result = await db.execute(select(processing_config_model.ProcessingConfig))
            configs = list(result.scalars().all())
            logger.info("Processing configs list retrieved, count: %s", len(configs))
            return configs
        except SQLAlchemyError as e:
            logger.error("Error getting processing configs list: %s", e)
            raise
