from pathlib import Path
from typing import Any

# mypy: ignore-errors

import redis
from pydantic_settings import BaseSettings, YamlConfigSettingsSource
from pydantic_settings.sources import PydanticBaseSettingsSource
from pydantic import BaseModel, PostgresDsn


class DatabaseSettings(BaseModel):
    """Настройки подключения к базе данных."""
    
    host: str = "localhost"
    port: int = 5432
    dbname: str = "bidb"
    user: str = "postgres"
    password: str  # Обязательная переменная, нет дефолта
    
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
    
    secret_key: str  # Обязательная переменная, нет дефолта
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class RedisSettings(BaseModel):
    """Настройки Redis."""
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None


class UploadSettings(BaseModel):
    """Настройки загрузки файлов."""
    
    temp_dir: str = "data/tmp_uploads"
    allowed_file_types: list[str] = [".csv.gz", ".csv"]
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    lazy_threshold_mb: float = 10.0


class LoggingSettings(BaseModel):
    """Настройки логирования."""
    
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level: str = "INFO"


class ChartsSettings(BaseModel):
    """Настройки графиков."""
    
    default_colors: list[str] = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    ]
    
    class YOYSettings(BaseModel):
        """Настройки сравнения год-к-году."""
        
        class CurrentYearStyle(BaseModel):
            line: dict = {"dash": "solid", "width": 3}
        
        class PreviousYearStyle(BaseModel):
            line: dict = {"dash": "dash", "width": 2}
        
        current_year_style: CurrentYearStyle = CurrentYearStyle()
        previous_year_style: PreviousYearStyle = PreviousYearStyle()
    
    yoy: YOYSettings = YOYSettings()
    
    class LayoutSettings(BaseModel):
        template: str = "plotly_white"
        margin: dict = {"l": 50, "r": 50, "t": 50, "b": 50}
    
    layout: LayoutSettings = LayoutSettings()


class Settings(BaseSettings):
    """Конфигурация приложения с использованием pydantic-settings.

    Все настройки загружаются из YAML файла.
    """

    # --- Database ---
    database: DatabaseSettings

    # --- JWT ---
    jwt: JWTSettings

    # --- Upload ---
    upload: UploadSettings

    # --- Redis ---
    redis: RedisSettings

    # --- Logging ---
    logging: LoggingSettings

    # --- Charts ---
    charts: ChartsSettings

    # --- App ---
    app_name: str = "mko_bi"
    debug: bool = False
    api_base_url: str = "http://localhost:8000"
    cors_origins: list[str] = []

    # --- Environment ---
    env: str = "development"

    # --- Database Migrations ---
    auto_migrate: bool = False
    migration_script_path: str = "alembic"
    alembic_ini_path: str = "alembic.ini"
    test_database_url: str | None = None
    recreate_test_db: bool = False

    # Настройки для pydantic-settings
    model_config = {
        "case_sensitive": False,
        "env_prefix": "",
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
        """Customize settings sources to include YAML config file."""
        yaml_file_path = Path(__file__).parent / "settings" / "app.yaml"
        yaml_source = YamlConfigSettingsSource(
            settings_cls,
            yaml_file=yaml_file_path,
        )
        return (yaml_source, env_settings, init_settings)

    @property
    def DATABASE_URL(self) -> str:
        """Формирует URL для подключения к PostgreSQL."""
        return str(self.database.database_url)

    @property
    def database_url(self) -> str:
        """Алиас для DATABASE_URL."""
        return self.DATABASE_URL

    @property
    def jwt_secret_key(self) -> str:
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
        """Алиас для ALLOWED_FILE_TYPES."""
        return self.upload.allowed_file_types

    @property
    def lazy_threshold_mb(self) -> float:
        """Порог в МБ для использования lazy evaluation."""
        return self.upload.lazy_threshold_mb

    @property
    def max_file_size(self) -> int:
        """Алиас для MAX_FILE_SIZE."""
        return self.upload.max_file_size

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации по ключу.

        Args:
            key: Имя атрибута конфигурации.
            default: Значение по умолчанию, если ключ не найден.

        Returns:
            Значение конфигурации или default.
        """
        return getattr(self, key, default)

    def __init__(self, **data: Any) -> None:
        """Инициализация конфигурации. Создаёт временную директорию для загрузок."""
        super().__init__(**data)
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Создаёт директорию для временных файлов загрузок, если её нет."""
        upload_path = Path(self.upload.temp_dir)
        upload_path.mkdir(parents=True, exist_ok=True)


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