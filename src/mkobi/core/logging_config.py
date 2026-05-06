"""Logging configuration for the application.

Sets up structured JSON logging with console and optional file handlers.
"""

import json
import logging
import logging.config
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON string with log fields.
        """
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "mkobi",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None:
    """Configure application logging.

    Args:
        log_level: Logging level (INFO, WARNING, ERROR). Defaults to "INFO".
        log_file: Optional path to log file. If None, no file handler is added.
    """
    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": log_level,
            "stream": "ext://sys.stdout",
        },
    }

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_path),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": log_level,
            "encoding": "utf-8",
        }

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": handlers,
        "loggers": {
            "mkobi": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "mkobi.api": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "mkobi.data": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "mkobi.db": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "mkobi.services": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": list(handlers.keys()),
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
            "handlers": list(handlers.keys()),
            "level": log_level,
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module.

    Args:
        name: Module name (usually __name__).

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(f"mkobi.{name}")
