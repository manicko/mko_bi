"""Пакет маршрутов API."""

from mkobi.api.routes import (
    auth,
    users,
    dashboards,
    layouts,
    upload,
    data,
    filters,
    processing_configs,
    processing_logs,
    admin,
)

__all__ = [
    "auth",
    "users",
    "dashboards",
    "layouts",
    "upload",
    "data",
    "filters",
    "processing_configs",
    "processing_logs",
    "admin",
]
