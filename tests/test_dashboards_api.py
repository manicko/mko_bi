"""Тесты для API дашбордов.

Тестирует все эндпоинты CRUD операций с дашбордами,
включая проверку прав доступа и валидацию данных.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from mko_bi.main import create_application
from mko_bi.models.dashboard import DashboardConfig, DashboardRead
from mko_bi.models.user import UserDB
from mko_bi.models.user_roles import UserRoleEnum
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.core.security import create_access_token


@pytest.fixture
def mock_user():
    """Создает мок пользователя."""
    user = MagicMock(spec=UserDB)
    user.id = uuid4()
    user.email = "test@example.com"
    user.role = UserRoleEnum.admin
    return user


@pytest.fixture
def valid_token(mock_user):
    """Создает валидный JWT токен для тестирования."""
    data = {"user_id": str(mock_user.id), "email": mock_user.email}
    return create_access_token(data=data)


@pytest.fixture
def client():
    """Создает тестовый клиент FastAPI."""
    app = create_application()
    yield TestClient(app)


class TestCreateDashboard:
    """Тесты для эндпоинта создания дашборда."""



    def test_create_dashboard_invalid_config(self, mocker, client, valid_token):
        """Создание дашборда с невалидной конфигурацией."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.services.dashboard_service.create_dashboard",
            side_effect=ValueError("Недопустимый тип графика"),
        )

        response = client.post(
            "/dashboards/",
            json={
                "name": "Test Dashboard",
                "config": {"graph_types": ["invalid_type"]},
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 422

    def test_create_dashboard_db_error(self, mocker, client, valid_token):
        """Ошибка базы данных при создании дашборда."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.services.dashboard_service.create_dashboard",
            side_effect=Exception("Database error"),
        )

        response = client.post(
            "/dashboards/",
            json={
                "name": "Test Dashboard",
                "config": {"graph_types": ["bar"]},
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 500


class TestGetDashboards:
    """Тесты для эндпоинта получения списка дашбордов."""

    def test_get_dashboards_success(self, mocker, client, valid_token):
        """Успешное получение списка дашбордов."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()
        mock_dashboard.name = "Test Dashboard"
        mock_dashboard.description = "Test description"
        mock_dashboard.config = {"graph_types": ["bar"]}
        mock_dashboard.created_at = "2026-04-24T16:02:46+03:00"
        mock_dashboard.updated_at = "2026-04-24T16:02:46+03:00"

        mocker.patch(
            "mko_bi.services.dashboard_service.get_user_dashboards",
            return_value=[DashboardRead.model_validate(mock_dashboard)],
        )

        response = client.get("/dashboards/", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Dashboard"

    def test_get_dashboards_empty(self, mocker, client, valid_token):
        """Получение пустого списка дашбордов."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.services.dashboard_service.get_user_dashboards",
            return_value=[],
        )

        response = client.get("/dashboards/", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 200
        assert response.json() == []

    def test_get_dashboards_db_error(self, mocker, client, valid_token):
        """Ошибка базы данных при получении списка дашбордов."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.services.dashboard_service.get_user_dashboards",
            side_effect=Exception("Database error"),
        )

        response = client.get("/dashboards/", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 500


class TestGetDashboard:
    """Тесты для эндпоинта получения дашборда по ID."""

    def test_get_dashboard_success(self, mocker, client, valid_token):
        """Успешное получение дашборда."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        dashboard_id = uuid4()
        mock_dashboard.id = dashboard_id
        mock_dashboard.name = "Test Dashboard"
        mock_dashboard.description = "Test description"
        mock_dashboard.config = {"graph_types": ["bar"]}
        mock_dashboard.created_at = "2026-04-24T16:02:46+03:00"
        mock_dashboard.updated_at = "2026-04-24T16:02:46+03:00"

        mocker.patch(
            "mko_bi.services.dashboard_service.get_dashboard",
            return_value=DashboardRead.model_validate(mock_dashboard),
        )

        response = client.get(f"/dashboards/{dashboard_id}", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Dashboard"
        assert data["id"] == str(dashboard_id)

    def test_get_dashboard_not_found(self, mocker, client, valid_token):
        """Дашборд не найден."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.services.dashboard_service.get_dashboard",
            return_value=None,
        )

        dashboard_id = uuid4()
        response = client.get(f"/dashboards/{dashboard_id}", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 404

    def test_get_dashboard_no_access(self, mocker, client, valid_token):
        """Нет доступа к дашборду."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.services.dashboard_service.get_dashboard",
            return_value=None,
        )

        dashboard_id = uuid4()
        response = client.get(f"/dashboards/{dashboard_id}", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 404


class TestUpdateDashboard:
    """Тесты для эндпоинта обновления дашборда."""

    def test_update_dashboard_success(self, mocker, client, valid_token):
        """Успешное обновление дашборда."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        dashboard_id = uuid4()
        mock_dashboard.id = dashboard_id
        mock_dashboard.name = "Updated Dashboard"
        mock_dashboard.description = "Updated description"
        mock_dashboard.config = {"graph_types": ["bar", "line"]}
        mock_dashboard.created_at = "2026-04-24T16:02:46+03:00"
        mock_dashboard.updated_at = "2026-04-24T17:00:00+03:00"

        mocker.patch(
            "mko_bi.services.dashboard_service.update_dashboard",
            return_value=DashboardRead.model_validate(mock_dashboard),
        )

        response = client.put(
            f"/dashboards/{dashboard_id}",
            json={
                "name": "Updated Dashboard",
                "description": "Updated description",
                "config": {
                    "graph_types": ["bar", "line"],
                    "filters": [{"field": "year", "type": "select"}],
                },
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Dashboard"
        assert data["config"]["graph_types"] == ["bar", "line"]

    def test_update_dashboard_no_permission(self, mocker, client, valid_token):
        """Нет прав на обновление дашборда."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=False,
        )

        dashboard_id = uuid4()
        response = client.put(
            f"/dashboards/{dashboard_id}",
            json={
                "name": "Updated Dashboard",
                "config": {"graph_types": ["bar"]},
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 403

    def test_update_dashboard_not_found(self, mocker, client, valid_token):
        """Дашборд не найден для обновления."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        mocker.patch(
            "mko_bi.services.dashboard_service.update_dashboard",
            return_value=None,
        )

        dashboard_id = uuid4()
        response = client.put(
            f"/dashboards/{dashboard_id}",
            json={
                "name": "Updated Dashboard",
                "config": {"graph_types": ["bar"]},
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 404


class TestDeleteDashboard:
    """Тесты для эндпоинта удаления дашборда."""

    def test_delete_dashboard_success(self, mocker, client, valid_token):
        """Успешное удаление дашборда."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        mocker.patch(
            "mko_bi.services.dashboard_service.delete_dashboard",
            return_value=True,
        )

        dashboard_id = uuid4()
        response = client.delete(f"/dashboards/{dashboard_id}", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 204

    def test_delete_dashboard_no_permission(self, mocker, client, valid_token):
        """Нет прав на удаление дашборда."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=False,
        )

        dashboard_id = uuid4()
        response = client.delete(f"/dashboards/{dashboard_id}", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 403

    def test_delete_dashboard_not_found(self, mocker, client, valid_token):
        """Дашборд не найден для удаления."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        mocker.patch(
            "mko_bi.services.dashboard_service.delete_dashboard",
            return_value=False,
        )

        dashboard_id = uuid4()
        response = client.delete(f"/dashboards/{dashboard_id}", headers={"Authorization": f"Bearer {valid_token}"})

        assert response.status_code == 404


class TestGrantDashboardAccess:
    """Тесты для эндпоинта предоставления доступа к дашборду."""

    def test_grant_access_success(self, mocker, client, valid_token):
        """Успешное предоставление доступа."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        mocker.patch(
            "mko_bi.services.dashboard_service.grant_access",
            return_value=True,
        )

        dashboard_id = uuid4()
        user_id = uuid4()
        response = client.post(
            f"/dashboards/{dashboard_id}/access",
            json={
                "user_id": str(user_id),
                "dashboard_id": str(dashboard_id),
                "permission_level": "edit",
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Доступ успешно предоставлен"
        assert data["permission"] == "edit"

    def test_grant_access_no_admin_permission(self, mocker, client, valid_token):
        """Нет прав на управление доступом (не admin)."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=False,
        )

        dashboard_id = uuid4()
        user_id = uuid4()
        response = client.post(
            f"/dashboards/{dashboard_id}/access",
            json={
                "user_id": str(user_id),
                "dashboard_id": str(dashboard_id),
                "permission_level": "edit",
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 403

    def test_grant_access_dashboard_mismatch(self, mocker, client, valid_token):
        """Несовпадение dashboard_id в URL и теле запроса."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        dashboard_id = uuid4()
        user_id = uuid4()
        response = client.post(
            f"/dashboards/{dashboard_id}/access",
            json={
                "user_id": str(user_id),
                "dashboard_id": str(uuid4()),  # Different ID
                "permission_level": "edit",
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 422

    def test_grant_access_invalid_permission(self, mocker, client, valid_token):
        """Недопустимый уровень доступа."""
        mock_db = MagicMock(spec=Session)
        mocker.patch("mko_bi.api.routes.dashboards.get_db", return_value=mock_db)

        mocker.patch(
            "mko_bi.core.permissions.check_dashboard_access",
            return_value=True,
        )

        mocker.patch(
            "mko_bi.services.dashboard_service.grant_access",
            side_effect=ValueError("Недопустимый уровень доступа"),
        )

        dashboard_id = uuid4()
        user_id = uuid4()
        response = client.post(
            f"/dashboards/{dashboard_id}/access",
            json={
                "user_id": str(user_id),
                "dashboard_id": str(dashboard_id),
                "permission_level": "invalid",
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 422