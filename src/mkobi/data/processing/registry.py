"""Data processing pipeline orchestration.

Contains DataPipeline class that manages sequential
data transformation, aggregation, saving and status updates.
"""

import logging
import tenacity
from typing import Any, cast
from uuid import UUID

import polars as pl
from sqlalchemy import ConnectionError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.data.processing.transformations import (
    aggregate_data,
    apply_transformations,
)
from mkobi.data.storage.manager import StorageManager
from mkobi.interfaces.repository_interfaces import IGraphRepository
from mkobi.interfaces.service_interfaces import (
    IProcessingConfigService,
    IProcessingLogService,
)
from mkobi.models.enums import ProcessingStatus, UploadMode
from mkobi.models.processing_logs import ProcessingLogRead

logger = logging.getLogger(__name__)


class DataPipeline:
    """Data processing orchestration.

    Manages sequential steps: transformation,
    aggregation, saving and status updates.

    Attributes:
        storage_manager: Manager for saving aggregated data.
        graph_repo: Injected graph repository.
        config_service: Injected processing config service.
        log_service: Injected processing log service.
    """

    def __init__(
        self,
        storage_manager: StorageManager,
        graph_repo: IGraphRepository,
        config_service: IProcessingConfigService,
        log_service: IProcessingLogService,
    ) -> None:
        """Initialize pipeline with dependency injection.

        Args:
            storage_manager: Storage manager instance.
            graph_repo: Graph repository instance.
            config_service: Processing config service instance.
            log_service: Processing log service instance.
        """
        self.storage_manager = storage_manager
        self.graph_repo = graph_repo
        self.config_service = config_service
        self.log_service = log_service
        logger.debug("DataPipeline initialized with injected dependencies")

    async def run(
        self,
        df: pl.DataFrame,
        dashboard_id: UUID,
        mode: UploadMode,
        db: AsyncSession,
    ) -> ProcessingLogRead:
        """Run data processing pipeline.

        Args:
            df: Input DataFrame with raw data.
            dashboard_id: Dashboard identifier.
            mode: Upload mode (overwrite/append).
            db: Async database session.

        Returns:
            ProcessingLogRead: Execution result with status.
        """
        log_entry = None
        try:
            logger.info(
                "Starting pipeline for dashboard_id=%s, mode=%s",
                dashboard_id,
                mode,
            )

            # Step 1: Create log entry
            log_entry = await self.log_service.create_processing_log(
                dashboard_id=dashboard_id,
                status=ProcessingStatus.STARTED.value,
                message="Upload started",
                db=db,
            )

            # Check for empty input DataFrame
            if df.height == 0:
                logger.warning("Empty DataFrame provided, skipping processing")
                await self.log_service.update_processing_log(
                    log_id=log_entry.id,
                    status=ProcessingStatus.COMPLETED.value,
                    message="No data to process",
                    finished_at=None,
                    db=db,
                )
                log_entry.status = ProcessingStatus.COMPLETED
                return log_entry

            # Step 2: Get config and transform data
            logger.info("Step 1: Transforming data")
            config_response = await self.config_service.get_processing_config_by_dashboard(
                dashboard_id, db
            )
            config = config_response.settings if config_response else None

            try:
                transformed_df = apply_transformations(df, cast(dict[str, Any] | None, config))
            except pl.PolarsError as e:
                logger.error("Polars transformation error: %s", e)
                await self.log_service.update_processing_log(
                    log_id=log_entry.id,
                    status=ProcessingStatus.FAILED.value,
                    message=f"Transformation error: {e}",
                    finished_at=None,
                    db=db,
                )
                raise ValueError(f"Data transformation failed: {e}") from None
            except Exception as e:
                logger.error("Unexpected transformation error: %s", e)
                await self.log_service.update_processing_log(
                    log_id=log_entry.id,
                    status=ProcessingStatus.FAILED.value,
                    message=f"Unexpected transformation error: {e}",
                    finished_at=None,
                    db=db,
                )
                raise

            logger.info("Transformation complete: %d rows", transformed_df.shape[0])

            # Step 3: Get graphs and aggregate data
            logger.info("Step 2: Aggregating data")
            graphs = await self.graph_repo.get_by_dashboard_id(dashboard_id, db)
            graph_configs = [
                {
                    "dimensions": g.dimensions,
                    "metrics": g.metrics,
                }
                for g in graphs
            ]

            aggregates = aggregate_data(transformed_df, graph_configs)

            # Step 4: Save results
            logger.info("Step 3: Saving data")
            clear_old = (mode == UploadMode.OVERWRITE)
            await self._save_with_retry(
                dashboard_id=dashboard_id,
                aggregates=aggregates,
                clear_old=clear_old,
            )

            # Update status to SUCCESS
            await self.log_service.update_processing_log(
                log_id=log_entry.id,
                status=ProcessingStatus.SUCCESS.value,
                message="Processing completed successfully",
                finished_at=None,
                db=db,
            )

            log_entry.status = ProcessingStatus.SUCCESS
            logger.info("Pipeline completed successfully: dashboard_id=%s", dashboard_id)
            return log_entry

        except (pl.PolarsError, SQLAlchemyError, ValueError, ConnectionError) as e:
            logger.error("Pipeline failed with expected error: %s", e)
            if log_entry:
                await self.log_service.update_processing_log(
                    log_id=log_entry.id,
                    status=ProcessingStatus.FAILED.value,
                    message=str(e),
                    finished_at=None,
                    db=db,
                )
            raise
        except Exception as e:
            logger.error("Pipeline failed with unexpected error: %s", e)
            if log_entry:
                await self.log_service.update_processing_log(
                    log_id=log_entry.id,
                    status=ProcessingStatus.FAILED.value,
                    message=f"Unexpected error: {e}",
                    finished_at=None,
                    db=db,
                )
            raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((SQLAlchemyError, ConnectionError)),
        reraise=True,
    )
    async def _save_with_retry(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        clear_old: bool,
    ) -> int:
        """Save aggregates with retry on transient DB errors."""
        return await self.storage_manager.save_aggregates(
            dashboard_id=dashboard_id,
            aggregates=aggregates,
            clear_old=clear_old,
        )
