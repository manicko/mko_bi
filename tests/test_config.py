"""Tests for application configuration.

Tests:
- Loading from environment variables
- Loading from .env file
- Loading from Docker secrets (_FILE suffix)
- Loading from YAML file
- Source priority
"""

import os
import pytest

from mkobi.config import Settings
from mkobi.models.enums import EnvironmentEnum, FileExtensionEnum


class TestSettingsBase:
    """Base class for settings tests."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Clean up environment variables after each test."""
        # Save current variables
        env_backup: dict[str, str] = {}
        yield
        # Clean up test variables
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
    """Tests for loading from environment variables."""

    def test_load_database_host_from_env(self, monkeypatch):
        """Test loading DATABASE__HOST from environment variable."""
        monkeypatch.setenv("DATABASE__HOST", "env-host")
        settings = Settings()
        assert settings.database.host == "env-host"

    def test_load_jwt_secret_from_env(self, monkeypatch):
        """Test loading JWT__SECRET_KEY from environment variable."""
        monkeypatch.setenv("JWT__SECRET_KEY", "test-secret-from-env")
        settings = Settings()
        assert settings.jwt.secret_key == "test-secret-from-env"

    def test_load_upload_max_file_size_mb_from_env(self, monkeypatch):
        """Test loading UPLOAD__MAX_FILE_SIZE_MB from environment variable."""
        monkeypatch.setenv("UPLOAD__MAX_FILE_SIZE_MB", "200")
        settings = Settings()
        assert settings.upload.max_file_size_mb == 200

    def test_load_environment_enum_from_env(self, monkeypatch):
        """Test loading ENV from environment variable."""
        monkeypatch.setenv("ENV", "production")
        settings = Settings()
        assert settings.environment == EnvironmentEnum.PRODUCTION


class TestSettingsFromYaml(TestSettingsBase):
    """Tests for loading from YAML file."""

    def test_load_app_name_from_yaml(self):
        """Test loading app.name from YAML file."""
        settings = Settings()
        yaml_config = settings.load_yaml_config()
        assert "app" in yaml_config
        assert yaml_config["app"]["name"] == "mkobi"

    def test_load_app_version_from_yaml(self):
        """Test loading app.version from YAML file."""
        settings = Settings()
        yaml_config = settings.load_yaml_config()
        assert yaml_config["app"]["version"] == "1.0.0"

    def test_load_email_blocked_domains_from_yaml(self):
        """Test loading email.blocked_domains from YAML file."""
        settings = Settings()
        assert "tempmail.com" in settings.email.blocked_domains
        assert "throwaway.email" in settings.email.blocked_domains

    def test_load_dashboard_default_items_from_yaml(self):
        """Test loading dashboard.default_items_per_page from YAML file."""
        settings = Settings()
        assert settings.dashboard.default_items_per_page == 20


class TestSettingsDockerSecrets(TestSettingsBase):
    """Tests for Docker secrets support."""

    def test_docker_secret_file_loading(self, tmp_path, monkeypatch):
        """Test loading secrets from files (_FILE suffix)."""
        # Create temporary file with secret
        secret_file = tmp_path / "db_password"
        secret_file.write_text("secret-from-file")

        # Set environment variable with _FILE suffix
        monkeypatch.setenv("DATABASE__PASSWORD_FILE", str(secret_file))
        # Remove regular environment variable so secret_file takes priority
        monkeypatch.delenv("DATABASE__PASSWORD", raising=False)

        settings = Settings()
        assert settings.database.password == "secret-from-file"

    def test_docker_secret_overrides_yaml(self, tmp_path, monkeypatch):
        """Test that Docker secrets override YAML."""
        # Create temporary file with secret
        secret_file = tmp_path / "jwt_secret"
        secret_file.write_text("secret-from-file")

        # Set environment variable with _FILE suffix
        monkeypatch.setenv("JWT__SECRET_KEY_FILE", str(secret_file))
        # Remove regular environment variable so secret_file takes priority
        monkeypatch.delenv("JWT__SECRET_KEY", raising=False)

        settings = Settings()
        assert settings.jwt.secret_key == "secret-from-file"


