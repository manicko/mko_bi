"""Data processing pipeline orchestration.

Contains DataPipeline class that manages sequential
data transformation, aggregation, saving and status updates.
"""

import logging
from uuid import UUID

import polars as pl
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

            # Step 2: Get config and transform data
            logger.info("Step 1: Transforming data")
            config_response = await self.config_service.get_processing_config_by_dashboard(
                dashboard_id, db
            )
            config = config_response.settings if config_response else {}
            transformed_df = apply_transformations(df, config)
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
            await self.storage_manager.save(
                dashboard_id=dashboard_id,
                aggregates=aggregates,
                mode=mode,
                db=db,
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

        except Exception as e:
            logger.error("Pipeline error: %s", e)
            if log_entry:
                await self.log_service.update_processing_log(
                    log_id=log_entry.id,
                    status=ProcessingStatus.FAILED.value,
                    message=str(e),
                    finished_at=None,
                    db=db,
                )
            raise
