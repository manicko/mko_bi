"""API routes package."""

from mkobi.api.routes import (
    admin,
    auth,
    client_errors,
    dashboards,
    dashboards_crud,
    dashboards_access,
    dashboards_filters,
    dashboards_graphs,
    filter_values,
    data,
    graphs,
    layouts,
    processing_configs,
    processing_logs,
    upload,
    users,
)

__all__ = [
    "admin",
    "auth",
    "client_errors",
    "dashboards",
    "dashboards_access",
    "dashboards_crud",
    "dashboards_filters",
    "dashboards_graphs",
    "filter_values",
    "data",
    "graphs",
    "layouts",
    "processing_configs",
    "processing_logs",
    "upload",
    "users",
]
