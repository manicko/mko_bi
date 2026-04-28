"""Пакет маршрутов API."""

from mko_bi.api.routes import (
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