class TestSettingsPriority(TestSettingsBase):
    """Tests for settings source priority."""

    def test_env_overrides_yaml(self, monkeypatch):
        """Test that environment variables override YAML."""
        monkeypatch.setenv("DATABASE__HOST", "env-host")
        settings = Settings()
        # YAML has localhost, but env should override
        assert settings.database.host == "env-host"

    def test_env_overrides_dotenv(self, monkeypatch):
        """Test that environment variables override .env file."""
        # Create temporary .env file
        monkeypatch.setenv("DATABASE__HOST", "env-host")
        settings = Settings()
        assert settings.database.host == "env-host"

    def test_priority_order(self, tmp_path, monkeypatch):
        """Test correct priority order.

        Priority: env vars > Docker secrets > .env > YAML > defaults
        """
        # Create file with secret
        secret_file = tmp_path / "secret"
        secret_file.write_text("secret-value")

        # Set variables
        monkeypatch.setenv("JWT__SECRET_KEY_FILE", str(secret_file))

        settings = Settings()
        # Docker secret should be loaded
        assert settings.jwt.secret_key == "secret-value"


class TestSettingsProperties(TestSettingsBase):
    """Tests for Settings properties and methods."""

    def test_database_url_property(self):
        """Test DATABASE_URL property."""
        settings = Settings()
        url = settings.DATABASE_URL
        assert "postgresql" in url or "postgresql+asyncpg" in url

    def test_allowed_file_types_property(self):
        """Test allowed_file_types property."""
        settings = Settings()
        extensions = settings.allowed_file_types
        assert "csv" in extensions
        assert "csv.gz" in extensions

    def test_allowed_mime_types_property(self):
        """Test allowed_mime_types property."""
        settings = Settings()
        mime_types = settings.allowed_mime_types
        assert "text/csv" in mime_types

    def test_max_file_size_property(self):
        """Test max_file_size property (in bytes)."""
        settings = Settings()
        # 100 MB = 100 * 1024 * 1024 bytes
        assert settings.max_file_size == 100 * 1024 * 1024

    def test_log_level_property(self):
        """Test log_level property."""
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_load_yaml_config_method(self):
        """Test load_yaml_config() method."""
        settings = Settings()
        config = settings.load_yaml_config()
        assert isinstance(config, dict)
        assert "app" in config


class TestAppSettings(TestSettingsBase):
    """Tests for AppSettings."""

    def test_app_settings_defaults(self):
        """Test default values for AppSettings."""
        settings = Settings()
        assert settings.app.name == "mkobi"
        assert settings.app.version == "1.0.0"


class TestUploadSettings(TestSettingsBase):
    """Tests for UploadSettings."""

    def test_upload_settings_defaults(self):
        """Test default values for UploadSettings."""
        settings = Settings()
        assert settings.upload.max_file_size_mb == 100
        assert settings.upload.temp_dir_prefix == "mkobi_upload"
        assert FileExtensionEnum.CSV in settings.upload.allowed_extensions


class TestEmailSettings(TestSettingsBase):
    """Tests for EmailSettings."""

    def test_email_blocked_domains(self):
        """Test blocked domains."""
        settings = Settings()
        assert "tempmail.com" in settings.email.blocked_domains
        assert "throwaway.email" in settings.email.blocked_domains


class TestDashboardSettings(TestSettingsBase):
    """Tests for DashboardSettings."""

    def test_dashboard_default_items(self):
        """Test default items per page."""
        settings = Settings()
        assert settings.dashboard.default_items_per_page == 20


class TestCORSOrigins(TestSettingsBase):
    """Tests for CORS origins configuration."""

    def test_cors_origins_default_from_yaml(self):
        """Test that CORS origins are loaded from YAML config."""
        settings = Settings()
        # Default from app.yaml
        assert "https://example.com" in settings.cors_origins
        assert "https://app.example.com" in settings.cors_origins

    def test_cors_origins_from_env_json(self, monkeypatch):
        """Test CORS origins parsing from JSON string in env var."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')
        settings = Settings()
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_from_env_multiple(self, monkeypatch):
        """Test CORS origins parsing from JSON array in env var."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000", "https://app.example.com"]')
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "https://app.example.com" in settings.cors_origins

    def test_cors_origins_from_env_comma_separated(self, monkeypatch):
        """Test CORS origins parsing from comma-separated string."""
        # CORS_ORIGINS expects JSON format, not comma-separated
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000", "http://example.com"]')
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://example.com" in settings.cors_origins

    def test_cors_origins_from_env_single(self, monkeypatch):
        """Test CORS origins parsing from single string."""
        # CORS_ORIGINS expects JSON format
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')
        settings = Settings()
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_env_overrides_yaml(self, monkeypatch):
        """Test that env var overrides YAML config."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://from-env:3000"]')
        settings = Settings()
        assert settings.cors_origins == ["http://from-env:3000"]
        assert "https://example.com" not in settings.cors_origins
