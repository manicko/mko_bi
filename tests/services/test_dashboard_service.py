import json
import pytest
from unittest.mock import Mock, patch
from mko_bi.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    delete_dashboard,
    list_dashboards,
)
from mko_bi.db.models.dashboard import Dashboard as DashboardModel


def test_create_dashboard_success():
    """Test successful dashboard creation."""
    # Mock repository
    mock_dashboard = DashboardModel()
    mock_dashboard.id = 1
    mock_dashboard.name = "Test Dashboard"
    mock_dashboard.config = '{"test": "config"}'
    mock_dashboard.user_id = 1

    with patch(
        "mko_bi.services.dashboard_service.DashboardRepository.create"
    ) as mock_create:
        mock_create.return_value = mock_dashboard

        result = create_dashboard(
            name="Test Dashboard", config={"test": "config"}, user_id=1
        )

        # Verify
        mock_create.assert_called_once()
        assert result.name == "Test Dashboard"
        assert result.config == {"test": "config"}


def test_create_dashboard_empty_name():
    """Test dashboard creation with empty name."""
    with pytest.raises(ValueError, match="Dashboard name cannot be empty"):
        create_dashboard(name="", config={"test": "config"}, user_id=1)


def test_get_dashboard_success():
    """Test successful dashboard retrieval."""
    # Mock repository and permissions
    mock_dashboard = DashboardModel()
    mock_dashboard.id = 1
    mock_dashboard.name = "Test Dashboard"
    mock_dashboard.config = '{"test": "config"}'
    mock_dashboard.user_id = 1

    with (
        patch("mko_bi.services.dashboard_service.DashboardRepository.get") as mock_get,
        patch("mko_bi.services.dashboard_service.check_access") as mock_check,
    ):
        mock_get.return_value = mock_dashboard
        mock_check.return_value = True

        result = get_dashboard(dashboard_id=1, user_id=1)

        # Verify
        mock_get.assert_called_once_with(1)
        mock_check.assert_called_once_with(1, 1)
        assert result is not None
        assert result.id == 1


def test_get_dashboard_not_found():
    """Test dashboard retrieval when not found."""
    with patch("mko_bi.services.dashboard_service.DashboardRepository.get") as mock_get:
        mock_get.return_value = None

        result = get_dashboard(dashboard_id=999, user_id=1)

        # Verify
        mock_get.assert_called_once_with(999)
        assert result is None


def test_get_dashboard_no_access():
    """Test dashboard retrieval when user has no access."""
    # Mock repository and permissions
    mock_dashboard = DashboardModel()
    mock_dashboard.id = 1
    mock_dashboard.name = "Test Dashboard"
    mock_dashboard.config = '{"test": "config"}'
    mock_dashboard.user_id = 1

    with (
        patch("mko_bi.services.dashboard_service.DashboardRepository.get") as mock_get,
        patch("mko_bi.services.dashboard_service.check_access") as mock_check,
    ):
        mock_get.return_value = mock_dashboard
        mock_check.return_value = False

        result = get_dashboard(dashboard_id=1, user_id=2)

        # Verify
        mock_get.assert_called_once_with(1)
        mock_check.assert_called_once_with(2, 1)
        assert result is None


def test_delete_dashboard_success():
    """Test successful dashboard deletion."""
    with (
        patch("mko_bi.services.dashboard_service.check_access") as mock_check,
        patch(
            "mko_bi.services.dashboard_service.DashboardRepository.delete"
        ) as mock_delete,
    ):
        mock_check.return_value = True
        mock_delete.return_value = True

        result = delete_dashboard(dashboard_id=1, user_id=1)

        # Verify
        mock_check.assert_called_once_with(1, 1)
        mock_delete.assert_called_once_with(1)
        assert result is True


def test_delete_dashboard_no_permission():
    """Test dashboard deletion when user has no permission."""
    with patch("mko_bi.services.dashboard_service.check_access") as mock_check:
        mock_check.return_value = False

        with pytest.raises(PermissionError, match="User does not have permission"):
            delete_dashboard(dashboard_id=1, user_id=2)

        mock_check.assert_called_once_with(1, 2)


def test_list_dashboards():
    """Test listing dashboards for a user."""
    # Mock repositories
    mock_dashboard1 = DashboardModel()
    mock_dashboard1.id = 1
    mock_dashboard1.name = "Dashboard 1"
    mock_dashboard1.config = "{}"
    mock_dashboard1.user_id = 1

    mock_dashboard2 = DashboardModel()
    mock_dashboard2.id = 2
    mock_dashboard2.name = "Dashboard 2"
    mock_dashboard2.config = "{}"
    mock_dashboard2.user_id = 2

    with (
        patch(
            "mko_bi.services.dashboard_service.DashboardRepository.list_all"
        ) as mock_list_all,
        patch("mko_bi.services.dashboard_service.check_access") as mock_check,
    ):
        mock_list_all.return_value = [mock_dashboard1, mock_dashboard2]
        # User 1 has access to dashboard 1 only
        mock_check.side_effect = lambda user_id, dashboard_id: (
            (user_id == 1 and dashboard_id == 1) or (user_id == 2 and dashboard_id == 2)
        )

        result = list_dashboards(user_id=1)

        # Verify
        mock_list_all.assert_called_once()
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].name == "Dashboard 1"


if __name__ == "__main__":
    pytest.main([__file__])
