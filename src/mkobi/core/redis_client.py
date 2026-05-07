import logging

import redis
import redis.asyncio as aioredis

from mkobi.config import get_config

logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    """Return synchronous Redis client based on application settings.

    Returns:
        redis.Redis: Synchronous Redis client instance.
    """
    config = get_config()
    logger.debug(
        "Initializing synchronous Redis client: host=%s, port=%s, db=%s",
        config.redis.host,
        config.redis.port,
        config.redis.db,
    )
    return redis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        password=config.redis.password,
        decode_responses=True,
    )


def get_async_redis_client() -> aioredis.Redis:
    """Return asynchronous Redis client based on application settings.

    Returns:
        redis.asyncio.Redis: Asynchronous Redis client instance.
    """
    config = get_config()
    logger.debug(
        "Initializing asynchronous Redis client: host=%s, port=%s, db=%s",
        config.redis.host,
        config.redis.port,
        config.redis.db,
    )
    return aioredis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        password=config.redis.password,
        decode_responses=True,
    )
