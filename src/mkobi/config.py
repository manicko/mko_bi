import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, PostgresDsn, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, YamlConfigSettingsSource
from pydantic_settings.sources import PydanticBaseSettingsSource

from mkobi.models.enums import EnvironmentEnum, FileExtensionEnum, MimeTypeEnum

logger = logging.getLogger(__name__)


def _set_nested_value(data: dict[str, Any], key: str, value: Any) -> None:
    """Set a nested value in a dict using __ as separator.

    Example: _set_nested_value({}, "DATABASE__PASSWORD", "secret")
             -> {"database": {"password": "secret"}}
    """
    parts = key.lower().split("__")
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


class SecretsFileSource(PydanticBaseSettingsSource):
    """Custom settings source for reading Docker secrets from files.

    Supports environment variables like DATABASE__PASSWORD_FILE that point to
    files containing the actual secret values (Docker secrets pattern).
    """

    def get_field_value(self, field_info: FieldInfo, field_name: str) -> Any:
        """Read secret from file for a specific field."""
        return None  # Not used - we override __call__ instead

    def __call__(self) -> dict[str, Any]:
        """Read secrets from file-based environment variables."""
        result: dict[str, Any] = {}

        # Look for environment variables ending with _FILE
        for env_var_name in list(os.environ.keys()):
            if env_var_name.endswith("_FILE"):
                # Get the base env var name (without _FILE suffix)
                base_env_var = env_var_name[:-5]  # Remove "_FILE"
                file_path_str = os.environ[env_var_name]
                file_path = Path(file_path_str)

                if file_path.exists():
                    try:
                        secret_value = file_path.read_text().strip()
                        # Convert DATABASE__PASSWORD to nested dict structure
                        _set_nested_value(result, base_env_var, secret_value)
                        logger.debug(
                            f"Loaded secret for {base_env_var} from {file_path}"
                        )
                    except OSError as e:
                        logger.warning(f"Failed to read secret file {file_path}: {e}")

        return result

    def __repr__(self) -> str:
        return "SecretsFileSource()"


class DatabaseSettings(BaseModel):
    """Database connection settings."""

    host: str = "localhost"
    port: int = 5432
    dbname: str = "bidb"
    user: str = "postgres"
    password: str | None = None
    test_dbname: str = "bidb_test"

    @property
    def database_url(self) -> PostgresDsn:
        """Build PostgreSQL connection URL using asyncpg."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.dbname,
        )


class JWTSettings(BaseModel):
    """JWT authentication settings."""

    secret_key: str | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class RedisSettings(BaseModel):
    """Redis settings."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None


class AppSettings(BaseModel):
    """Application settings."""

    name: str = "mkobi"
    version: str = "1.0.0"


class UploadSettings(BaseModel):
    """File upload settings."""

    temp_dir: str = "data/tmp_uploads"
    temp_dir_prefix: str = "mkobi_upload"
    max_file_size_mb: int = Field(default=100, alias="max_file_size_mb")
    allowed_extensions: list[FileExtensionEnum] = [
        FileExtensionEnum.CSV_GZ,
        FileExtensionEnum.CSV,
    ]
    allowed_mime_types: list[MimeTypeEnum] = [
        MimeTypeEnum.TEXT_CSV,
        MimeTypeEnum.APPLICATION_GZIP,
    ]
    lazy_threshold_mb: float = 10.0

    model_config = {"populate_by_name": True}


class EmailSettings(BaseModel):
    """Email settings."""

    blocked_domains: list[str] = ["tempmail.com", "throwaway.email"]


class DashboardSettings(BaseModel):
    """Dashboard settings."""

    default_items_per_page: int = 20


class LoggingSettings(BaseModel):
    """Logging settings."""

    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level: str = "INFO"
    log_file: str | None = None
    json_logging: bool = True


class ChartsSettings(BaseModel):
    """Chart settings."""

    default_colors: list[str] = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
    ]

    class YOYSettings(BaseModel):
        """Year-over-year comparison settings."""

        class CurrentYearStyle(BaseModel):
            line: dict[str, Any] = {"dash": "solid", "width": 3}

        class PreviousYearStyle(BaseModel):
            line: dict[str, Any] = {"dash": "dash", "width": 2}

        current_year_style: CurrentYearStyle = CurrentYearStyle()
        previous_year_style: PreviousYearStyle = PreviousYearStyle()

    yoy: YOYSettings = YOYSettings()

    class LayoutSettings(BaseModel):
        template: str = "plotly_white"
        margin: dict[str, int] = {"l": 50, "r": 50, "t": 50, "b": 50}

    layout: LayoutSettings = LayoutSettings()


