import logging
import logging.config
import os
from typing import Any

from mko_bi.config import config


def setup_logging() -> None:
    """Настраивает логирование для приложения.

    Создаёт конфигурацию логгера с форматом:
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    Уровни логирования:
        - INFO: Основные события (запросы, загрузки, обработка)
        - WARNING: Предупреждения
        - ERROR: Ошибки
    """
    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": config.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "()": "logging.StreamHandler",
                "formatter": "default",
                "level": config.LOG_LEVEL,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "()": "logging.handlers.RotatingFileHandler",
                "filename": "data/logs/app.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "formatter": "default",
                "level": config.LOG_LEVEL,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "mko_bi": {
                "handlers": ["console", "file"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            },
            "mko_bi.api": {
                "handlers": ["console", "file"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            },
            "mko_bi.data": {
                "handlers": ["console", "file"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            },
            "mko_bi.db": {
                "handlers": ["console", "file"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            },
            "mko_bi.services": {
                "handlers": ["console", "file"],
                "level": config.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": config.LOG_LEVEL,
        },
    }

    # Создаём директорию для логов, если её нет
    os.makedirs("data/logs", exist_ok=True)

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Возвращает настроенный логгер.

    Args:
        name: Имя логгера (обычно __name__).

    Returns:
        Настроенный экземпляр Logger.
    """
    return logging.getLogger(f"mko_bi.{name}")


def get_logger_for_module(module_name: str) -> logging.Logger:
    """Возвращает логгер для конкретного модуля.

    Args:
        module_name: Полное имя модуля.

    Returns:
        Настроенный экземпляр Logger.
    """
    return logging.getLogger(module_name)
