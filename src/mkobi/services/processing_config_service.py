"""Processing configuration service.

Provides business logic for operations with processing settings.

All operations are performed asynchronously through IProcessingConfigRepository.
"""

import logging
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.interfaces.repository_interfaces import IProcessingConfigRepository
from mkobi.interfaces.service_interfaces import IProcessingConfigService
from mkobi.models.processing_configs import ProcessingConfigRead
from mkobi.models.types import ProcessingSettingsDict

logger = logging.getLogger(__name__)


class ProcessingConfigService(IProcessingConfigService):
    """Processing configuration management service."""

    def __init__(self, config_repo: IProcessingConfigRepository) -> None:
        """Initialize service with injected repository.

        Args:
            config_repo: Processing config repository instance.
        """
        self.config_repo = config_repo
        logger.info("ProcessingConfigService initialized with injected repository")

    def _merge_metric_agg_into_settings(
        self,
        settings: ProcessingSettingsDict | None,
        metric_agg: str | None,
    ) -> ProcessingSettingsDict | None:
        """Merge metric_agg into settings dict.

        Args:
            settings: Processing settings dict.
            metric_agg: Optional metric aggregation function.

        Returns:
            Settings dict with metric_agg merged in, or None.
        """
        if settings is None:
            return None
        if metric_agg is not None:
            settings = {**settings, "metric_agg": metric_agg}
        return settings

    def _extract_metric_agg_from_settings(
        self,
        settings: ProcessingSettingsDict,
    ) -> str | None:
        """Extract metric_agg from settings dict.

        Args:
            settings: Processing settings dict.

        Returns:
            metric_agg value or None.
        """
        metric_agg = settings.get("metric_agg")
        if metric_agg is None:
            return None
        return str(metric_agg) if isinstance(metric_agg, str) else None

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

        loader = settings.get("loader")
        if not isinstance(loader, str) or not loader.strip():
            raise ValueError("Field 'loader' must be a non-empty string")
        date_column = settings.get("date_column")
        if not isinstance(date_column, str) or not date_column.strip():
            raise ValueError("Field 'date_column' must be a non-empty string")
        timezone = settings.get("timezone")
        if not isinstance(timezone, str) or not timezone.strip():
            raise ValueError("Field 'timezone' must be a non-empty string")

    async def get_by_dashboard_id(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> ProcessingConfigRead | None:
        """Get processing config by dashboard ID.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.

        Returns:
            ProcessingConfigRead or None if not found.
        """
        logger.info("Getting config: dashboard_id=%s", dashboard_id)

        config_obj = await self.config_repo.get(dashboard_id, db)
        if config_obj is None:
            logger.warning("Config not found: dashboard_id=%s", dashboard_id)
            return None

        logger.info("Config retrieved: dashboard_id=%s", dashboard_id)
        # Extract metric_agg from settings for the response
        metric_agg = self._extract_metric_agg_from_settings(config_obj.settings)
        return cast(
            ProcessingConfigRead,
            ProcessingConfigRead.model_validate(
                {
                    "dashboard_id": config_obj.dashboard_id,
                    "settings": config_obj.settings,
                    "updated_at": config_obj.updated_at,
                    "metric_agg": metric_agg,
                }
            ),
        )

    async def upsert(
        self,
        dashboard_id: UUID,
        db: AsyncSession,
        settings: ProcessingSettingsDict | None = None,
        metric_agg: str | None = None,
    ) -> ProcessingConfigRead:
        """Create or update processing config.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.
            settings: Processing settings.
            metric_agg: Optional metric aggregation function to merge into settings.

        Returns:
            ProcessingConfigRead: Config model.

        Raises:
            ValueError: If settings structure is incorrect.
        """
        logger.info("Upsert config: dashboard_id=%s", dashboard_id)

        # Merge metric_agg into settings
        settings = self._merge_metric_agg_into_settings(settings, metric_agg)

        if settings is not None:
            await self._validate_settings(settings)

        existing = await self.config_repo.get(dashboard_id, db)
        if existing:
            updated = await self.config_repo.update(
                dashboard_id, db, settings=settings
            )
            if updated is None:
                raise ValueError(
                    f"Failed to update config for dashboard {dashboard_id}"
                )
            logger.info("Config updated: dashboard_id=%s", dashboard_id)
            return cast(
                ProcessingConfigRead,
                ProcessingConfigRead.model_validate(
                    {
                        "dashboard_id": updated.dashboard_id,
                        "settings": updated.settings,
                        "updated_at": updated.updated_at,
                        "metric_agg": updated.settings.get("metric_agg"),
                    }
                ),
            )
        else:
            created = await self.config_repo.create(
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
                ProcessingConfigRead,
                ProcessingConfigRead.model_validate(
                    {
                        "dashboard_id": created.dashboard_id,
                        "settings": created.settings,
                        "updated_at": created.updated_at,
                        "metric_agg": created.settings.get("metric_agg"),
                    }
                ),
            )

    async def delete(self, dashboard_id: UUID, db: AsyncSession) -> bool:
        """Delete processing config.

        Args:
            dashboard_id: Dashboard identifier.
            db: Async database session.

        Returns:
            True if deletion successful.
        """
        logger.info("Deleting config: dashboard_id=%s", dashboard_id)

        result: bool = await self.config_repo.delete(dashboard_id, db)
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
        db: AsyncSession,
        metric_agg: str | None = None,
    ) -> ProcessingConfigRead:
        """Create processing config for dashboard."""
        return await self.upsert(dashboard_id, db, settings=settings, metric_agg=metric_agg)

    async def get_processing_config_by_dashboard(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> ProcessingConfigRead | None:
        """Get processing config by dashboard ID."""
        return await self.get_by_dashboard_id(dashboard_id, db)

    async def update_processing_config(
        self,
        dashboard_id: UUID,
        settings: ProcessingSettingsDict,
        db: AsyncSession,
        metric_agg: str | None = None,
    ) -> ProcessingConfigRead | None:
        """Update processing config."""
        return await self.upsert(dashboard_id, db, settings=settings, metric_agg=metric_agg)

    async def delete_processing_config(
        self, dashboard_id: UUID, db: AsyncSession
    ) -> bool:
        """Delete processing config."""
        return await self.delete(dashboard_id, db)