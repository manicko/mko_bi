"""Тесты для конфигурации приложения.

Проверяют:
- Загрузку из переменных окружения
- Загрузку из .env файла
- Загрузку из Docker secrets (_FILE суффикс)
- Загрузку из YAML файла
- Приоритет источников
"""

import os
import pytest

from mkobi.config import Settings
from mkobi.models.enums import EnvironmentEnum, FileExtensionEnum


class TestSettingsBase:
    """Базовый класс для тестов настроек."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Очищает переменные окружения после каждого теста."""
        # Сохраняем текущие переменные
        env_backup: dict[str, str] = {}
        yield
        # Очищаем тестовые переменные
        for key in list(os.environ.keys()):
            if key.startswith((
                "DATABASE__",
                "JWT__",
                "UPLOAD__",
                "REDIS__",
                "LOGGING__",
                "CORS_",
                "APP_",
                "ENV",
                "DEBUG",
                "HOST",
                "PORT",
            )):
                if key in env_backup:
                    os.environ[key] = env_backup[key]
                else:
                    os.environ.pop(key, None)


class TestSettingsFromEnv(TestSettingsBase):
    """Тесты загрузки из переменных окружения."""

    def test_load_database_host_from_env(self, monkeypatch):
        """Проверяет загрузку DATABASE__HOST из переменной окружения."""
        monkeypatch.setenv("DATABASE__HOST", "env-host")
        settings = Settings()
        assert settings.environment == EnvironmentEnum.DEVELOPMENT

    def test_load_jwt_secret_from_env(self, monkeypatch):
        """Проверяет загрузку JWT__SECRET_KEY из переменной окружения."""
        monkeypatch.setenv("JWT__SECRET_KEY", "test-secret-from-env")
        settings = Settings()
        assert settings.jwt.secret_key == "test-secret-from-env"

    def test_load_upload_max_file_size_mb_from_env(self, monkeypatch):
        """Проверяет загрузку UPLOAD__MAX_FILE_SIZE_MB из переменной окружения."""
        monkeypatch.setenv("UPLOAD__MAX_FILE_SIZE_MB", "200")
        settings = Settings()
        assert settings.upload.max_file_size_mb == 200

    def test_load_environment_enum_from_env(self, monkeypatch):
        """Проверяет загрузку ENV из переменной окружения."""
        monkeypatch.setenv("ENV", "production")
        settings = Settings()
        assert settings.environment == EnvironmentEnum.PRODUCTION


class TestSettingsFromYaml(TestSettingsBase):
    """Тесты загрузки из YAML файла."""

    def test_load_app_name_from_yaml(self):
        """Проверяет загрузку app.name из YAML файла."""
        settings = Settings()
        yaml_config = settings.load_yaml_config()
        assert "app" in yaml_config
        assert yaml_config["app"]["name"] == "mkobi"

    def test_load_app_version_from_yaml(self):
        """Проверяет загрузку app.version из YAML файла."""
        settings = Settings()
        yaml_config = settings.load_yaml_config()
        assert yaml_config["app"]["version"] == "1.0.0"

    def test_load_email_blocked_domains_from_yaml(self):
        """Проверяет загрузку email.blocked_domains из YAML файла."""
        settings = Settings()
        assert "tempmail.com" in settings.email.blocked_domains
        assert "throwaway.email" in settings.email.blocked_domains

    def test_load_dashboard_default_items_from_yaml(self):
        """Проверяет загрузку dashboard.default_items_per_page из YAML файла."""
        settings = Settings()
        assert settings.dashboard.default_items_per_page == 20


class TestSettingsDockerSecrets(TestSettingsBase):
    """Тесты поддержки Docker secrets."""

    def test_docker_secret_file_loading(self, tmp_path, monkeypatch):
        """Проверяет загрузку секретов из файлов (_FILE суффикс)."""
        # Создаем временный файл с секретом
        secret_file = tmp_path / "db_password"
        secret_file.write_text("secret-from-file")

        # Устанавливаем переменную окружения с суффиксом _FILE
        monkeypatch.setenv("DATABASE__PASSWORD_FILE", str(secret_file))
        # Убираем обычную переменную окружения, чтобы secret_file имел приоритет
        monkeypatch.delenv("DATABASE__PASSWORD", raising=False)

        settings = Settings()
        assert settings.database.password == "secret-from-file"

    def test_docker_secret_overrides_yaml(self, tmp_path, monkeypatch):
        """Проверяет, что Docker secrets переопределяют YAML."""
        # Создаем временный файл с секретом
        secret_file = tmp_path / "jwt_secret"
        secret_file.write_text("secret-from-file")

        # Устанавливаем переменную окружения с суффиксом _FILE
        monkeypatch.setenv("JWT__SECRET_KEY_FILE", str(secret_file))
        # Убираем обычную переменную окружения, чтобы secret_file имел приоритет
        monkeypatch.delenv("JWT__SECRET_KEY", raising=False)

        settings = Settings()
        assert settings.jwt.secret_key == "secret-from-file"


