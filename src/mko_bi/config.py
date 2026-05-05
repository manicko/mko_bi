from pathlib import Path
from typing import Any

import logging
import redis
from pydantic_settings import BaseSettings, YamlConfigSettingsSource
from pydantic_settings.sources import PydanticBaseSettingsSource
from pydantic import BaseModel, PostgresDsn, Field

from mko_bi.models.enums import EnvironmentEnum, FileExtensionEnum, MimeTypeEnum

from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

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
        import os
        
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
                        logger.debug(f"Loaded secret for {base_env_var} from {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to read secret file {file_path}: {e}")
        
        return result


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
    
    def __repr__(self) -> str:
        return "SecretsFileSource()"


class DatabaseSettings(BaseModel):
    """Настройки подключения к базе данных."""

    host: str = "localhost"
    port: int = 5432
    dbname: str = "bidb"
    user: str = "postgres"
    password: str | None = None
    
    @property
    def database_url(self) -> PostgresDsn:
        """Формирует URL для подключения к PostgreSQL."""
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.dbname,
        )


class JWTSettings(BaseModel):
    """Настройки JWT аутентификации."""
    
    secret_key: str | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class RedisSettings(BaseModel):
    """Настройки Redis."""
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None


class AppSettings(BaseModel):
    """Настройки приложения."""

    name: str = "mko_bi"
    version: str = "1.0.0"


class UploadSettings(BaseModel):
    """Настройки загрузки файлов."""

    temp_dir: str = "data/tmp_uploads"
    temp_dir_prefix: str = "mko_bi_upload"
    max_file_size_mb: int = Field(default=100, alias="max_file_size_mb")
    allowed_extensions: list[FileExtensionEnum] = [FileExtensionEnum.CSV_GZ, FileExtensionEnum.CSV]
    allowed_mime_types: list[MimeTypeEnum] = [MimeTypeEnum.TEXT_CSV, MimeTypeEnum.APPLICATION_GZIP]
    lazy_threshold_mb: float = 10.0

    model_config = {"populate_by_name": True}


class EmailSettings(BaseModel):
    """Настройки email."""

    blocked_domains: list[str] = ["tempmail.com", "throwaway.email"]


class DashboardSettings(BaseModel):
    """Настройки дашбордов."""

    default_items_per_page: int = 20


class LoggingSettings(BaseModel):
    """Настройки логирования."""

    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level: str = "INFO"
    log_file: str | None = None
    json_logging: bool = True


class ChartsSettings(BaseModel):
    """Настройки графиков."""
    
    default_colors: list[str] = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    ]
    
    class YOYSettings(BaseModel):
        """Настройки сравнения год-к-году."""
        
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
    """Конфигурация приложения с использованием pydantic-settings.

    Все настройки загружаются из переменных окружения, .env файла,
    Docker secrets и YAML файла с соблюдением приоритета.
    """

    # --- App ---
    app_name: str = "mko_bi"
    environment: EnvironmentEnum = Field(default=EnvironmentEnum.DEVELOPMENT, alias="ENV")
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

    # --- Database Migrations ---
    auto_migrate: bool = False
    migration_script_path: str = "alembic"
    alembic_ini_path: str = "alembic.ini"
    test_database_url: str | None = None
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
        return (env_settings, secrets_source, dotenv_settings, yaml_source, init_settings)
    
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
        """Создаёт директорию для временных файлов загрузок, если её нет."""
        upload_path = Path(self.upload.temp_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

    @property
    def DATABASE_URL(self) -> str:
        """Формирует URL для подключения к PostgreSQL."""
        return str(self.database.database_url)

    @property
    def database_url(self) -> str:
        """Алиас для DATABASE_URL."""
        return self.DATABASE_URL

    @property
    def jwt_secret_key(self) -> str | None:
        """Алиас для JWT_SECRET_KEY."""
        return self.jwt.secret_key

    @property
    def jwt_algorithm(self) -> str:
        """Алиас для JWT_ALGORITHM."""
        return self.jwt.algorithm

    @property
    def upload_temp_dir(self) -> str:
        """Алиас для UPLOAD_TEMP_DIR."""
        return self.upload.temp_dir

    @property
    def allowed_file_types(self) -> list[str]:
        """Возвращает список разрешённых расширений файлов."""
        return [ext.value for ext in self.upload.allowed_extensions]

    @property
    def allowed_mime_types(self) -> list[str]:
        """Возвращает список разрешённых MIME-типов."""
        return [mime.value for mime in self.upload.allowed_mime_types]

    @property
    def lazy_threshold_mb(self) -> float:
        """Порог в МБ для использования lazy evaluation."""
        return self.upload.lazy_threshold_mb

    @property
    def max_file_size(self) -> int:
        """Возвращает максимальный размер файла в байтах."""
        return self.upload.max_file_size_mb * 1024 * 1024

    @property
    def log_level(self) -> str:
        """Алиас для уровня логирования."""
        return self.logging.level

    @property
    def log_file(self) -> str | None:
        """Алиас для файла логирования."""
        return self.logging.log_file

    def load_yaml_config(self) -> dict[str, Any]:
        """Загружает и возвращает конфигурацию из app.yaml.

        Returns:
            dict[str, Any]: Словарь с настройками из YAML файла.
        """
        yaml_file_path = Path(__file__).parent / "settings" / "app.yaml"
        if yaml_file_path.exists():
            import yaml
            with open(yaml_file_path) as f:
                return yaml.safe_load(f)  # type: ignore[no-any-return]
        return {}


# Кэшированный экземпляр конфигурации
_settings: Settings | None = None


def get_config() -> Settings:
    """Возвращает экземпляр конфигурации.
    
    Использует паттерн синглтон с кэшированием для обеспечения
    единого источника конфигурации в приложении.
    
    Returns:
        Settings: Экземпляр конфигурации.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_redis_client() -> "redis.Redis":
    """Возвращает клиент Redis на основе настроек.
    
    Returns:
        redis.Redis: Клиент Redis.
    """
    import redis
    config = get_config()
    return redis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        password=config.redis.password,
        decode_responses=True,
    )