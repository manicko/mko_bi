"""Database schema reproduction module.

Automatically checks database state on FastAPI startup
and applies Alembic migrations according to the environment.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import cast

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from mkobi.config import get_config
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import EnvironmentEnum, UserRole
from mkobi.services.file_cleanup import cleanup_stale_temp_files

logger = logging.getLogger(__name__)


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
        self._test_engine: AsyncEngine | None = None

    async def startup(self) -> None:
        """Main entry point for database initialization."""
        logger.info("Starting database initialization...")

        # Check main database
        main_url = self._config.main_database_url or get_config().DATABASE_URL
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
                        "WHERE table_name = 'alembic_version')"
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

        # Ensure admin user exists (after migrations, before test DB handling)
        await self.ensure_admin_user()

        # Clean up orphaned temp files from previous runs
        deleted_count = cleanup_stale_temp_files()
        if deleted_count > 0:
            logger.info("Cleaned up %d orphaned temp files during startup", deleted_count)

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

        # Parse the test URL to get the base connection details
        # Connect to 'postgres' database to be able to drop/create bidb_test
        base_url = test_url.rsplit("/", 1)[0] + "/postgres"

        # Create engine connected to 'postgres' database with autocommit
        admin_engine = create_async_engine(
            base_url,
            isolation_level="AUTOCOMMIT",
        )

        # Drop and recreate test database
        try:
            async with admin_engine.connect() as conn:
                # Terminate existing connections to bidb_test
                await conn.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) "
                        "FROM pg_stat_activity "
                        "WHERE datname = 'bidb_test'"
                    )
                )
                await conn.execute(text("DROP DATABASE IF EXISTS bidb_test"))
                await conn.execute(text("CREATE DATABASE bidb_test"))
            await admin_engine.dispose()
        except Exception as e:
            logger.error("Failed to recreate test database: %s", e)
            await admin_engine.dispose()
            raise

        # Apply migrations to test database
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

        logger.info("Running migrations for %s...", db_url)
        await asyncio.to_thread(_sync_migrate)
        logger.info("Migrations applied successfully")

    async def ensure_admin_user(self) -> None:
        """Create admin user if it does not already exist.

        Idempotent — safe to run multiple times. Uses a SAVEPOINT
        (nested transaction) so that IntegrityError from duplicate
        email is caught cleanly without aborting the outer transaction.
        """
        config = get_config()
        admin_email = config.admin_username
        admin_password = config.admin_password

        # Warn if using default credentials (not production due to config validation)
        if admin_email == "admin":
            logger.warning(
                "Using default admin username - set ADMIN_USERNAME environment variable"
            )

        logger.info("Ensuring admin user exists: %s", admin_email)

        user_repo = UserRepository()
        assert self._main_engine is not None

        async with self._main_engine.begin() as conn:
            # Create a SAVEPOINT for idempotent user creation
            try:
                async with conn.begin_nested():
                    user = await user_repo.get_by_email(email=admin_email, db=conn)
                    if user is not None:
                        logger.info("Admin user already exists: %s", admin_email)
                        return

                    from mkobi.core.security import hash_password

                    password_hash = hash_password(admin_password)
                    await user_repo.create(
                        db=conn,
                        email=admin_email,
                        password_hash=password_hash,
                        role=UserRole.ADMIN,
                    )
                    logger.info("Admin user created successfully: %s", admin_email)
            except IntegrityError:
                logger.warning(
                    "Admin user already exists (IntegrityError): %s", admin_email
                )

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
        if self._test_engine:
            await self._test_engine.dispose()
            self._test_engine = None
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
