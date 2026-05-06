"""Пакет маршрутов API."""

from mkobi.api.routes import (
    auth,
    users,
    dashboards,
    upload,
    data,
    filters,
    processing_configs,
    processing_logs,
)

__all__ = [
    "auth",
    "users",
    "dashboards",
    "upload",
    "data",
    "filters",
    "processing_configs",
    "processing_logs",
]
