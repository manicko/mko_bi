"""Logging configuration for the application.

Sets up structured JSON logging with console and optional file handlers.
Provides consistent logging across the application with proper log levels.
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
        # Add extra fields from record (for structured logging)
        # Extra fields are set via logger.info("msg", extra={"key": "value"})
        if hasattr(record, "__dict__"):
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "message",
                    "asctime",
                ]
            }
            log_record.update(extra_fields)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    json_logging: bool = True,
) -> None:
    """Configure application logging.

    Args:
        log_level: Logging level (INFO, WARNING, ERROR). Defaults to "INFO".
        log_file: Optional path to log file. If None, no file handler is added.
        json_logging: If True, use JSON formatting. Otherwise, use standard format.
    """
    # Determine formatter
    if json_logging:
        formatter_name = "json"
        formatters: dict[str, Any] = {
            "json": {
                "()": JSONFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        }
    else:
        formatter_name = "standard"
        formatters = {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        }

    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": formatter_name,
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
            "formatter": formatter_name,
            "level": log_level,
            "encoding": "utf-8",
        }

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
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
            "mkobi.core": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "mkobi.workers": {
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
    # Ensure the name is under mkobi namespace
    if not name.startswith("mkobi."):
        name = f"mkobi.{name}"
    return logging.getLogger(name)
