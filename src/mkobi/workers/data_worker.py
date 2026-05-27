"""RQ worker tasks for background data processing.

Contains functions that are executed by RQ workers in separate processes.
These functions handle CSV processing, status updates, and database operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

from uuid import UUID

import polars as pl
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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

# Default timeout for stale processing logs (in minutes)
DEFAULT_STALE_PROCESSING_TIMEOUT_MINUTES = 30


async def _update_processing_log_status(
    task_id: str,
    status: ProcessingStatus,
    message: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    session: AsyncSession | None = None,
) -> None:
    """Update processing log status.

    Args:
        task_id: Task ID (UUID string).
        status: New status.
        message: Status message.
        started_at: Processing start time (only set if not already set).
        finished_at: Processing finish time.
        session: Optional database session for testing. If None, creates a new session.
    """
    try:
        values: dict[str, Any] = {
            "status": status,
            "message": message,
        }

        if started_at is not None:
            values["started_at"] = started_at
        if status in (ProcessingStatus.SUCCESS, ProcessingStatus.FAILED):
            values["finished_at"] = finished_at or datetime.now(UTC)

        stmt = (
            update(ProcessingLog)
            .where(ProcessingLog.id == UUID(task_id))
            .values(**values)
        )
        if session is not None:
            # Test mode - use provided session (already in transaction)
            await session.execute(stmt)
            if status in (ProcessingStatus.SUCCESS, ProcessingStatus.FAILED):
                await session.commit()
        else:
            # Production mode - create new session
            async with get_session() as db:
                async with db.begin():
                    await db.execute(stmt)
        logger.info(
            "Processing log updated: task_id=%s, status=%s", task_id, status
        )
    except Exception as e:
        logger.error("Error updating processing log: %s", e)


async def cleanup_stale_processing_logs(
    timeout_minutes: int = DEFAULT_STALE_PROCESSING_TIMEOUT_MINUTES,
    session: AsyncSession | None = None,
) -> int:
    """Mark stale PROCESSING entries as FAILED.

    This function should be called periodically to detect processing jobs
    that were left in PROCESSING state due to worker crashes or timeouts.

    Args:
        timeout_minutes: Maximum age in minutes for entries to be considered stale.
            Entries older than this will be marked as FAILED.
        session: Optional database session. If None, creates a new session.

    Returns:
        int: Number of entries that were marked as FAILED.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

    if session is not None:  # Test mode - use provided session (already in transaction)
        stmt = (
            update(ProcessingLog)
            .where(
                ProcessingLog.status == ProcessingStatus.PROCESSING,
                ProcessingLog.started_at < cutoff,
            )
            .values(
                status=ProcessingStatus.FAILED,
                message="Worker timeout - marked as failed by cleanup job",
                finished_at=datetime.now(UTC),
            )
        )
        result = await session.execute(stmt)
        count = result.rowcount if result.rowcount is not None else 0
    else:  # Production mode - create new session
        async with get_session() as db:
            async with db.begin():
                stmt = (
                    update(ProcessingLog)
                    .where(
                        ProcessingLog.status == ProcessingStatus.PROCESSING,
                        ProcessingLog.started_at < cutoff,
                    )
                    .values(
                        status=ProcessingStatus.FAILED,
                        message="Worker timeout - marked as failed by cleanup job",
                        finished_at=datetime.now(UTC),
                    )
                )
                result = await db.execute(stmt)
                count = result.rowcount if result.rowcount is not None else 0

    if count > 0:
        logger.info(
            "Marked %d stale PROCESSING entries as FAILED (timeout=%dm)",
            count,
            timeout_minutes,
        )
    return int(count)


