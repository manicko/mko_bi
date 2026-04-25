import os
from typing import Any
from pathlib import Path


class Config:
    """Конфигурация приложения с поддержкой переменных окружения и fallback значений."""

    # --- Database ---
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432") or "5432")
    DB_NAME: str = os.getenv("DB_NAME", "mydb")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "1234")
    DB_DRIVER: str = os.getenv("DB_DRIVER", "postgresql")

    @property
    def DATABASE_URL(self) -> str:
        """Формирует URL для подключения к PostgreSQL."""
        return (
            f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # --- JWT ---
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-secret-key-change-in-production-use-env-variable",
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # --- Upload ---
    UPLOAD_TEMP_DIR: str = os.getenv("UPLOAD_TEMP_DIR", "data/tmp_uploads")
    ALLOWED_FILE_TYPES: list[str] = [
        ".csv.gz",
    ]
    MAX_FILE_SIZE: int = int(
        os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024))
    )  # 100MB

    # --- Logging ---
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- App ---
    APP_NAME: str = os.getenv("APP_NAME", "mko_bi")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    def __init__(self) -> None:
        """Инициализация конфигурации. Создаёт временную директорию для загрузок."""
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
config = Config()
