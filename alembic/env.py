import asyncio
import logging
import os
from logging.config import fileConfig

from sqlalchemy import Connection, pool, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models to ensure they're registered with Base metadata
from mkobi.db.models import (  # noqa: F401, E402
    AggregatedData,
    Dashboard,
    DashboardAccess,
    Filter,
    Graph,
    Layout,
    ProcessingConfig,
    ProcessingLog,
    User,
)
from mkobi.db.base import Base  # noqa: E402

target_metadata = Base.metadata

# Get database URL from alembic config first (set by _apply_migrations)
# If not set, fall back to environment or app config
db_url = config.get_main_option("sqlalchemy.url")
if db_url is None:
    db_url = os.environ.get("DATABASE_URL")
if db_url is None:
    from mkobi.config import get_config

    app_config = get_config()
    db_url = app_config.DATABASE_URL

if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

logger = logging.getLogger("alembic.env")

# Advisory lock key for migration synchronization
# Used to prevent concurrent migrations in multi-instance deployments
MIGRATION_ADVISORY_LOCK_KEY = 42


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(sync_connection: Connection) -> None:
    """Sync wrapper to run migrations using a sync connection proxy."""
    context.configure(
        connection=sync_connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' async mode.

    Uses pg_advisory_lock to prevent concurrent migrations in multi-instance
    deployments. The lock is acquired before running migrations and released
    afterwards, even if migrations fail.
    """
    db_url = config.get_main_option("sqlalchemy.url")
    if db_url is None:
        raise ValueError("Database URL is not configured in alembic.ini or env.py")
    connectable: AsyncEngine = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        try:
            # Acquire advisory lock to prevent concurrent migrations
            await connection.execute(
                text(f"SELECT pg_advisory_lock({MIGRATION_ADVISORY_LOCK_KEY})")
            )
            await connection.commit()

            try:
                await connection.run_sync(do_run_migrations)
            finally:
                # Always release the advisory lock
                await connection.execute(
                    text(f"SELECT pg_advisory_unlock({MIGRATION_ADVISORY_LOCK_KEY})")
                )
                await connection.commit()
        except Exception:
            # Ensure lock is released on any error
            try:
                await connection.execute(
                    text(f"SELECT pg_advisory_unlock({MIGRATION_ADVISORY_LOCK_KEY})")
                )
                await connection.commit()
            except Exception:
                pass
            raise
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async wrapper)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
