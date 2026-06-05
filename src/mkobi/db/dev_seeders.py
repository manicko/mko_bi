"""Development seeders runner.

This module provides utilities to run database seeders during application startup
in development environment. Seeders create test data for local development.

Usage in DatabaseStarter.startup():
    if self._config.env == EnvironmentEnum.DEVELOPMENT:
        await run_dev_seeders()
"""

import logging
from typing import Any

from mkobi.db.seeders.test_media_dash import ensure_test_media_dash

logger = logging.getLogger(__name__)


async def run_dev_seeders() -> dict[str, Any]:
    """Run all development seeders.

    This function should be called during application startup in development
    environment to ensure test data exists in the database.

    Returns:
        dict with results from all seeders.
    """
    logger.info("Running development seeders...")

    results: dict[str, Any] = {}

    try:
        results["test_media_dash"] = await ensure_test_media_dash()
        logger.info("Development seeders completed successfully")
    except Exception as e:
        logger.error("Development seeders failed: %s", e, exc_info=True)
        # Log but don't raise - seeding failure shouldn't crash the app
        results["error"] = str(e)

    return results