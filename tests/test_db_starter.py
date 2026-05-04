"""Тесты для модуля воспроизведения структуры БД."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from mko_bi.db.starter import (
    DatabaseStarter,
    DatabaseStarterConfig,
    DatabaseNotFoundError,
    SchemaNotFoundError,
)
from mko_bi.models.user_roles import EnvironmentEnum


@pytest.fixture
def starter_config():
    """Фикстура с базовой конфигурацией."""
    return DatabaseStarterConfig(
        env=EnvironmentEnum.DEVELOPMENT,
        main_database_url="postgresql+asyncpg://test:test@localhost:5432/testdb",
        test_database_url="postgresql+asyncpg://test:test@localhost:5432/testdb_test",
        auto_migrate=True,
    )


@pytest.fixture
def starter():
    """Фикстура с DatabaseStarter."""
    with patch.dict(
        os.environ,
        {
            "ENV": "development",
            "MAIN_DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/testdb",
            "AUTO_MIGRATE": "true",
        },
        clear=False,
    ):
        return DatabaseStarter()


class TestDatabaseStarterConfig:
    """Тесты конфигурации."""

    def test_default_config(self):
        """Тест конфигурации по умолчанию."""
        config = DatabaseStarterConfig()
        assert config.env == EnvironmentEnum.DEVELOPMENT
        assert config.main_database_url is None
        assert config.auto_migrate is False

    def test_custom_config(self):
        """Тест пользовательской конфигурации."""
        config = DatabaseStarterConfig(
            env=EnvironmentEnum.PRODUCTION,
            main_database_url="postgresql+asyncpg://user:pass@localhost:5432/proddb",
            auto_migrate=False,
        )
        assert config.env == EnvironmentEnum.PRODUCTION
        assert config.auto_migrate is False


class TestDatabaseStarterLoadConfig:
    """Тесты загрузки конфигурации из переменных окружения."""

    def test_load_from_env_development(self, monkeypatch):
        """Тест загрузки окружения development."""
        monkeypatch.setenv("ENV", "development")
        monkeypatch.setenv("MAIN_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
        starter = DatabaseStarter()
        assert starter._config.env == EnvironmentEnum.DEVELOPMENT
        assert starter._config.auto_migrate is True  # auto for dev

    def test_load_from_env_production(self, monkeypatch):
        """Тест загрузки окружения production."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("MAIN_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/proddb")
        starter = DatabaseStarter()
        assert starter._config.env == EnvironmentEnum.PRODUCTION
        assert starter._config.auto_migrate is False  # no auto for prod

    def test_load_from_env_test(self, monkeypatch):
        """Тест загрузки окружения test."""
        monkeypatch.setenv("ENV", "test")
        monkeypatch.setenv("MAIN_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
        monkeypatch.setenv("TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb_test")
        starter = DatabaseStarter()
        assert starter._config.env == EnvironmentEnum.TEST
        assert starter._config.auto_migrate is True  # auto for test

    def test_load_unknown_env(self, monkeypatch):
        """Тест загрузки неизвестного окружения."""
        monkeypatch.setenv("ENV", "unknown")
        starter = DatabaseStarter()
        assert starter._config.env == EnvironmentEnum.DEVELOPMENT  # default


class TestDatabaseStarterCheckDatabase:
    """Тесты проверки существования БД."""

    @patch("mko_bi.db.starter.create_async_engine")
    async def test_database_exists(self, mock_create_engine, starter):
        """Тест успешного подключения к БД."""
        mock_engine = AsyncMock(spec=AsyncEngine)
        # Настраиваем контекстный менеджер для connect()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        mock_engine.connect.return_value.__aexit__.return_value = False
        mock_create_engine.return_value = mock_engine

        await starter._check_database_exists()
        mock_conn.execute.assert_called_once()

    @patch("mko_bi.db.starter.create_async_engine")
    async def test_database_not_exists(self, mock_create_engine, starter):
        """Тест отсутствия БД."""
        mock_engine = AsyncMock(spec=AsyncEngine)
        # Настраиваем контекстный менеджер для connect() с ошибкой
        mock_engine.connect.return_value.__aenter__.side_effect = Exception("Connection failed")
        mock_create_engine.return_value = mock_engine

        with pytest.raises(DatabaseNotFoundError):
            await starter._check_database_exists()


class TestDatabaseStarterCheckSchema:
    """Тесты проверки схемы."""

    @patch("mko_bi.db.starter.create_async_engine")
    async def test_schema_exists(self, mock_create_engine, starter):
        """Тест наличия схемы (таблица alembic_version найдена)."""
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=(True,))
        mock_conn.execute = AsyncMock(return_value=mock_result)
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        mock_engine.connect.return_value.__aexit__.return_value = False
        mock_create_engine.return_value = mock_engine

        result = await starter._check_schema_exists()
        assert result is True

    @patch("mko_bi.db.starter.create_async_engine")
    async def test_schema_not_exists(self, mock_create_engine, starter):
        """Тест отсутствия схемы (таблица alembic_version не найдена)."""
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=(False,))
        mock_conn.execute = AsyncMock(return_value=mock_result)
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        mock_engine.connect.return_value.__aexit__.return_value = False
        mock_create_engine.return_value = mock_engine

        result = await starter._check_schema_exists()
        assert result is False