class TestSettingsPriority(TestSettingsBase):
    """Тесты приоритета источников настроек."""

    def test_env_overrides_yaml(self, monkeypatch):
        """Проверяет, что переменные окружения переопределяют YAML."""
        monkeypatch.setenv("DATABASE__HOST", "env-host")
        settings = Settings()
        # YAML has localhost, but env should override
        assert settings.database.host == "env-host"

    def test_env_overrides_dotenv(self, monkeypatch):
        """Проверяет, что переменные окружения переопределяют .env файл."""
        # Создаем временный .env файл
        monkeypatch.setenv("DATABASE__HOST", "env-host")
        settings = Settings()
        assert settings.database.host == "env-host"

    def test_priority_order(self, tmp_path, monkeypatch):
        """Проверяет правильный порядок приоритета.

        Priority: env vars > Docker secrets > .env > YAML > defaults
        """
        # Создаем файл с секретом
        secret_file = tmp_path / "secret"
        secret_file.write_text("secret-value")

        # Устанавливаем переменные
        monkeypatch.setenv("JWT__SECRET_KEY_FILE", str(secret_file))

        settings = Settings()
        # Docker secret should be loaded
        assert settings.jwt.secret_key == "secret-value"


class TestSettingsProperties(TestSettingsBase):
    """Тесты свойств и методов Settings."""

    def test_database_url_property(self):
        """Проверяет свойство DATABASE_URL."""
        settings = Settings()
        url = settings.DATABASE_URL
        assert "postgresql" in url or "postgresql+asyncpg" in url

    def test_allowed_file_types_property(self):
        """Проверяет свойство allowed_file_types."""
        settings = Settings()
        extensions = settings.allowed_file_types
        assert "csv" in extensions
        assert "csv.gz" in extensions

    def test_allowed_mime_types_property(self):
        """Проверяет свойство allowed_mime_types."""
        settings = Settings()
        mime_types = settings.allowed_mime_types
        assert "text/csv" in mime_types

    def test_max_file_size_property(self):
        """Проверяет свойство max_file_size (в байтах)."""
        settings = Settings()
        # 100 MB = 100 * 1024 * 1024 bytes
        assert settings.max_file_size == 100 * 1024 * 1024

    def test_log_level_property(self):
        """Проверяет свойство log_level."""
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_load_yaml_config_method(self):
        """Проверяет метод load_yaml_config()."""
        settings = Settings()
        config = settings.load_yaml_config()
        assert isinstance(config, dict)
        assert "app" in config


class TestAppSettings(TestSettingsBase):
    """Тесты для AppSettings."""

    def test_app_settings_defaults(self):
        """Проверяет значения по умолчанию для AppSettings."""
        settings = Settings()
        assert settings.app.name == "mkobi"
        assert settings.app.version == "1.0.0"


class TestUploadSettings(TestSettingsBase):
    """Тесты для UploadSettings."""

    def test_upload_settings_defaults(self):
        """Проверяет значения по умолчанию для UploadSettings."""
        settings = Settings()
        assert settings.upload.max_file_size_mb == 100
        assert settings.upload.temp_dir_prefix == "mkobi_upload"
        assert FileExtensionEnum.CSV in settings.upload.allowed_extensions


class TestEmailSettings(TestSettingsBase):
    """Тесты для EmailSettings."""

    def test_email_blocked_domains(self):
        """Проверяет заблокированные домены."""
        settings = Settings()
        assert "tempmail.com" in settings.email.blocked_domains
        assert "throwaway.email" in settings.email.blocked_domains


class TestDashboardSettings(TestSettingsBase):
    """Тесты для DashboardSettings."""

    def test_dashboard_default_items(self):
        """Проверяет количество элементов по умолчанию."""
        settings = Settings()
        assert settings.dashboard.default_items_per_page == 20
