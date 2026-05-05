"""RQ task queue setup for background processing.

Provides queue initialization and job enqueueing functions
using Redis as the message broker.
"""

import logging
from typing import Any

import redis
from rq import Queue

from mko_bi.config import get_redis_client

logger = logging.getLogger(__name__)

# Queue name constants
DEFAULT_QUEUE = "default"
DATA_PROCESSING_QUEUE = "data_processing"


def get_redis_connection() -> redis.Redis:
    """Get Redis connection for RQ.

    Returns:
        redis.Redis: Configured Redis connection.
    """
    return get_redis_client()  # type: ignore[no-any-return]


def get_queue(queue_name: str = DATA_PROCESSING_QUEUE) -> Queue:
    """Get RQ queue by name.

    Args:
        queue_name: Name of the queue to retrieve.

    Returns:
        Queue: RQ queue instance.
    """
    redis_conn = get_redis_connection()
    return Queue(queue_name, connection=redis_conn)


def enqueue_job(
    func: Any,
    *args: Any,
    queue_name: str = DATA_PROCESSING_QUEUE,
    job_timeout: int = 3600,
    **kwargs: Any,
) -> str | None:
    """Enqueue a job to RQ queue.

    Args:
        func: Function to execute in background.
        *args: Positional arguments for the function.
        queue_name: Name of the queue.
        job_timeout: Job timeout in seconds (default: 1 hour).
        **kwargs: Keyword arguments for the function.

    Returns:
        str | None: Job ID if enqueued successfully, None otherwise.
    """
    try:
        queue = get_queue(queue_name)
        job = queue.enqueue(
            func,
            *args,
            **kwargs,
            job_timeout=job_timeout,
        )
        logger.info("Job enqueued: job_id=%s, queue=%s", job.id, queue_name)
        return job.id
    except Exception as e:
        logger.error("Failed to enqueue job: %s", e)
        return None


def get_job_status(job_id: str, queue_name: str = DATA_PROCESSING_QUEUE) -> dict[str, Any] | None:
    """Get job status by ID.

    Args:
        job_id: RQ job ID.
        queue_name: Name of the queue.

    Returns:
        dict | None: Job info if found, None otherwise.
    """
    try:
        queue = get_queue(queue_name)
        job = queue.fetch_job(job_id)
        if job is None:
            logger.warning("Job not found: job_id=%s", job_id)
            return None

        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "exc_info": job.exc_info,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "ended_at": job.ended_at,
        }
    except Exception as e:
        logger.error("Failed to get job status: %s", e)
        return None