class TestDatabaseStarterHandleMissingSchema:
    """Тесты обработки отсутствия схемы."""

    async def test_production_raises_error(self):
        """В production без схемы поднимается ошибка."""
        config = DatabaseStarterConfig(
            env=EnvironmentEnum.PRODUCTION,
            main_database_url="postgresql+asyncpg://test:test@localhost:5432/proddb",
        )
        starter = DatabaseStarter()
        starter._config = config

        with pytest.raises(SchemaNotFoundError) as exc_info:
            await starter._handle_missing_schema()
        assert "alembic upgrade head" in str(exc_info.value)

    @patch("mko_bi.db.starter.DatabaseStarter._run_migrations")
    async def test_development_with_auto_migrate(self, mock_run_migrations):
        """В development с AUTO_MIGRATE=true применяются миграции."""
        config = DatabaseStarterConfig(
            env=EnvironmentEnum.DEVELOPMENT,
            main_database_url="postgresql+asyncpg://test:test@localhost:5432/devdb",
            auto_migrate=True,
        )
        starter = DatabaseStarter()
        starter._config = config

        await starter._handle_missing_schema()
        mock_run_migrations.assert_called_once()

    async def test_development_without_auto_migrate_raises_error(self):
        """В development без AUTO_MIGRATE поднимается ошибка."""
        config = DatabaseStarterConfig(
            env=EnvironmentEnum.DEVELOPMENT,
            main_database_url="postgresql+asyncpg://test:test@localhost:5432/devdb",
            auto_migrate=False,
        )
        starter = DatabaseStarter()
        starter._config = config

        with pytest.raises(SchemaNotFoundError):
            await starter._handle_missing_schema()


class TestDatabaseStarterRunMigrations:
    """Тесты запуска миграций."""

    @patch("mko_bi.db.starter.to_thread")
    async def test_run_migrations_calls_to_thread(self, mock_to_thread):
        """Тест что миграции запускаются через to_thread."""
        starter = DatabaseStarter()
        await starter._run_migrations()
        mock_to_thread.assert_called_once()


class TestDatabaseStarterUtilityMethods:
    """Тесты вспомогательных методов."""

    def test_extract_db_name(self, starter):
        """Тест извлечения имени БД из URL."""
        url = "postgresql+asyncpg://user:pass@localhost:5432/mydb"
        result = starter._extract_db_name(url)
        assert result == "mydb"

    def test_get_system_db_url(self, starter):
        """Тест получения URL системной БД."""
        url = "postgresql+asyncpg://user:pass@localhost:5432/mydb"
        result = starter._get_system_db_url(url)
        assert result == "postgresql+asyncpg://user:pass@localhost:5432/postgres"


class TestDatabaseStarterIntegration:
    """Integration tests (require real DB)."""
    pass
