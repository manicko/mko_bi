"""RQ worker tasks for background data processing.

Contains functions that are executed by RQ workers in separate processes.
These functions handle CSV processing, status updates, and database operations.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import polars as pl
from sqlalchemy import delete, select, update

from mkobi.data.loaders.loader import CSVLoader
from mkobi.data.processing.transformations import (
    apply_transformations,
    calculate_aggregations,
)
from mkobi.db.models.aggregated_data import AggregatedData
from mkobi.db.models.graphs import Graph
from mkobi.db.models.processing_logs import ProcessingLog
from mkobi.db.session import get_session
from mkobi.models.data import ProcessingConfig
from mkobi.models.enums import ProcessingStatus

logger = logging.getLogger(__name__)


async def _update_processing_log_status(
    task_id: str,
    status: ProcessingStatus,
    message: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> None:
    """Update processing log status.

    Args:
        task_id: Task ID (UUID string).
        status: New status.
        message: Status message.
        started_at: Processing start time.
        finished_at: Processing finish time.
    """
    async with get_session() as session:
        async with session.begin():
            stmt = (
                update(ProcessingLog)
                .where(ProcessingLog.id == UUID(task_id))
                .values(
                    status=status,
                    message=message,
                    started_at=started_at or datetime.now(),
                    finished_at=finished_at,
                )
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(
                "Processing log updated: task_id=%s, status=%s", task_id, status
            )


async def _process_csv_file_task_sync(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Process CSV file in background (async wrapper for sync processing).

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.

    Returns:
        dict: Processing result.
    """
    return await asyncio.to_thread(
        _process_csv_file_sync_impl,
        file_path_str,
        task_id,
        dashboard_id_str,
        processing_config_dict,
    )


def _process_csv_file_sync_impl(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Synchronous CSV processing implementation.

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.

    Returns:
        dict: Processing result with status and data.
    """
    file_path = Path(file_path_str)
    dashboard_id = UUID(dashboard_id_str)

    try:
        # Update status to processing
        async def _update_start():
            await _update_processing_log_status(
                task_id=task_id,
                status=ProcessingStatus.PROCESSING,
                message="Processing started (background task)",
                started_at=datetime.now(),
            )

        asyncio.run(_update_start())

        # Load and process CSV
        loader = CSVLoader()
        df = loader.load_csv(file_path)
        logger.info("File loaded: %d rows, %d columns", df.shape[0], df.shape[1])

        # Apply processing config if provided
        if processing_config_dict:
            config = ProcessingConfig(**processing_config_dict)

            # Apply transformations
            df = apply_transformations(
                df,
                filters=config.filters,
                groupby=config.groupby if not config.aggregations else None,
                sort_by=config.sort_by,
                descending=config.descending,
                limit=config.limit,
            )

            # Apply aggregations
            if (
                config.aggregations
                or config.yoy_config
                or config.share_config
                or config.custom_metrics
            ):
                df = calculate_aggregations(
                    df,
                    groupby=config.groupby,
                    aggregations=config.aggregations,
                    yoy_config=config.yoy_config,
                    share_config=config.share_config,
                    custom_metrics=config.custom_metrics,
                )

        # Save aggregated data to database
        result_data = {
            "rows": df.shape[0],
            "columns": df.columns,
            "preview": df.head(10).to_dicts(),
        }

        # Store aggregates in database
        async def _save_aggregates():
            await _store_aggregates(df, dashboard_id, task_id)

        asyncio.run(_save_aggregates())

        # Update status to success
        async def _update_success():
            await _update_processing_log_status(
                task_id=task_id,
                status=ProcessingStatus.SUCCESS,
                message=f"Processing completed successfully: {result_data['rows']} rows processed",
                finished_at=datetime.now(),
            )

        asyncio.run(_update_success())

        # Clean up temp file
        if file_path.exists():
            file_path.unlink()
            logger.info("Temp file deleted: %s", file_path)

        return {
            "success": True,
            "rows_processed": result_data["rows"],
            "message": "Processing completed",
        }

    except Exception as e:
        error_msg = str(e)
        logger.error("Processing failed: task_id=%s, error=%s", task_id, error_msg)

        # Update status to failed
        async def _update_failed():
            await _update_processing_log_status(
                task_id=task_id,
                status=ProcessingStatus.FAILED,
                message=f"Processing failed: {error_msg}",
                finished_at=datetime.now(),
            )

        asyncio.run(_update_failed())

        # Clean up temp file on error
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

        return {
            "success": False,
            "error": error_msg,
        }


async def _store_aggregates(
    df: pl.DataFrame,
    dashboard_id: UUID,
    task_id: str,
) -> None:
    """Store aggregated data to database.

    Args:
        df: Processed DataFrame.
        dashboard_id: Dashboard ID.
        task_id: Task ID for logging.
    """
    async with get_session() as session:
        async with session.begin():
            # Get graphs for dashboard
            result = await session.execute(
                select(Graph).where(Graph.dashboard_id == dashboard_id)
            )
            graphs = result.scalars().all()

            if not graphs:
                logger.warning("No graphs found for dashboard: %s", dashboard_id)
                return

            # Convert DataFrame to list of dicts
            rows = df.to_dicts()

            # Store aggregates for each graph

            # Clear old data
            await session.execute(
                delete(AggregatedData).where(
                    AggregatedData.dashboard_id == dashboard_id
                )
            )

            # Insert new data
            for row in rows:
                for graph in graphs:
                    dims = {
                        k: v for k, v in row.items() if k in df.columns[:3]
                    }  # Simplified
                    metrics = {k: v for k, v in row.items() if k not in dims}

                    agg = AggregatedData(
                        dashboard_id=dashboard_id,
                        graph_id=graph.id,
                        dims=dims,
                        metrics=metrics,
                    )
                    session.add(agg)

            await session.commit()
            logger.info(
                "Aggregates stored: dashboard_id=%s, rows=%d", dashboard_id, len(rows)
            )


def process_csv_background(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """RQ task entry point for CSV processing.

    This function is called by RQ worker in a separate process.

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.

    Returns:
        dict: Processing result.
    """
    logger.info(
        "Starting background processing: task_id=%s, dashboard_id=%s",
        task_id,
        dashboard_id_str,
    )

    return _process_csv_file_sync_impl(
        file_path_str,
        task_id,
        dashboard_id_str,
        processing_config_dict,
    )
