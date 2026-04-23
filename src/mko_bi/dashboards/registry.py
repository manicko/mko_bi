class DashboardRegistry:
    """Registry for dashboard classes.

    Maintains a mapping of dashboard names to their classes.
    """

    _registry: dict = {}

    @classmethod
    def register(cls, name: str, dashboard_class):
        """Register a dashboard class.

        Args:
            name: Dashboard identifier
            dashboard_class: Dashboard class to register
        """
        cls._registry[name] = dashboard_class

    @classmethod
    def get(cls, name: str):
        """Get a registered dashboard class.

        Args:
            name: Dashboard identifier

        Returns:
            Dashboard class or None if not found
        """
        return cls._registry.get(name)

    @classmethod
    def list_all(cls) -> list:
        """List all registered dashboard names.

        Returns:
            List of dashboard names
        """
        return list(cls._registry.keys())

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a dashboard.

        Args:
            name: Dashboard identifier

        Returns:
            True if unregistered, False if not found
        """
        if name in cls._registry:
            del cls._registry[name]
            return True
        return False
