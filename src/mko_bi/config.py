from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings


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

    # --- Logging ---
    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_LEVEL: str = "INFO"

    # --- App ---
    APP_NAME: str = "mko_bi"
    DEBUG: bool = False

    # Настройки для pydantic-settings
    model_config = {
        "case_sensitive": False,
        "env_prefix": "",
        "extra": "ignore",
    }

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
    def max_file_size(self) -> int:
        """Алиас для MAX_FILE_SIZE."""
        return self.MAX_FILE_SIZE


# Глобальный экземпляр конфигурации
config = Settings()
