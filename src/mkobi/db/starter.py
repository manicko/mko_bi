"""Database schema reproduction module.

Automatically checks database state on FastAPI startup
and applies Alembic migrations according to the environment.
"""

import asyncio
import logging
import re
import sys
import uuid
from datetime import datetime, timedelta
from typing import cast

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from mkobi.config import get_config
from mkobi.core.security import hash_password
from mkobi.models.enums import EnvironmentEnum, UserRole
from mkobi.services.file_cleanup import cleanup_stale_temp_files

logger = logging.getLogger(__name__)

# Timeout constants for DB operations
DB_CONNECT_TIMEOUT = 10.0
DB_HEALTH_CHECK_TIMEOUT = 5.0


class DatabaseNotFoundError(Exception):
    """Database not found."""


class SchemaNotFoundError(Exception):
    """Database schema not found."""


class DatabaseStarterConfig:
    """Database starter configuration."""

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

    async def _check_db_connection(self) -> None:
        """Check database connectivity with timeout."""
        assert self._main_engine is not None
        try:
            async with asyncio.timeout(DB_CONNECT_TIMEOUT):
                async with self._main_engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
        except TimeoutError:
            raise DatabaseNotFoundError("Database connection timed out") from None
        except Exception as e:
            logger.error("Main database not accessible: %s", e)
            raise DatabaseNotFoundError(f"Main database not accessible: {e}") from e

    async def _get_alembic_revision(self) -> str | None:
        """Get current alembic revision from database.

        Returns revision hash if schema is initialized, None otherwise.
        """
        try:
            # Query the alembic_version table directly to avoid asyncio.run issues
            from sqlalchemy import text
            async with self._main_engine.connect() as conn:
                result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                row = result.fetchone()
                if row:
                    return row[0]
            return None
        except Exception:
            return None

    async def startup(self) -> None:
        """Main entry point for database initialization."""
        logger.info("Starting database initialization...")

        # Check main database
        main_url = self._config.main_database_url or get_config().DATABASE_URL
        if not main_url:
            raise DatabaseNotFoundError("Main database URL not configured")

        # Create main engine with connection pool settings
        self._main_engine = create_async_engine(
            main_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        assert self._main_engine is not None

        # Check database connectivity with timeout
        await self._check_db_connection()

        # Apply migrations if configured (this also creates the schema)
        if self._config.auto_migrate:
            await self._apply_migrations(main_url)

        # Check if schema is properly initialized via alembic
        current_rev = await self._get_alembic_revision()
        if not current_rev:
            raise SchemaNotFoundError(
                "Database schema not initialized - no alembic revision found"
            )
        logger.info("Database schema initialized at revision: %s", current_rev)

        # Ensure admin user exists (after migrations, before test DB handling)
        await self.ensure_admin_user()

        # Clean up orphaned temp files from previous runs
        deleted_count = cleanup_stale_temp_files()
        if deleted_count > 0:
            logger.info("Cleaned up %d orphaned temp files during startup", deleted_count)

        # Clean up old processing logs based on retention policy
        await self.cleanup_old_logs()

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

        # Parse the test URL to get the database name
        parsed_url = make_url(test_url)
        db_name = parsed_url.database

        # Validate database name against safe pattern to prevent SQL injection
        if not db_name or not re.match(r"^[a-zA-Z0-9_]+$", db_name):
            raise ValueError(f"Invalid database name: {db_name}")

        # Connect to 'postgres' database to be able to drop/create target database
        base_url = test_url.rsplit("/", 1)[0] + "/postgres"

        # Create engine connected to 'postgres' database with autocommit
        admin_engine = create_async_engine(
            base_url,
            isolation_level="AUTOCOMMIT",
        )

        # Drop and recreate test database
        try:
            async with admin_engine.connect() as conn:
                # Terminate existing connections to the target database
                await conn.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) "
                        "FROM pg_stat_activity "
                        "WHERE datname = :db_name"
                    ),
                    {"db_name": db_name},
                )
                await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
                await conn.execute(text(f"CREATE DATABASE {db_name}"))
            await admin_engine.dispose()
        except Exception as e:
            logger.error("Failed to recreate test database: %s", e)
            await admin_engine.dispose()
            raise

        # Apply migrations to test database
        await self._apply_migrations(test_url)

        logger.info("Test database recreated successfully")

    async def _apply_migrations(self, db_url: str) -> None:
        """Apply Alembic migrations to the specified database.

        Advisory lock is acquired in alembic/env.py to prevent concurrent
        migrations in multi-instance deployments.
        """

        def _sync_migrate() -> None:
            """Synchronous migration function for to_thread."""
            alembic_ini = self._config.alembic_ini_path

            # Override the database URL in alembic config
            config = Config(alembic_ini)
            config.set_main_option("sqlalchemy.url", db_url)

            # Run migrations (advisory lock handled in alembic/env.py)
            command.upgrade(config, "head")

        safe_url = make_url(db_url).render_as_string(hide_password=True)
        logger.info("Running migrations for %s...", safe_url)
        await asyncio.to_thread(_sync_migrate)
        logger.info("Migrations applied successfully")

    async def ensure_admin_user(self) -> None:
        """Create admin user if it does not already exist.

        Idempotent — safe to run multiple times.
        Uses atomic UPSERT to avoid race conditions on concurrent startup.
        """
        from mkobi.db.session import get_async_sessionlocal

        config = get_config()
        admin_email = config.admin_username
        admin_password = config.admin_password

        # Warn if using default credentials (not production due to config validation)
        if admin_email == "admin":
            logger.warning(
                "Using default admin username - set ADMIN_USERNAME environment variable"
            )

        SessionLocal = await get_async_sessionlocal()

        async with SessionLocal() as db:
            async with db.begin():
                await db.execute(
                    text(
                        "INSERT INTO users (id, email, password_hash, role, is_active) "
                        "VALUES (:id, :email, :password, :role, true) "
                        "ON CONFLICT (email) DO NOTHING"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "email": admin_email,
                        "password": hash_password(admin_password),
                        "role": UserRole.ADMIN,
                    },
                )
            logger.info("Admin user ensured: %s", admin_email)

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
                logger.info("Cleaned up %d old processing logs", result.rowcount)

    async def shutdown(self) -> None:
        """Dispose database engines on application shutdown."""
        if self._main_engine:
            await self._main_engine.dispose()
            self._main_engine = None
        logger.info("Database engines disposed")


def main() -> None:
    """Entry point for recreating test database via CLI."""
    if "--recreate-test-db" in sys.argv:
        starter = DatabaseStarter()

        asyncio.run(starter.recreate_test_database())
    else:
        logger.error("Usage: python -m mkobi.db.starter --recreate-test-db")


if __name__ == "__main__":
    main()
