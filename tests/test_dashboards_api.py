"""Тесты для API дашбордов.

Тестирует эндпоинты CRUD операций с дашбордами через httpx.AsyncClient
с реальным FastAPI стеком (middleware, Depends).
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestCreateDashboardEndpoint:
    """Тесты эндпоинта создания дашборда."""

    @pytest.mark.asyncio
    async def test_create_dashboard_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешное создание дашборда."""
        response = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Test Dashboard", "config": {"graph_types": ["bar"]}},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Dashboard"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_dashboard_no_auth(self):
        """Ошибка создания без аутентификации."""
        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/dashboards/",
                json={"name": "Test Dashboard", "config": {"graph_types": ["bar"]}},
            )

        assert response.status_code == 401


class TestGetDashboardsEndpoint:
    """Тесты эндпоинта получения списка дашбордов."""

    @pytest.mark.asyncio
    async def test_get_dashboards_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешное получение списка дашбордов."""
        # Создаем дашборд
        await authenticated_client.post(
            "/dashboards/",
            json={"name": "Dashboard 1", "config": {"graph_types": ["bar"]}},
        )

        response = await authenticated_client.get("/dashboards/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_dashboards_no_auth(self):
        """Ошибка без аутентификации."""
        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/dashboards/")

        assert response.status_code == 401


class TestGetDashboardEndpoint:
    """Тесты эндпоинта получения дашборда по ID."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешное получение дашборда."""
        # Создаем дашборд
        create_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Test Dashboard", "config": {"graph_types": ["bar"]}},
        )
        assert create_resp.status_code == 201
        dashboard_id = create_resp.json()["id"]

        response = await authenticated_client.get(f"/dashboards/{dashboard_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dashboard_id

    @pytest.mark.asyncio
    async def test_get_dashboard_not_found(self, authenticated_client: AsyncClient):
        """Дашборд не найден."""
        dashboard_id = str(uuid4())
        response = await authenticated_client.get(f"/dashboards/{dashboard_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_dashboard_no_auth(self):
        """Ошибка без аутентификации."""
        dashboard_id = str(uuid4())

        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(f"/dashboards/{dashboard_id}")

        assert response.status_code == 401


class TestUpdateDashboardEndpoint:
    """Тесты эндпоинта обновления дашборда."""

    @pytest.mark.asyncio
    async def test_update_dashboard_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешное обновление дашборда."""
        # Создаем дашборд
        create_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Test Dashboard", "config": {"graph_types": ["bar"]}},
        )
        assert create_resp.status_code == 201
        dashboard_id = create_resp.json()["id"]

        # Обновляем
        response = await authenticated_client.put(
            f"/dashboards/{dashboard_id}",
            json={"config": {"graph_types": ["line"]}},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_dashboard_not_found(self, authenticated_client: AsyncClient):
        """Дашборд не найден при обновлении."""
        dashboard_id = str(uuid4())
        response = await authenticated_client.put(
            f"/dashboards/{dashboard_id}",
            json={"config": {"graph_types": ["line"]}},
        )

        assert response.status_code == 403


class TestDeleteDashboardEndpoint:
    """Тесты эндпоинта удаления дашборда."""

    @pytest.mark.asyncio
    async def test_delete_dashboard_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешное удаление дашборда."""
        # Создаем дашборд
        create_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "To Delete", "config": {"graph_types": ["bar"]}},
        )
        assert create_resp.status_code == 201
        dashboard_id = create_resp.json()["id"]

        # Удаляем
        response = await authenticated_client.delete(f"/dashboards/{dashboard_id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_dashboard_not_found(self, authenticated_client: AsyncClient):
        """Дашборд не найден при удалении."""
        dashboard_id = str(uuid4())
        response = await authenticated_client.delete(f"/dashboards/{dashboard_id}")

        assert response.status_code == 403


class TestGrantDashboardAccessEndpoint:
    """Тесты эндпоинта предоставления доступа к дашборду."""

    @pytest.mark.asyncio
    async def test_grant_access_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешное предоставление доступа."""
        # Создаем дашборд
        create_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Dashboard with Access", "config": {"graph_types": ["bar"]}},
        )
        assert create_resp.status_code == 201
        dashboard_id = create_resp.json()["id"]

        # Создаем второго пользователя через БД
        from mko_bi.db.repositories.user_repo import UserRepository
        from mko_bi.db.session import get_session
        from mko_bi.core.security import hash_password
    
        repo = UserRepository()
        with get_session() as db:
            user2 = repo.create(
                db=db,
                email="user2@example.com",
                password_hash=hash_password("Pass123!"),
                role="viewer",
            )
            db.commit()

        # Предоставляем доступ
        response = await authenticated_client.post(
            f"/dashboards/{dashboard_id}/access",
            json={"user_id": str(user2.id), "dashboard_id": dashboard_id, "permission": "view"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Доступ успешно предоставлен"

    @pytest.mark.asyncio
    async def test_grant_access_mismatched_ids(self, authenticated_client: AsyncClient, test_user: dict):
        """Ошибка при несовпадении dashboard_id в URL и теле запроса."""
        dashboard_id = str(uuid4())
        other_id = str(uuid4())

        response = await authenticated_client.post(
            f"/dashboards/{dashboard_id}/access",
            json={"user_id": str(uuid4()), "dashboard_id": other_id, "permission_level": "view"},
        )

        assert response.status_code == 403
