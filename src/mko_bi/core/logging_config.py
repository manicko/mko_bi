import json
import logging
import logging.config
import os
from typing import Any

from mko_bi.config import get_config


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированного логирования."""

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON.

        Args:
            record: Запись лога.

        Returns:
            str: JSON строка с полями лога.
        """
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "mko_bi",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging() -> None:
    """Настраивает структурированное логирование в формате JSON.

    Создаёт конфигурацию логгера с JSON форматом.
    Настраивает вывод в stdout (для Docker) и файл.

    Уровни логирования:
        - INFO: Основные события (запросы, загрузки, обработка)
        - WARNING: Предупреждения
        - ERROR: Ошибки
    """
    config = get_config()

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "()": "logging.StreamHandler",
                "formatter": "json",
                "level": config.logging.level,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "()": "logging.handlers.RotatingFileHandler",
                "filename": "data/logs/app.json.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": config.logging.level,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "mko_bi": {
                "handlers": ["console", "file"],
                "level": config.logging.level,
                "propagate": False,
            },
            "mko_bi.api": {
                "handlers": ["console", "file"],
                "level": config.logging.level,
                "propagate": False,
            },
            "mko_bi.data": {
                "handlers": ["console", "file"],
                "level": config.logging.level,
                "propagate": False,
            },
            "mko_bi.db": {
                "handlers": ["console", "file"],
                "level": config.logging.level,
                "propagate": False,
            },
            "mko_bi.services": {
                "handlers": ["console", "file"],
                "level": config.logging.level,
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
            "level": config.logging.level,
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
