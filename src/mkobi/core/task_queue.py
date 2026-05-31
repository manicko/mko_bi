"""In-memory async task queue for data processing.

Provides a simple MVP queue using asyncio.Queue with status tracking.
For production, replace with Redis/RabbitMQ and integrate with processing_logs.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from typing import Any

from mkobi.models.enums import ProcessingStatus

logger = logging.getLogger(__name__)


class TaskQueue:
    """In-memory async task queue for MVP.

    Uses asyncio.Queue for task storage and tracks task status in memory.
    For production, replace with a persistent message broker and integrate with processing_logs.
    """

    def __init__(self) -> None:
        """Initialize task queue."""
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._statuses: dict[str, ProcessingStatus] = {}
        self._results: dict[str, Any] = {}
        self._errors: dict[str, str | None] = {}

    async def enqueue(self, task_func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Enqueue a task for async processing.

        Args:
            task_func: Async function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            str: Unique task ID.
        """
        task_id = str(uuid.uuid4())
        self._statuses[task_id] = ProcessingStatus.STARTED
        await self._queue.put({
            "task_id": task_id,
            "func": task_func,
            "args": args,
            "kwargs": kwargs,
        })
        logger.info("Task enqueued: task_id=%s", task_id)
        return task_id

    async def enqueue_with_worker(
        self, job_func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> str:
        """Enqueue a job for background worker processing.

        MVP: Uses in-memory queue (non-persistent, tasks lost on restart).
        Production: Replace with RQ enqueue via Redis for persistence and scaling.
        See docs/11-guides/task-queue-migration.md for migration guide.

        This method serves as the integration point for background worker migration.
        The stub below delegates to the in-memory queue; during migration, replace
        the implementation with `rq.Queue.enqueue()` for Redis/RQ compatibility.

        Args:
            job_func: Function to execute (sync for RQ, async for in-memory).
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            str: Unique job/task ID.
        """
        return await self.enqueue(job_func, *args, **kwargs)

    async def process_next(self) -> None:
        """Process the next task in the queue.

        Executes the task function and updates status to COMPLETED or FAILED.
        """
        try:
            task = await self._queue.get()
            task_id = task["task_id"]
            func = task["func"]
            args = task["args"]
            kwargs = task["kwargs"]

            self._statuses[task_id] = ProcessingStatus.PROCESSING
            try:
                result = await func(*args, **kwargs)
                self._statuses[task_id] = ProcessingStatus.COMPLETED
                self._results[task_id] = result
                logger.info("Task processed successfully: task_id=%s", task_id)
            except Exception as e:
                self._statuses[task_id] = ProcessingStatus.FAILED
                self._errors[task_id] = str(e)
                logger.error("Task failed: task_id=%s, error=%s", task_id, e)
            finally:
                self._queue.task_done()
        except asyncio.QueueEmpty:
            logger.debug("No tasks to process")
        except Exception as e:
            logger.error("Error processing task: %s", e)

    async def get_status(self, task_id: str) -> ProcessingStatus:
        """Get task status by ID.

        Args:
            task_id: Task identifier.

        Returns:
            ProcessingStatus: Current status of the task.
        """
        status = self._statuses.get(task_id)
        if status is None:
            logger.warning("Task not found: task_id=%s", task_id)
            return ProcessingStatus.FAILED
        return status

    async def get_result(self, task_id: str) -> Any:
        """Get task result by ID.

        Args:
            task_id: Task identifier.

        Returns:
            Any: Task result, or None if not completed.
        """
        return self._results.get(task_id)

    async def get_error(self, task_id: str) -> str | None:
        """Get task error by ID.

        Args:
            task_id: Task identifier.

        Returns:
            Optional[str]: Error message, or None if no error.
        """
        return self._errors.get(task_id)

    async def shutdown(self) -> None:
        """Log warning for pending tasks on shutdown.

        Called during application shutdown to warn about tasks that will be lost.
        """
        pending = self._queue.qsize()
        if pending > 0:
            logger.warning(
                "TaskQueue shutting down with %d pending tasks. "
                "These will be lost. Consider using Redis/RQ for persistence.",
                pending,
            )


# Global default queue instance for backward compatibility
default_queue = TaskQueue()


async def enqueue_job(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> str | None:
    """Compatibility function for enqueueing jobs.

    Args:
        func: Async function to execute.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        str | None: Task ID if enqueued, None otherwise.
    """
    try:
        return await default_queue.enqueue(func, *args, **kwargs)
    except Exception as e:
        logger.error("Failed to enqueue job: %s", e)
        return None


def get_task_queue() -> TaskQueue:
    """Get default task queue instance."""
    return default_queue
