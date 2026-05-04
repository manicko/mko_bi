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

from mko_bi.config import get_config
from mko_bi.models.user_roles import EnvironmentEnum

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
    ) -> None:
        self.env = env
        self.main_database_url = main_database_url
        self.test_database_url = test_database_url
        self.auto_migrate = auto_migrate
        self.migration_script_path = migration_script_path
        self.alembic_ini_path = alembic_ini_path
        self.recreate_test_db = recreate_test_db


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

        return DatabaseStarterConfig(
            env=env,
            main_database_url=main_db_url,
            test_database_url=test_db_url,
            auto_migrate=auto_migrate,
            migration_script_path=migration_script_path,
            alembic_ini_path=alembic_ini_path,
            recreate_test_db=recreate_test_db,
        )

    async def startup(self) -> None:
        """Действия при старте приложения."""
        logger.info(f"Starting database initialization for ENV={self._config.env}")

        if self._config.env == EnvironmentEnum.TEST and self._config.recreate_test_db:
            await self.recreate_test_database()

        # 1. Проверка существования БД
        await self._check_database_exists()

        # 2. Проверка схемы
        schema_exists = await self._check_schema_exists()

        # 3. Применение миграций (если нужно)
        if not schema_exists:
            await self._handle_missing_schema()

        logger.info("Database initialization completed")

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
        """Проверка наличия таблицы alembic_version."""
        if not self._config.main_database_url:
            return False

        engine = create_async_engine(self._config.main_database_url)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_name = 'alembic_version'"
                        ")"
                    )
                )
                row = result.first()
                schema_exists = row is not None and row[0]
            logger.info(f"Schema exists: {schema_exists}")
            return bool(schema_exists)
        except Exception as e:
            logger.warning(f"Failed to check schema: {e}")
            return False
        finally:
            await engine.dispose()

    async def _handle_missing_schema(self) -> None:
        """Обработка отсутствия схемы."""
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
        print("Usage: python -m mko_bi.db.starter --recreate-test-db")


if __name__ == "__main__":
    main()
