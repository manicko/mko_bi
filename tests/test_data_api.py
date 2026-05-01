"""Тесты для API данных дашбордов.

Тестирует эндпоинты получения агрегированных данных,
данных для графиков и применения фильтров через httpx.AsyncClient.
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestGetDashboardAggregatesEndpoint:
    """Тесты эндпоинта получения агрегатов дашборда."""

    @pytest.mark.asyncio
    async def test_get_aggregates_no_auth(self):
        """Ошибка без аутентификации."""
        dashboard_id = str(uuid4())

        # Используем клиент без токена
        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(f"/data/{dashboard_id}")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_aggregates_dashboard_not_found(self, authenticated_client: AsyncClient):
        """Дашборд не найден."""
        dashboard_id = str(uuid4())
        response = await authenticated_client.get(f"/data/{dashboard_id}")

        assert response.status_code == 404


class TestGetDashboardChartsEndpoint:
    """Тесты эндпоинта получения данных для графиков."""

    @pytest.mark.asyncio
    async def test_get_charts_no_auth(self):
        """Ошибка без аутентификации."""
        dashboard_id = str(uuid4())

        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(f"/data/{dashboard_id}/charts")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_charts_not_found(self, authenticated_client: AsyncClient):
        """Дашборд не найден."""
        dashboard_id = str(uuid4())
        response = await authenticated_client.get(f"/data/{dashboard_id}/charts")

        assert response.status_code == 404


class TestApplyFiltersEndpoint:
    """Тесты эндпоинта применения фильтров."""

    @pytest.mark.asyncio
    async def test_apply_filters_no_auth(self):
        """Ошибка без аутентификации."""
        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/data/filter",
                json={"dashboard_id": str(uuid4())},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_apply_filters_dashboard_not_found(self, authenticated_client: AsyncClient):
        """Ошибка при запросе несуществующего дашборда."""
        # Create a dashboard first to verify request is valid
        dashboard_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Test Dashboard", "config": {"graph_types": ["bar"]}},
        )
        assert dashboard_resp.status_code == 201
        valid_dashboard_id = dashboard_resp.json()["id"]

        # Test with non-existent dashboard ID
        non_existent_id = str(uuid4())
        response = await authenticated_client.post(
            "/data/filter",
            json={"dashboard_id": non_existent_id},
        )

        assert response.status_code == 404
