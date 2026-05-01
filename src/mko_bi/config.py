from pathlib import Path
from typing import Any

import redis
from pydantic import field_validator
from pydantic_settings import BaseSettings, YamlConfigSettingsSource
from pydantic_settings.sources import PydanticBaseSettingsSource


class Settings(BaseSettings):
    """Конфигурация приложения с использованием pydantic-settings.

    Все секретные ключи являются обязательными переменными окружения.
    """

    # --- Database ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "bidb"
    DB_USER: str = "postgres"
    DB_PASSWORD: str  # Обязательная переменная, нет дефолта
    DB_DRIVER: str = "postgresql"

    @property
    def DATABASE_URL(self) -> str:
        """Формирует URL для подключения к PostgreSQL."""
        return (
            f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # --- JWT ---
    JWT_SECRET_KEY: str  # Обязательная переменная, нет дефолта
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Upload ---
    UPLOAD_TEMP_DIR: str = "data/tmp_uploads"
    ALLOWED_FILE_TYPES: list[str] = [".csv.gz"]
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    LAZY_THRESHOLD_MB: float = 10.0  # Use lazy evaluation for files larger than this

    @field_validator("LAZY_THRESHOLD_MB")
    @classmethod
    def validate_lazy_threshold_mb(cls, v: Any) -> float:
        """Валидация порога для lazy evaluation."""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError as err:
                raise ValueError("LAZY_THRESHOLD_MB должен быть числом с плавающей точкой") from err
        return v

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # --- Logging ---
    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_LEVEL: str = "INFO"

    # --- App ---
    APP_NAME: str = "mko_bi"
    DEBUG: bool = False
    API_BASE_URL: str = "http://localhost:8000"
    cors_origins: list[str] = []

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

    @field_validator("DB_PORT")
    @classmethod
    def validate_db_port(cls, v: Any) -> int:
        """Валидация порта базы данных."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError as err:
                raise ValueError("DB_PORT должен быть целым числом") from err
        return v

    @field_validator("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_jwt_expire(cls, v: Any) -> int:
        """Валидация времени жизни токена."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError as err:
                raise ValueError(
                    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES должен быть целым числом"
                ) from err
        return v

    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def validate_max_file_size(cls, v: Any) -> int:
        """Валидация максимального размера файла."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError as err:
                raise ValueError("MAX_FILE_SIZE должен быть целым числом") from err
        return v

    def __init__(self, **data: Any) -> None:
        """Инициализация конфигурации. Создаёт временную директорию для загрузок."""
        super().__init__(**data)
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Создаёт директорию для временных файлов загрузок, если её нет."""
        upload_path = Path(self.UPLOAD_TEMP_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации по ключу.

        Args:
            key: Имя атрибута конфигурации.
            default: Значение по умолчанию, если ключ не найден.

        Returns:
            Значение конфигурации или default.
        """
        return getattr(self, key, default)

    @property
    def database_url(self) -> str:
        """Алиас для DATABASE_URL."""
        return self.DATABASE_URL

    @property
    def jwt_secret_key(self) -> str:
        """Алиас для JWT_SECRET_KEY."""
        return self.JWT_SECRET_KEY

    @property
    def jwt_algorithm(self) -> str:
        """Алиас для JWT_ALGORITHM."""
        return self.JWT_ALGORITHM

    @property
    def upload_temp_dir(self) -> str:
        """Алиас для UPLOAD_TEMP_DIR."""
        return self.UPLOAD_TEMP_DIR

    @property
    def allowed_file_types(self) -> list[str]:
        """Алиас для ALLOWED_FILE_TYPES."""
        return self.ALLOWED_FILE_TYPES

    @property
    def lazy_threshold_mb(self) -> float:
        """Порог в МБ для использования lazy evaluation."""
        return self.LAZY_THRESHOLD_MB

    @property
    def max_file_size(self) -> int:
        """Алиас для MAX_FILE_SIZE."""
        return self.MAX_FILE_SIZE


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
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=config.REDIS_PASSWORD,
        decode_responses=True,
    )

