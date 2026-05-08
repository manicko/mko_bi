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
from sqlalchemy import select, update

from mkobi.data.loaders.loader import CSVLoader
from mkobi.data.processing.transformations import (
    apply_transformations,
    calculate_aggregations,
)
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
        started_at: Processing start time (only set if not already set).
        finished_at: Processing finish time.
    """
    async with get_session() as session:
        async with session.begin():
            values: dict[str, Any] = {
                "status": status,
                "message": message,
            }

            if started_at is not None:
                values["started_at"] = started_at
            if status in (ProcessingStatus.SUCCESS, ProcessingStatus.FAILED):
                values["finished_at"] = finished_at or datetime.now()

            stmt = (
                update(ProcessingLog)
                .where(ProcessingLog.id == UUID(task_id))
                .values(**values)
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(
                "Processing log updated: task_id=%s, status=%s", task_id, status
            )


async def _process_csv_file_async(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
    mode: str = "overwrite",
) -> dict[str, Any]:
    """Async CSV processing implementation.

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.
        mode: Upload mode (overwrite or append).

    Returns:
        dict: Processing result with status and data.
    """
    file_path = Path(file_path_str)
    dashboard_id = UUID(dashboard_id_str)

    try:
        # Update status to processing
        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.PROCESSING,
            message="Processing started (background task)",
        )

        # Load and process CSV (run in thread since Polars is sync)
        loader = CSVLoader()
        df = await asyncio.to_thread(loader.load_csv, file_path)
        logger.info("File loaded: %d rows, %d columns", df.shape[0], df.shape[1])

        # Apply processing config if provided
        if processing_config_dict:
            config = ProcessingConfig(**processing_config_dict)

            # Apply transformations in thread
            df = await asyncio.to_thread(
                apply_transformations,
                df=df,
                filters=config.filters,
                groupby=config.groupby if not config.aggregations else None,
                sort_by=config.sort_by,
                descending=config.descending,
                limit=config.limit,
            )

            # Apply aggregations in thread
            if (
                config.aggregations
                or config.yoy_config
                or config.share_config
                or config.custom_metrics
            ):
                df = await asyncio.to_thread(
                    calculate_aggregations,
                    df=df,
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

        # Store aggregates in database with mode
        await _store_aggregates(df, dashboard_id, task_id, mode)

        # Update status to success
        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.SUCCESS,
            message=f"Processing completed successfully: {result_data['rows']} rows processed",
            finished_at=datetime.now(),
        )

        # Clean up temp file
        if file_path.exists():
            await asyncio.to_thread(file_path.unlink)
            logger.info("Temp file deleted: %s", file_path)

        return {
            "success": True,
            "rows_processed": result_data["rows"],
            "message": "Processing completed",
        }

    except Exception as e:
        error_msg = str(e)
        logger.exception("Processing failed: task_id=%s, error=%s", task_id, error_msg)

        # Update status to failed
        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.FAILED,
            message=f"Processing failed: {error_msg}",
            finished_at=datetime.now(),
        )

        # Clean up temp file on error
        if file_path.exists():
            try:
                await asyncio.to_thread(file_path.unlink)
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
    mode: str = "overwrite",
) -> None:
    """Store aggregated data to database.

    Args:
        df: Processed DataFrame.
        dashboard_id: Dashboard ID.
        task_id: Task ID for logging.
        mode: Upload mode - "overwrite" clears old data, "append" keeps it.
    """
    from mkobi.data.storage.manager import StorageManager
    from mkobi.models.enums import UploadMode

    async with get_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Graph).where(Graph.dashboard_id == dashboard_id)
            )
            graphs = result.scalars().all()

            if not graphs:
                logger.warning("No graphs found for dashboard: %s", dashboard_id)
                return

            rows = df.to_dicts()

            aggregates = []
            for row in rows:
                for graph in graphs:
                    dims = {k: v for k, v in row.items() if k in df.columns[:3]}
                    metrics = {k: v for k, v in row.items() if k not in dims}

                    aggregates.append({
                        "graph_id": str(graph.id),
                        "dims": dims,
                        "metrics": metrics,
                    })

            manager = StorageManager(session)
            clear_old = (mode == UploadMode.OVERWRITE)
            processed = await manager.save_aggregates(
                dashboard_id=dashboard_id,
                aggregates=aggregates,
                clear_old=clear_old,
            )

            logger.info(
                "Aggregates stored: dashboard_id=%s, rows=%d, mode=%s, processed=%d",
                dashboard_id,
                len(rows),
                mode,
                processed,
            )


async def process_csv_background(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
    mode: str = "overwrite",
) -> dict[str, Any]:
    """Background task entry point for CSV processing.

    This function is called by the task queue (async) or RQ worker.
    Uses asyncio.to_thread() for RQ compatibility.

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.
        mode: Upload mode (overwrite or append).

    Returns:
        dict: Processing result.
    """
    logger.info(
        "Starting background processing: task_id=%s, dashboard_id=%s, mode=%s",
        task_id,
        dashboard_id_str,
        mode,
    )

    return await _process_csv_file_async(
        file_path_str=file_path_str,
        task_id=task_id,
        dashboard_id_str=dashboard_id_str,
        processing_config_dict=processing_config_dict,
        mode=mode,
    )


def process_csv_background_sync(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
    mode: str = "overwrite",
) -> dict[str, Any]:
    """RQ worker entry point (sync wrapper).

    This function is called by RQ worker in a separate process.
    Runs the async implementation using asyncio.run().

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.
        mode: Upload mode (overwrite or append).

    Returns:
        dict: Processing result.
    """
    return asyncio.run(
        process_csv_background(
            file_path_str=file_path_str,
            task_id=task_id,
            dashboard_id_str=dashboard_id_str,
            processing_config_dict=processing_config_dict,
            mode=mode,
        )
    )
