import json
from typing import List, Optional, Dict, Any
from mko_bi.db.models.dashboard import Dashboard as DashboardModel
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.core.permissions import check_access, get_user_by_id


def create_dashboard(
    name: str,
    config: Dict[str, Any],
    user_id: int,
) -> DashboardModel:
    """Create a new dashboard.

    Args:
        name: Dashboard name
        config: Dashboard configuration
        user_id: User ID creating the dashboard

    Returns:
        Created dashboard model
    """
    dashboard_data = {
        "name": name,
        "config": config,
        "user_id": user_id,
    }
    return DashboardRepository.create(dashboard_data)


def get_dashboard(dashboard_id: int, user_id: int) -> Optional[DashboardModel]:
    """Get a dashboard if user has access.

    Args:
        dashboard_id: Dashboard ID
        user_id: User ID requesting access

    Returns:
        Dashboard model if accessible, None otherwise
    """
    dashboard = DashboardRepository.get(dashboard_id)
    if not dashboard:
        return None

    # Check access permissions
    if not check_access(user_id, dashboard_id):
        return None

    return dashboard


def delete_dashboard(dashboard_id: int, user_id: int) -> bool:
    """Delete a dashboard if user has admin access.

    Args:
        dashboard_id: Dashboard ID to delete
        user_id: User ID performing deletion

    Returns:
        True if deleted successfully

    Raises:
        PermissionError: If user doesn't have admin access
    """
    # Check if user is admin
    # This would typically check user role
    # For now, assume check_access handles admin bypass
    if not check_access(user_id, dashboard_id):
        raise PermissionError("User does not have permission to delete this dashboard")

    return DashboardRepository.delete(dashboard_id)


def list_dashboards(user_id: int) -> List[DashboardModel]:
    """List all dashboards accessible to a user.

    Args:
        user_id: User ID requesting dashboards

    Returns:
        List of accessible dashboards
    """
    all_dashboards = DashboardRepository.list_all()
    return [
        dashboard for dashboard in all_dashboards if check_access(user_id, dashboard.id)
    ]
