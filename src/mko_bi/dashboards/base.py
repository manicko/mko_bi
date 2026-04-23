from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseDashboard(ABC):
    """Base class for all dashboards.

    Provides a config-driven interface for dashboard functionality.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize dashboard with configuration.

        Args:
            config: Dashboard configuration dictionary
        """
        self.config = config
        self.name = config.get("name", "Unnamed Dashboard")

    @abstractmethod
    def get_data(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get dashboard data with optional filters.

        Args:
            filters: Optional filters to apply to data

        Returns:
            Dictionary containing dashboard data
        """
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get dashboard configuration.

        Returns:
            Dashboard configuration dictionary
        """
        return self.config

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update dashboard configuration.

        Args:
            new_config: New configuration to merge
        """
        self.config.update(new_config)


# Registry for dashboard classes
from mko_bi.dashboards.registry import DashboardRegistry


def register_dashboard(name: str, dashboard_class):
    """Register a dashboard class.

    Args:
        name: Dashboard name/identifier
        dashboard_class: Dashboard class to register
    """
    DashboardRegistry.register(name, dashboard_class)


def get_dashboard(name: str):
    """Get a registered dashboard class.

    Args:
        name: Dashboard name/identifier

    Returns:
        Dashboard class or None
    """
    return DashboardRegistry.get(name)
