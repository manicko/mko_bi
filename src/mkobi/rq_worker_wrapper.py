"""RQ worker startup wrapper with Redis connection retry logic.

Provides a connection wrapper that retries Redis connection on startup failures
with exponential backoff, allowing the RQ worker to gracefully handle temporary
Redis unavailability during container startup.
"""

import asyncio
import logging
import sys

import redis
import rq

from mkobi.config import get_config

logger = logging.getLogger(__name__)

# Maximum number of retry attempts for Redis connection
MAX_RETRIES = 3

# Base delay in seconds for exponential backoff
BASE_DELAY_SECONDS = 2


async def check_redis_connection(redis_url: str, max_retries: int = MAX_RETRIES) -> bool:
    """Check Redis connectivity with exponential backoff retry.

    Attempts to connect to Redis and pings it. Retries on connection failures
    using exponential backoff (2^attempt seconds).

    Args:
        redis_url: Redis connection URL (e.g., redis://redis:6379/0).
        max_retries: Maximum number of connection attempts.

    Returns:
        bool: True if connection successful, False otherwise.

    Raises:
        ConnectionError: If all retry attempts fail.
    """
    for attempt in range(max_retries):
        try:
            client = redis.Redis.from_url(redis_url)
            client.ping()
            client.close()
            if attempt > 0:
                logger.info(
                    "Redis connection established after %d attempt(s)",
                    attempt + 1,
                )
            return True
        except (ConnectionError, redis.ConnectionError, OSError) as e:
            if attempt < max_retries - 1:
                delay = BASE_DELAY_SECONDS ** attempt
                logger.warning(
                    "Redis connection attempt %d/%d failed: %s. Retrying in %ds...",
                    attempt + 1,
                    max_retries,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Redis connection failed after %d attempts: %s",
                    max_retries,
                    e,
                )
                raise ConnectionError(
                    f"Failed to connect to Redis after {max_retries} attempts: {e}"
                ) from e
    return False


def start_rq_worker(redis_url: str | None = None) -> None:
    """Start RQ worker with Redis connection retry logic.

    Creates an RQ worker that connects to Redis. Retries the connection on startup
    failures with exponential backoff. This allows the worker to handle temporary
    Redis unavailability during container startup.

    Args:
        redis_url: Redis connection URL. If None, uses the URL from config.

    Raises:
        SystemExit: If Redis connection fails after all retries.
    """
    if redis_url is None:
        config = get_config()
        redis_url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"

    try:
        # Run async connection check with retry
        asyncio.run(check_redis_connection(redis_url))
    except ConnectionError as e:
        logger.error("Unable to start RQ worker: %s", e)
        sys.exit(1)

    # Import data worker module (ensures task registration)
    import mkobi.workers.data_worker  # noqa: F401

    # RQ Worker uses Redis connection directly via URL
    queue = rq.Queue(connection=redis.Redis.from_url(redis_url))
    worker = rq.Worker([queue])
    worker.work()


if __name__ == "__main__":
    start_rq_worker()