class Settings(BaseSettings):
    """Application configuration using pydantic-settings.

    All settings are loaded from environment variables, .env file,
    Docker secrets and YAML file with proper priority.
    """

    # --- App ---
    app_name: str = "mkobi"
    environment: EnvironmentEnum = Field(
        default=EnvironmentEnum.DEVELOPMENT, alias="ENV"
    )
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    app: AppSettings = AppSettings()
    email: EmailSettings = EmailSettings()
    dashboard: DashboardSettings = DashboardSettings()

    # --- Database ---
    database: DatabaseSettings = DatabaseSettings()

    # --- JWT ---
    jwt: JWTSettings = JWTSettings()

    # --- Upload ---
    upload: UploadSettings = UploadSettings()

    # --- Redis ---
    redis: RedisSettings = RedisSettings()

    # --- Logging ---
    logging: LoggingSettings = LoggingSettings()

    # --- Charts ---
    charts: ChartsSettings = ChartsSettings()

    # --- CORS ---
    cors_origins: list[str] = []

    # --- Admin ---
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")

    # --- Cleanup Settings ---
    stale_file_threshold_hours: int = Field(default=24, alias="STALE_FILE_THRESHOLD_HOURS")

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        """Validate CORS origins.

        Args:
            value: List of CORS origins (already parsed by pydantic-settings).

        Returns:
            list[str]: Validated list of CORS origins.
        """
        if not isinstance(value, list):
            return []
        return [str(origin) for origin in value]

    # --- Database Migrations ---
    auto_migrate: bool = False
    migration_script_path: str = "alembic"
    alembic_ini_path: str = "alembic.ini"
    recreate_test_db: bool = False

    model_config = {
        "env_prefix": "",
        "env_nested_delimiter": "__",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources with correct priority order.

        Priority (highest to lowest):
        1. Environment variables (DATABASE__PASSWORD, JWT__SECRET_KEY, etc.)
        2. Docker secrets files (DATABASE__PASSWORD_FILE -> /run/secrets/db_password)
        3. .env file (for development convenience)
        4. YAML config file (app.yaml)
        5. Default values from code

        Note: In pydantic-settings 2.x, the FIRST source in tuple has HIGHEST priority.
        """
        yaml_file_path = Path(__file__).parent / "settings" / "app.yaml"
        yaml_source = YamlConfigSettingsSource(
            settings_cls,
            yaml_file=yaml_file_path,
        )
        secrets_source = SecretsFileSource(settings_cls)
        # First source has highest priority
        return (
            env_settings,
            secrets_source,
            dotenv_settings,
            yaml_source,
            init_settings,
        )

    def __init__(self, **data: Any) -> None:
        """Initialize configuration and log settings (without secrets)."""
        super().__init__(**data)
        self._log_initialization()
        self._ensure_upload_dir()

    def _log_initialization(self) -> None:
        """Log configuration initialization without exposing secrets."""
        logger.info(
            "Configuration loaded: env=%s, database_host=%s, redis_host=%s",
            self.environment,
            self.database.host,
            self.redis.host,
        )
        if self.debug:
            logger.debug("Debug mode is enabled")

    def _ensure_upload_dir(self) -> None:
        """Create directory for temporary upload files if it doesn't exist."""
        upload_path = Path(self.upload.temp_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

    @property
    def DATABASE_URL(self) -> str:
        """Build PostgreSQL connection URL."""
        return str(self.database.database_url)

    @property
    def TEST_DATABASE_URL(self) -> str | None:
        """Construct test database URL from database settings with test dbname."""
        if not self.database.password:
            return None
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.database.user,
                password=self.database.password,
                host=self.database.host,
                port=self.database.port,
                path=self.database.test_dbname,
            )
        )

    @property
    def test_database_url(self) -> str | None:
        """Alias for TEST_DATABASE_URL."""
        return self.TEST_DATABASE_URL

    @property
    def jwt_secret_key(self) -> str | None:
        """Alias for JWT_SECRET_KEY."""
        return self.jwt.secret_key

    @property
    def jwt_algorithm(self) -> str:
        """Alias for JWT_ALGORITHM."""
        return self.jwt.algorithm

    @property
    def upload_temp_dir(self) -> str:
        """Alias for UPLOAD_TEMP_DIR."""
        return self.upload.temp_dir

    @property
    def allowed_file_types(self) -> list[str]:
        """Return list of allowed file extensions."""
        return [ext.value for ext in self.upload.allowed_extensions]

    @property
    def allowed_mime_types(self) -> list[str]:
        """Return list of allowed MIME types."""
        return [mime.value for mime in self.upload.allowed_mime_types]

    @property
    def lazy_threshold_mb(self) -> float:
        """Threshold in MB for using lazy evaluation."""
        return self.upload.lazy_threshold_mb

    @property
    def max_file_size(self) -> int:
        """Return maximum file size in bytes."""
        return self.upload.max_file_size_mb * 1024 * 1024

    @property
    def log_level(self) -> str:
        """Alias for logging level."""
        return self.logging.level

    @property
    def log_file(self) -> str | None:
        """Alias for logging file."""
        return self.logging.log_file

    @property
    def admin_user(self) -> str:
        """Return admin username."""
        return self.admin_username

    @property
    def admin_pass(self) -> str:
        """Return admin password."""
        return self.admin_password

    def load_yaml_config(self) -> dict[str, Any]:
        """Load and return configuration from app.yaml.

        Returns:
            dict[str, Any]: Dictionary with settings from YAML file.
        """
        yaml_file_path = Path(__file__).parent / "settings" / "app.yaml"
        if yaml_file_path.exists():
            with open(yaml_file_path) as f:
                result: Any = yaml.safe_load(f)
                return result if isinstance(result, dict) else {}
        return {}


# Cached configuration instance
_settings: Settings | None = None


def get_config() -> Settings:
    """Return configuration instance.

    Uses singleton pattern with caching to ensure
    a single configuration source in the application.

    Returns:
        Settings: Configuration instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
