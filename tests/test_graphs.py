"""Tests for graphs API."""

import uuid
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.core.security import hash_password
from mkobi.db.repositories.user_repo import UserRepository


class TestGraphsAPI:
    """Test cases for graphs API endpoints."""

    async def _create_admin_user(self, async_db_session: AsyncSession, suffix: str = ""):
        """Helper to create and commit an admin user."""
        user_repo = UserRepository()
        email = f"admin_{suffix}{uuid.uuid4().hex[:8]}@example.com"
        admin = await user_repo.create(
            db=async_db_session,
            email=email,
            password_hash=hash_password("AdminPass123!"),
            role="admin",
        )
        await async_db_session.commit()
        return admin

    async def _create_viewer_user(self, async_db_session: AsyncSession, suffix: str = ""):
        """Helper to create and commit a viewer user."""
        user_repo = UserRepository()
        email = f"viewer_{suffix}{uuid.uuid4().hex[:8]}@example.com"
        viewer = await user_repo.create(
            db=async_db_session,
            email=email,
            password_hash=hash_password("TestPass123!"),
            role="viewer",
        )
        await async_db_session.commit()
        return viewer

    async def test_create_graph_admin_required(
        self, async_db_session: AsyncSession, async_client: AsyncClient
    ) -> None:
        """Test that creating graph requires admin role."""
        # Create a viewer user (not admin)
        viewer = await self._create_viewer_user(async_db_session, suffix="graph_test_")

        # Create an admin user to own the dashboard
        admin = await self._create_admin_user(async_db_session, suffix="graph_test_")

        # Login as admin and create dashboard via API
        admin_login = await async_client.post(
            "/auth/login",
            json={"email": admin.email, "password": "AdminPass123!"},
        )
        assert admin_login.status_code == status.HTTP_200_OK
        admin_token = admin_login.json()["access_token"]

        dashboard_response = await async_client.post(
            "/dashboards/",
            json={
                "name": f"test-dashboard-{uuid.uuid4().hex[:8]}",
                "description": "Test",
                "config": {"graph_types": ["bar"]},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert dashboard_response.status_code == status.HTTP_201_CREATED
        dashboard_id = dashboard_response.json()["id"]

        # Login as viewer and attempt to create a graph
        viewer_login = await async_client.post(
            "/auth/login",
            json={"email": viewer.email, "password": "TestPass123!"},
        )
        assert viewer_login.status_code == status.HTTP_200_OK
        viewer_token = viewer_login.json()["access_token"]

        response = await async_client.post(
            f"/dashboards/{dashboard_id}/graphs",
            json={
                "dashboard_id": str(dashboard_id),
                "name": "test-graph",
                "type": "bar",
                "config": {"xaxis": {"title": "X"}},
                "dimensions": ["category"],
                "metrics": ["sales"],
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_graphs_for_dashboard(
        self, async_db_session: AsyncSession, async_client: AsyncClient
    ) -> None:
        """Test getting graphs for a dashboard."""
        # Create admin user
        admin = await self._create_admin_user(async_db_session, suffix="graph_test2_")

        # Login as admin
        login_response = await async_client.post(
            "/auth/login",
            json={"email": admin.email, "password": "AdminPass123!"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        admin_token = login_response.json()["access_token"]

        # Create dashboard via API
        dashboard_response = await async_client.post(
            "/dashboards/",
            json={
                "name": f"test-dashboard-{uuid.uuid4().hex[:8]}",
                "description": "Test",
                "config": {"graph_types": ["bar", "line"]},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert dashboard_response.status_code == status.HTTP_201_CREATED
        dashboard_id = dashboard_response.json()["id"]

        # Create graphs via API
        graph1_response = await async_client.post(
            f"/dashboards/{dashboard_id}/graphs",
            json={
                "dashboard_id": str(dashboard_id),
                "name": "Graph 1",
                "type": "bar",
                "config": {"xaxis": {"title": "Category"}, "yaxis": {"title": "Sales"}},
                "dimensions": ["category", "region"],
                "metrics": ["sales", "profit", "qty"],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert graph1_response.status_code == status.HTTP_201_CREATED

        graph2_response = await async_client.post(
            f"/dashboards/{dashboard_id}/graphs",
            json={
                "dashboard_id": str(dashboard_id),
                "name": "Graph 2",
                "type": "line",
                "config": {"xaxis": {"title": "Date"}, "yaxis": {"title": "Revenue"}},
                "dimensions": ["region", "product"],
                "metrics": ["sales", "profit"],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert graph2_response.status_code == status.HTTP_201_CREATED

        # Get graphs for dashboard via API
        graphs_response = await async_client.get(
            f"/dashboards/{dashboard_id}/graphs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert graphs_response.status_code == status.HTTP_200_OK
        data = graphs_response.json()
        assert len(data) >= 2
