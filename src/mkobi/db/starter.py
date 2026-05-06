"""Модуль воспроизведения структуры БД.

Автоматически проверяет состояние БД при старте FastAPI
и применяет миграции Alembic в соответствии с окружением.
"""

import logging
from asyncio import to_thread

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command
from alembic.config import Config

from mkobi.config import get_config
from mkobi.models.user_roles import EnvironmentEnum

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
    """Модуль воспроизведения структуры БД."""

    def __init__(self) -> None:
        self._config = self._load_config()
        self._engine: AsyncEngine | None = None

    def _load_config(self) -> DatabaseStarterConfig:
        """Загрузка конфигурации из Settings (YAML)."""
        settings = get_config()

        # Определяем окружение из настроек
        try:
            env = EnvironmentEnum(settings.env)
        except ValueError:
            logger.warning(f"Unknown ENV value: {settings.env}, defaulting to development")
            env = EnvironmentEnum.DEVELOPMENT

        # Получаем URL из settings (yaml/config)
        main_db_url = settings.DATABASE_URL
        test_db_url = settings.test_database_url

        # Auto migrate: из настроек или по умолчанию для dev/test
        auto_migrate = settings.auto_migrate

        if env == EnvironmentEnum.DEVELOPMENT and not settings.auto_migrate:
            auto_migrate = True

        if env == EnvironmentEnum.TEST and not settings.auto_migrate:
            auto_migrate = True

        migration_script_path = settings.migration_script_path
        alembic_ini_path = settings.alembic_ini_path
        recreate_test_db = settings.recreate_test_db
        logs_retention_days = getattr(settings, 'logs_retention_days', 30)

        return DatabaseStarterConfig(
            env=env,
            main_database_url=main_db_url,
            test_database_url=test_db_url,
            auto_migrate=auto_migrate,
            migration_script_path=migration_script_path,
            alembic_ini_path=alembic_ini_path,
            recreate_test_db=recreate_test_db,
            logs_retention_days=logs_retention_days,
        )

    async def startup(self) -> None:
        """Действия при старте приложения."""
        logger.info(f"Starting database initialization for ENV={self._config.env}")

        if self._config.env == EnvironmentEnum.TEST and self._config.recreate_test_db:
            await self.recreate_test_database()

        # 1. Проверка существования БД
        await self._check_database_exists()

        # 2. Проверка схемы и версии
        schema_exists = await self._check_schema_exists()

        # 3. Обработка отсутствия схемы или версии
        if not schema_exists:
            await self._handle_missing_schema()
        else:
            # TASK-DB-001 & TASK-DB-007: Check if version needs to be populated
            await self._check_and_fix_version()

        # 4. Cleanup old logs (TASK-DB-010)
        if self._config.logs_retention_days > 0:
            await self.cleanup_old_logs(self._config.logs_retention_days)

        logger.info("Database initialization completed")

    async def _check_and_fix_version(self) -> None:
        """Check if alembic_version is populated and fix if needed.
        
        TASK-DB-001: Fix alembic_version table - populate with current version.
        TASK-DB-007: Enhance starter.py to verify alembic_version has value.
        """
        if self._config.env == EnvironmentEnum.PRODUCTION:
            # In production, only warn, don't auto-fix
            return

        if not self._config.auto_migrate and self._config.env != EnvironmentEnum.TEST:
            logger.warning("auto_migrate is disabled, skipping version fix")
            return

        if not self._config.main_database_url:
            logger.warning("No database URL configured, skipping version check")
            return

        engine = create_async_engine(self._config.main_database_url)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM alembic_version")
                )
                row = result.first()
                count = row[0] if row else 0

                if count == 0:
                    logger.warning("alembic_version is empty, populating with current version...")
                    await self._populate_alembic_version()
        except Exception as e:
            logger.warning(f"Failed to check/fix version: {e}")
        finally:
            await engine.dispose()

    async def shutdown(self) -> None:
        """Действия при завершении приложения."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")

    async def _check_database_exists(self) -> None:
        """Проверка существования БД через попытку подключения."""
        if not self._config.main_database_url:
            raise DatabaseNotFoundError("MAIN_DATABASE_URL is not configured")

        try:
            engine = create_async_engine(self._config.main_database_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            logger.info("Database exists and is accessible")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseNotFoundError(f"Database not found: {e}") from e

    async def _check_schema_exists(self) -> bool:
        """Проверка наличия таблицы alembic_version и наличия в ней версии."""
        if not self._config.main_database_url:
            return False

        engine = create_async_engine(self._config.main_database_url)
        try:
            async with engine.connect() as conn:
                # Check if table exists
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_name = 'alembic_version'"
                        ")"
                    )
                )
                row = result.first()
                table_exists = row is not None and row[0]

                if not table_exists:
                    logger.info("alembic_version table does not exist")
                    return False

                # Check if table has a version recorded (TASK-DB-007)
                version_check = await conn.execute(
                    text("SELECT COUNT(*) FROM alembic_version")
                )
                count_row = version_check.first()
                version_exists = count_row is not None and count_row[0] > 0

                if not version_exists:
                    logger.warning("alembic_version table exists but is empty")

                return bool(version_exists)
        except Exception as e:
            logger.warning(f"Failed to check schema: {e}")
            return False
        finally:
            await engine.dispose()

    async def _handle_missing_schema(self) -> None:
        """Обработка отсутствия схемы или версии."""
        env = self._config.env

        if env == EnvironmentEnum.PRODUCTION:
            error_msg = (
                "Database schema not found in production. "
                "Please run migrations manually: alembic upgrade head"
            )
            logger.error(error_msg)
            raise SchemaNotFoundError(error_msg)

        if env == EnvironmentEnum.STAGING:
            if self._config.auto_migrate:
                logger.warning("Schema not found in staging, applying migrations...")
                await self._run_migrations()
            else:
                error_msg = (
                    "Database schema not found in staging. "
                    "Set AUTO_MIGRATE=true or run: alembic upgrade head"
                )
                logger.error(error_msg)
                raise SchemaNotFoundError(error_msg)

        if env == EnvironmentEnum.DEVELOPMENT:
            if self._config.auto_migrate:
                logger.warning("Schema not found in development, applying migrations...")
                await self._run_migrations()
            else:
                error_msg = (
                    "Database schema not found in development. "
                    "Set AUTO_MIGRATE=true or run: alembic upgrade head"
                )
                logger.error(error_msg)
                raise SchemaNotFoundError(error_msg)

        if env == EnvironmentEnum.TEST:
            logger.info("Test environment: schema will be created via migrations")
            await self._run_migrations()

    async def _run_migrations(self) -> None:
        """Запуск миграций в отдельном thread."""

        def _sync_migrate() -> None:
            alembic_cfg = Config(self._config.alembic_ini_path)
            command.upgrade(alembic_cfg, "head")

        logger.info("Running Alembic migrations...")
        await to_thread(_sync_migrate)
        logger.info("Migrations applied successfully")

        # TASK-DB-008: Verify migration success
        await self._verify_migration_success()

    async def _verify_migration_success(self) -> None:
        """Verify that alembic_version has been populated after migration.
        
        TASK-DB-008: Post-migration verification.
        """
        if not self._config.main_database_url:
            return

        engine = create_async_engine(self._config.main_database_url)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM alembic_version")
                )
                row = result.first()
                count = row[0] if row else 0

                if count != 1:
                    error_msg = f"alembic_version has {count} rows after migration (expected 1)"
                    if self._config.env == EnvironmentEnum.PRODUCTION:
                        logger.error(error_msg)
                    else:
                        logger.warning(error_msg)
                else:
                    logger.info("Migration verification passed: alembic_version has 1 row")
        except Exception as e:
            logger.error(f"Failed to verify migration: {e}")
        finally:
            await engine.dispose()

    async def _populate_alembic_version(self) -> None:
        """Populate alembic_version with current HEAD version.
        
        TASK-DB-001: Fix alembic_version table - populate with current version.
        """
        import subprocess
        import os

        # Get HEAD revision from alembic
        alembic_ini = self._config.alembic_ini_path
        
        try:
            result = subprocess.run(
                ["uv", "run", "alembic", "-c", alembic_ini, "heads"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get alembic heads: {result.stderr}")
                return

            # Parse the head revision (format: "revision (head), description")
            head_line = result.stdout.strip().split("\n")[0] if result.stdout.strip() else ""
            head_revision = head_line.split(" ")[0] if head_line else ""

            if not head_revision:
                logger.error("Could not determine HEAD revision")
                return

            if not self._config.main_database_url:
                logger.error("No database URL configured, cannot populate alembic_version")
                return

            # Insert the version into the database
            engine = create_async_engine(self._config.main_database_url)
            try:
                async with engine.connect() as conn:
                    await conn.execute(
                        text("DELETE FROM alembic_version")
                    )
                    await conn.execute(
                        text("INSERT INTO alembic_version (version_num) VALUES (:rev)"),
                        {"rev": head_revision}
                    )
                    await conn.commit()
                logger.info(f"Populated alembic_version with version: {head_revision}")
            finally:
                await engine.dispose()

        except Exception as e:
            logger.error(f"Failed to populate alembic_version: {e}")

    async def cleanup_old_logs(self, retention_days: int = 30) -> int:
        """Clean up old processing_logs entries.
        
        TASK-DB-010: Implement processing_logs cleanup/retention policy.
        
        Args:
            retention_days: Number of days to retain logs (default: 30)
            
        Returns:
            Number of deleted rows
        """
        if not self._config.main_database_url:
            logger.warning("No database URL configured, skipping log cleanup")
            return 0

        engine = create_async_engine(self._config.main_database_url)
        try:
            async with engine.connect() as conn:
                # Delete old logs, but keep active ones (started/processing)
                result = await conn.execute(
                    text(
                        "DELETE FROM processing_logs "
                        "WHERE started_at < NOW() - INTERVAL ':days days' "
                        "AND status NOT IN ('started', 'processing')"
                    ),
                    {"days": retention_days}
                )
                await conn.commit()
                deleted_count = result.rowcount
                logger.info(f"Cleaned up {deleted_count} old processing logs (retention: {retention_days} days)")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0
        finally:
            await engine.dispose()

    async def recreate_test_database(self) -> None:
        """Полное пересоздание тестовой БД."""
        if not self._config.test_database_url:
            raise ValueError("TEST_DATABASE_URL not configured for test DB recreation")

        logger.info("Recreating test database...")

        # Парсинг URL для получения имени БД
        db_name = self._extract_db_name(self._config.test_database_url)
        sys_db_url = self._get_system_db_url(self._config.test_database_url)

        engine = create_async_engine(sys_db_url)
        try:
            async with engine.connect() as conn:
                # Завершаем все соединения с тестовой БД
                await conn.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) "
                        "FROM pg_stat_activity "
                        f"WHERE datname = '{db_name}'"
                    )
                )
                # DROP WITH FORCE
                await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
                # CREATE
                await conn.execute(text(f"CREATE DATABASE {db_name}"))
            logger.info(f"Test database '{db_name}' recreated")
        finally:
            await engine.dispose()

        # Применение миграций к тестовой БД
        await self._run_migrations_for_url(self._config.test_database_url)

    def _extract_db_name(self, url: str) -> str:
        """Извлечение имени БД из URL."""
        # postgresql+asyncpg://user:pass@host:port/dbname
        return url.split("/")[-1]

    def _get_system_db_url(self, url: str) -> str:
        """Получение URL для подключения к системной БД (postgres)."""
        # Заменяем имя БД на 'postgres' для системных операций
        parts = url.rsplit("/", 1)
        return parts[0] + "/postgres"

    async def _run_migrations_for_url(self, db_url: str) -> None:
        """Запуск миграций для конкретного URL."""

        def _sync_migrate() -> None:
            alembic_cfg = Config(self._config.alembic_ini_path)
            # Переопределяем URL БД для Alembic
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(alembic_cfg, "head")

        logger.info(f"Running migrations for {db_url}...")
        await to_thread(_sync_migrate)
        logger.info("Migrations applied successfully")


def main() -> None:
    """Точка входа для пересоздания тестовой БД через CLI."""
    import sys

    if "--recreate-test-db" in sys.argv:
        starter = DatabaseStarter()
        import asyncio

        asyncio.run(starter.recreate_test_database())
    else:
        print("Usage: python -m mkobi.db.starter --recreate-test-db")


if __name__ == "__main__":
    main()
