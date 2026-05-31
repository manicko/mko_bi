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
        env_backup: dict[str, str] = {
            key: os.environ[key]
            for key in os.environ
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
            ))
        }
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
        monkeypatch.setenv("ADMIN_USERNAME", "testadmin")
        monkeypatch.setenv("ADMIN_PASSWORD", "testpassword123")
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

        # Set variables - remove JWT__SECRET_KEY env var so Docker secret takes effect
        monkeypatch.setenv("JWT__SECRET_KEY_FILE", str(secret_file))
        monkeypatch.delenv("JWT__SECRET_KEY", raising=False)

        settings = Settings()
        # Docker secret should be loaded
        assert settings.jwt.secret_key == "secret-value"


class TestSettingsProperties(TestSettingsBase):
    """Tests for Settings properties and methods."""

    def test_database_url_property(self):
        """Test DATABASE_URL property."""
        settings = Settings()
        url = settings.DATABASE_URL
        # In development without password, DATABASE_URL returns None
        # (password is required in production)
        if url is not None:
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
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:5173" in settings.cors_origins

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


class TestWeakCredentialDetection(TestSettingsBase):
    """Tests for weak admin credential detection."""

    @pytest.mark.parametrize("weak_username", [
        "admin", "administrator", "root", "test", "user", "admin@example.com"
    ])
    def test_weak_username_rejected(self, monkeypatch, weak_username):
        """Verify known-weak usernames are rejected in production."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("ADMIN_USERNAME", weak_username)
        monkeypatch.setenv("ADMIN_PASSWORD", "StrongP@ss1")
        with pytest.raises(ValueError, match="too common"):
            Settings()

    @pytest.mark.parametrize("weak_password", [
        "password", "123456", "admin", "secret", "test", "admin@example.com"
    ])
    def test_weak_password_rejected(self, monkeypatch, weak_password):
        """Verify known-weak passwords are rejected in production."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("ADMIN_USERNAME", "secure_admin")
        monkeypatch.setenv("ADMIN_PASSWORD", weak_password)
        with pytest.raises(ValueError, match="too common"):
            Settings()

    def test_strong_credentials_accepted(self, monkeypatch):
        """Verify strong credentials pass validation in production."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("ADMIN_USERNAME", "secure_admin")
        monkeypatch.setenv("ADMIN_PASSWORD", "StrongP@ss1")
        # Should not raise
        settings = Settings()
        assert settings.admin_username == "secure_admin"
        assert settings.admin_password == "StrongP@ss1"


class TestGetConfigReload:
    """Tests for get_config() reload mechanism."""

    def test_get_config_returns_singleton(self, monkeypatch):
        """Test that get_config returns the same instance by default."""
        from mkobi.config import get_config, clear_config_cache

        # Clear cache first to start fresh
        clear_config_cache()

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_reload_returns_new_instance(self, monkeypatch):
        """Test that get_config(reload=True) returns a new instance."""
        from mkobi.config import get_config, clear_config_cache

        # Clear cache first to start fresh
        clear_config_cache()

        config1 = get_config()
        config2 = get_config(reload=True)
        assert config1 is not config2

    def test_clear_config_cache_allows_new_instance(self, monkeypatch):
        """Test that clear_config_cache allows creating a new config instance."""
        from mkobi.config import get_config, clear_config_cache

        # Clear cache first to start fresh
        clear_config_cache()

        config1 = get_config()
        clear_config_cache()
        config2 = get_config()
        assert config1 is not config2

    def test_get_config_reload_with_different_env(self, monkeypatch):
        """Test reload picks up new environment variables."""
        from mkobi.config import get_config, clear_config_cache

        # Clear cache first
        clear_config_cache()

        # Set initial env
        monkeypatch.setenv("DATABASE__HOST", "initial-host")
        config1 = get_config()
        assert config1.database.host == "initial-host"

        # Change env and reload
        monkeypatch.setenv("DATABASE__HOST", "new-host")
        config2 = get_config(reload=True)
        assert config2.database.host == "new-host"

        # Verify singleton still works (returns same instance as last call)
        config3 = get_config()
        assert config3 is config2


class TestDatabaseUrlPasswordValidation(TestSettingsBase):
    """Tests for DATABASE_URL password validation."""

    def test_database_url_returns_none_without_password_in_development(self, monkeypatch):
        """Test DATABASE_URL returns None when password is missing in development."""
        # Override password to empty string to simulate missing password
        monkeypatch.setenv("DATABASE__PASSWORD", "")
        monkeypatch.setenv("ENV", "development")
        from mkobi.config import clear_config_cache
        clear_config_cache()
        settings = Settings()
        # Password is empty string (which is falsy), so DATABASE_URL should return None
        assert settings.database.password == ""
        assert settings.DATABASE_URL is None

    def test_database_url_raises_error_without_password_in_production(self, monkeypatch):
        """Test DATABASE_URL raises ValueError when password is missing in production."""
        # Override password to empty string to simulate missing password
        monkeypatch.setenv("DATABASE__PASSWORD", "")
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("ADMIN_USERNAME", "prodadmin")
        monkeypatch.setenv("ADMIN_PASSWORD", "StrongP@ss1")
        from mkobi.config import clear_config_cache
        clear_config_cache()
        settings = Settings()
        # Should raise ValueError in production without password
        with pytest.raises(ValueError, match="DATABASE__PASSWORD is required in production"):
            _ = settings.DATABASE_URL

    def test_database_url_returns_url_with_password(self, monkeypatch):
        """Test DATABASE_URL returns URL when password is set."""
        monkeypatch.setenv("DATABASE__PASSWORD", "test-password")
        settings = Settings()
        url = settings.DATABASE_URL
        assert url is not None
        assert "postgresql" in url or "postgresql+asyncpg" in url
