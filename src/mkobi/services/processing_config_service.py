"""Processing configuration service.

Provides business logic for operations with processing settings.

All operations are performed asynchronously through ProcessingConfigRepository.
"""

import logging
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.repositories.processing_config_repo import ProcessingConfigRepository
from mkobi.db.session import get_session
from mkobi.interfaces.service_interfaces import IProcessingConfigService
from mkobi.models.processing_configs import ProcessingConfigRead
from mkobi.models.types import ProcessingSettingsDict

logger = logging.getLogger(__name__)


class ProcessingConfigService(IProcessingConfigService):
    """Processing configuration management service."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        """Initialize service.

        Args:
            db: Optional async database session.
        """
        self._db = db

    async def _validate_settings(self, settings: ProcessingSettingsDict) -> None:
        """Validate processing settings structure.

        Args:
            settings: Processing settings.

        Raises:
            ValueError: If settings structure is incorrect.
        """
        if not isinstance(settings, dict):
            raise ValueError("Settings must be a dictionary")

        if not settings:
            raise ValueError("Settings cannot be empty")

        required_fields = ["loader", "date_column", "timezone"]
        missing_fields = [field for field in required_fields if field not in settings]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        for field in required_fields:
            if not isinstance(settings.get(field), str) or not settings[field].strip():
                raise ValueError(f"Field '{field}' must be a non-empty string")

    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> ProcessingConfigRead | None:
        """Get processing config by dashboard ID.

        Args:
            dashboard_id: Dashboard identifier.
            db: Optional database session.

        Returns:
            ProcessingConfigRead or None if not found.
        """
        logger.info("Getting config: dashboard_id=%s", dashboard_id)

        if db is None:
            db = self._db

        if db is None:
            async with get_session() as db:
                return await self.get_by_dashboard_id(dashboard_id, db)

        config_repo = ProcessingConfigRepository()
        config_obj = await config_repo.get(dashboard_id, db)
        if config_obj is None:
            logger.warning("Config not found: dashboard_id=%s", dashboard_id)
            return None

        logger.info("Config retrieved: dashboard_id=%s", dashboard_id)
        return cast(
            ProcessingConfigRead, ProcessingConfigRead.model_validate(config_obj)
        )

    async def upsert(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
        db: AsyncSession | None = None,
    ) -> ProcessingConfigRead:
        """Create or update processing config.

        Args:
            dashboard_id: Dashboard identifier.
            settings: Processing settings.
            db: Optional database session.

        Returns:
            ProcessingConfigRead: Config model.

        Raises:
            ValueError: If settings structure is incorrect.
        """
        logger.info("Upsert config: dashboard_id=%s", dashboard_id)
        self._validate_settings(settings)

        if db is None:
            db = self._db

        if db is None:
            async with get_session() as db:
                return await self.upsert(dashboard_id, settings, db)

        config_repo = ProcessingConfigRepository()
        existing = await config_repo.get(dashboard_id, db)
        if existing:
            updated = await config_repo.update(
                dashboard_id=dashboard_id,
                db=db,
                settings=settings,
            )
            if updated is None:
                raise ValueError(
                    f"Failed to update config for dashboard {dashboard_id}"
                )
            logger.info("Config updated: dashboard_id=%s", dashboard_id)
            return cast(
                ProcessingConfigRead, ProcessingConfigRead.model_validate(updated)
            )
        else:
            created = await config_repo.create(
                db=db,
                dashboard_id=dashboard_id,
                settings=settings,
            )
            if created is None:
                raise ValueError(
                    f"Failed to create config for dashboard {dashboard_id}"
                )
            logger.info("Config created: dashboard_id=%s", dashboard_id)
            return cast(
                ProcessingConfigRead, ProcessingConfigRead.model_validate(created)
            )

    async def delete(self, dashboard_id: UUID, db: AsyncSession | None = None) -> bool:
        """Delete processing config.

        Args:
            dashboard_id: Dashboard identifier.
            db: Optional database session.

        Returns:
            True if deletion successful.
        """
        logger.info("Deleting config: dashboard_id=%s", dashboard_id)

        if db is None:
            db = self._db

        if db is None:
            async with get_session() as db:
                return await self.delete(dashboard_id, db)

        result: bool = await config_repo.delete(dashboard_id, db)
        if result:
            logger.info("Config deleted: dashboard_id=%s", dashboard_id)
        else:
            logger.warning(
                "Config not found for deletion: dashboard_id=%s", dashboard_id
            )
        return result

    # ========= IProcessingConfigService interface methods =========

    async def create_processing_config(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
        db: AsyncSession | None = None,
    ) -> ProcessingConfigRead:
        """Create processing config for dashboard."""
        return await self.upsert(dashboard_id, settings, db)

    async def get_processing_config_by_dashboard(
        self, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> ProcessingConfigRead | None:
        """Get processing config by dashboard ID."""
        return await self.get_by_dashboard_id(dashboard_id, db)

    async def update_processing_config(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
        db: AsyncSession | None = None,
    ) -> ProcessingConfigRead | None:
        """Update processing config."""
        return await self.upsert(dashboard_id, settings, db)

    async def delete_processing_config(
        self, dashboard_id: UUID, db: AsyncSession | None = None
    ) -> bool:
        """Delete processing config."""
        return await self.delete(dashboard_id, db)
