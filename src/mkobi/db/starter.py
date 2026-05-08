"""Модуль воспроизведения структуры БД.

Автоматически проверяет состояние БД при старте FastAPI
и применяет миграции Alembic в соответствии с окружением.
"""

import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from anyio import to_thread
from typing import cast

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from mkobi.config import get_config
from mkobi.models.enums import EnvironmentEnum

logger = logging.getLogger(__name__)


class DatabaseNotFoundError(Exception):
    """База данных не найдена."""


class SchemaNotFoundError(Exception):
    """Схема БД не найдена."""


class DatabaseStarterConfig:
    """Конфигурация модуля воспроизведения БД."""

    def __init__(
        self,
        env: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT,
        main_database_url: str | None = None,
        test_database_url: str | None = None,
        auto_migrate: bool = False,
        migration_script_path: str = "alembic",
        alembic_ini_path: str = "alembic.ini",
        recreate_test_db: bool = False,
        logs_retention_days: int = 30,
    ) -> None:
        self.env = env
        self.main_database_url = main_database_url
        self.test_database_url = test_database_url
        self.auto_migrate = auto_migrate
        self.migration_script_path = migration_script_path
        self.alembic_ini_path = alembic_ini_path
        self.recreate_test_db = recreate_test_db
        self.logs_retention_days = logs_retention_days


class DatabaseStarter:
    """Main class for database initialization and migration management."""

    def __init__(self, config: DatabaseStarterConfig | None = None) -> None:
        self._config = config or DatabaseStarterConfig()
        self._main_engine: AsyncEngine | None = None
        self._test_engine: AsyncEngine | None = None

    async def startup(self) -> None:
        """Main entry point for database initialization."""
        logger.info("Starting database initialization...")

        # Check main database
        main_url = self._config.main_database_url or get_config().database.url
        if not main_url:
            raise DatabaseNotFoundError("Main database URL not configured")

        # Create main engine
        self._main_engine = create_async_engine(main_url)
        assert self._main_engine is not None

        # Check if database exists
        try:
            async with self._main_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.error("Main database not accessible: %s", e)
            raise DatabaseNotFoundError(f"Main database not accessible: {e}") from e

        # Check if schema exists (check for alembic_version table)
        try:
            assert self._main_engine is not None
            async with self._main_engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_name = 'alembic_version'"
                    )
                )
                schema_exists = result.scalar()
                if not schema_exists:
                    raise SchemaNotFoundError("Schema not initialized")
        except SchemaNotFoundError:
            raise
        except Exception as e:
            logger.warning("Could not check schema: %s", e)

        # Apply migrations if needed
        if self._config.auto_migrate:
            assert self._main_engine is not None
            await self._apply_migrations(main_url)

        # Handle test database
        if self._config.env == EnvironmentEnum.TEST or self._config.recreate_test_db:
            await self.recreate_test_database()

        logger.info("Database initialization completed successfully")

    async def recreate_test_database(self) -> None:
        """Recreate test database from scratch."""
        test_url = self._config.test_database_url or get_config().test_database_url
        if not test_url:
            logger.warning("Test database URL not configured, skipping")
            return

        logger.info("Recreating test database...")

        # Create test engine with autocommit mode
        # (required for DROP/CREATE DATABASE in PostgreSQL)
        self._test_engine = create_async_engine(
            test_url,
            isolation_level="AUTOCOMMIT",
        )

        # Drop and recreate test database
        try:
            async with self._test_engine.connect() as conn:
                await conn.execute(text("DROP DATABASE IF EXISTS test_bidb"))
                await conn.execute(text("CREATE DATABASE test_bidb"))
        except Exception as e:
            logger.error("Failed to recreate test database: %s", e)
            raise

        # Apply migrations to test database
        # (use a new engine without autocommit for migrations)
        migration_engine = create_async_engine(test_url)
        await self._apply_migrations(test_url)
        await migration_engine.dispose()

        logger.info("Test database recreated successfully")

    async def _apply_migrations(self, db_url: str) -> None:
        """Apply Alembic migrations to the specified database."""

        def _sync_migrate() -> None:
            """Synchronous migration function for to_thread."""
            alembic_ini = self._config.alembic_ini_path

            # Override the database URL in alembic config
            config = Config(alembic_ini)
            config.set_main_option("sqlalchemy.url", db_url)

            # Run migrations
            command.upgrade(config, "head")

        logger.info(f"Running migrations for {db_url}...")
        await to_thread(_sync_migrate)
        logger.info("Migrations applied successfully")

    async def _populate_alembic_version(self) -> None:
        """Populate alembic_version with current HEAD version.

        TASK-DB-001: Fix alembic_version table - populate with current version.
        """
        # Get HEAD revision from alembic
        alembic_ini = self._config.alembic_ini_path

        try:
            result = subprocess.run(
                ["uv", "run", "alembic", "-c", alembic_ini, "heads"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            if result.returncode != 0:
                logger.error(f"Failed to get alembic heads: {result.stderr}")
                return

            # Parse the head revision (format: "revision (head), description")
            head_line = (
                result.stdout.strip().split("\n")[0] if result.stdout.strip() else ""
            )
            revision = head_line.split(" ")[0] if head_line else ""

            if not revision:
                logger.warning("Could not determine alembic head revision")
                return

            # Insert into alembic_version
            async with cast(AsyncEngine, self._main_engine).connect() as conn:
                await conn.execute(
                    text(
                        "INSERT INTO alembic_version (version_num) "
                        "VALUES (:revision) ON CONFLICT DO NOTHING"
                    ),
                    {"revision": revision},
                )
                await conn.commit()

            logger.info(f"Alembic version populated with revision: {revision}")
        except Exception as e:
            logger.error(f"Failed to populate alembic_version: {e}")

    async def cleanup_old_logs(self) -> None:
        """Clean up old processing logs based on retention policy."""
        if self._config.logs_retention_days <= 0:
            return

        cutoff_date = datetime.now() - timedelta(days=self._config.logs_retention_days)

        async with cast(AsyncEngine, self._main_engine).connect() as conn:
            result = await conn.execute(
                text(
                    "DELETE FROM processing_logs "
                    "WHERE started_at < :cutoff AND status IN ('success', 'failed')"
                ),
                {"cutoff": cutoff_date},
            )
            await conn.commit()

            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} old processing logs")


def main() -> None:
    """Точка входа для пересоздания тестовой БД через CLI."""
    if "--recreate-test-db" in sys.argv:
        starter = DatabaseStarter()

        asyncio.run(starter.recreate_test_database())
    else:
        print("Usage: python -m mkobi.db.starter --recreate-test-db")


if __name__ == "__main__":
    main()