async def _process_csv_file_async(
    file_path_str: str,
    task_id: str,
    dashboard_id_str: str,
    processing_config_dict: dict[str, Any] | None = None,
    mode: str = "overwrite",
    db_session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Async CSV processing implementation.

    Args:
        file_path_str: Path to CSV file as string.
        task_id: Task ID (UUID string).
        dashboard_id_str: Dashboard ID as string.
        processing_config_dict: Processing configuration dictionary.
        mode: Upload mode (overwrite or append).
        db_session: Optional database session for testing. If None, creates a new session.

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
            session=db_session,
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
        await _store_aggregates(df, dashboard_id, task_id, mode, db_session=db_session)

        # Update status to success
        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.SUCCESS,
            message=f"Processing completed successfully: {result_data['rows']} rows processed",
            finished_at=datetime.now(UTC),
            session=db_session,
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
            finished_at=datetime.now(UTC),
            session=db_session,
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
    db_session: AsyncSession | None = None,
) -> None:
    """Store aggregated data to database.

    Args:
        df: Processed DataFrame.
        dashboard_id: Dashboard ID.
        task_id: Task ID for logging.
        mode: Upload mode - "overwrite" clears old data, "append" keeps it.
        db_session: Optional database session for testing. If None, creates a new session.
    """
    from mkobi.data.storage.manager import StorageManager
    from mkobi.models.enums import UploadMode

    if db_session is not None:
        # Test mode - use provided session (already in transaction)
        result = await db_session.execute(
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
                # Validate graph.dimensions is non-empty and contains valid column names
                valid_dimensions = [
                    dim for dim in graph.dimensions if dim in df.columns
                ] if graph.dimensions else []
                if not valid_dimensions:
                    raise ValueError(
                        f"Graph {graph.id} has no valid dimensions configured. "
                        f"Dimensions: {graph.dimensions or 'empty'}. "
                        f"Available DataFrame columns: {list(df.columns)}. "
                        "Please set dimensions in the graph configuration."
                    )
                dims = {
                    k: v for k, v in row.items() if k in valid_dimensions
                }
                metrics = {k: v for k, v in row.items() if k not in dims}

                aggregates.append(
                    {
                        "graph_id": str(graph.id),
                        "dims": dims,
                        "metrics": metrics,
                    }
                )

        manager = StorageManager(db_session)
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
    else:
        # Production mode - create new session
        async with get_session() as session:
            # Use session.begin() for explicit transaction control
            # This ensures atomicity: either all aggregates are saved or none
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
                        # Validate graph.dimensions is non-empty and contains valid column names
                        valid_dimensions = [
                            dim for dim in graph.dimensions if dim in df.columns
                        ] if graph.dimensions else []
                        if not valid_dimensions:
                            raise ValueError(
                                f"Graph {graph.id} has no valid dimensions configured. "
                                f"Dimensions: {graph.dimensions or 'empty'}. "
                                f"Available DataFrame columns: {list(df.columns)}. "
                                "Please set dimensions in the graph configuration."
                            )
                        dims = {
                            k: v for k, v in row.items() if k in valid_dimensions
                        }
                        metrics = {k: v for k, v in row.items() if k not in dims}

                        aggregates.append(
                            {
                                "graph_id": str(graph.id),
                                "dims": dims,
                                "metrics": metrics,
                            }
                        )

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
    db_session: AsyncSession | None = None,
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
        db_session: Optional database session for testing. If None, creates a new session.

    Returns:
        dict: Processing result.
    """
    logger.info(
        "Starting background processing: task_id=%s, dashboard_id=%s, mode=%s",
        task_id,
        dashboard_id_str,
        mode,
    )

    # Use the internal implementation with optional session
    result = await _process_csv_file_async(
        file_path_str=file_path_str,
        task_id=task_id,
        dashboard_id_str=dashboard_id_str,
        processing_config_dict=processing_config_dict,
        mode=mode,
        db_session=db_session,
    )
    return result


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


async def start_stale_processing_cleanup_task(
    interval_seconds: int = 300,  # Run every 5 minutes by default
    timeout_minutes: int = DEFAULT_STALE_PROCESSING_TIMEOUT_MINUTES,
) -> None:
    """Start background task for cleaning up stale processing logs.

    This function runs indefinitely, periodically checking for and marking
    stale PROCESSING entries as FAILED.

    Args:
        interval_seconds: Interval between cleanup runs in seconds.
        timeout_minutes: Timeout threshold for considering entries stale.
    """
    logger.info(
        "Starting stale processing cleanup task (interval=%ds, timeout=%dm)",
        interval_seconds,
        timeout_minutes,
    )
    while True:
        try:
            await cleanup_stale_processing_logs(timeout_minutes=timeout_minutes)
        except Exception as e:
            logger.exception("Error during stale processing cleanup: %s", e)
        await asyncio.sleep(interval_seconds)
