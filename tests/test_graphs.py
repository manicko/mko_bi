"""Tests for graphs API."""


from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.models import graphs as graph_model
from mkobi.db.models.dashboard import Dashboard
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.core.security import hash_password, create_access_token


class TestGraphsAPI:
    """Test cases for graphs API endpoints."""

    async def test_create_graph_admin_required(
        self, async_db_session: AsyncSession, async_client: AsyncClient
    ) -> None:
        """Test that creating graph requires admin role."""
        # Create a viewer user (not admin)
        user = await UserRepository.create(
            db=async_db_session,
            email="viewer@example.com",
            password_hash=hash_password("TestPass123!"),
            role="viewer",
        )
        await async_db_session.commit()

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        # Create dashboard
        dashboard = Dashboard(name="test_dashboard")
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        response = await async_client.post(
            f"/dashboards/{dashboard.id}/graphs",
            json={
                "name": "test_graph",
                "type": "bar",
                "dashboard_id": str(dashboard.id),
                "config": {"xaxis": {"title": "X"}},
                "dimensions": ["category"],
                "metrics": ["sales"],
            },
            headers=headers,
        )
        assert response.status_code == 403

    async def test_get_graphs_for_dashboard(
        self, async_db_session: AsyncSession, async_client: AsyncClient
    ) -> None:
        """Test getting graphs for a dashboard."""
        # Create admin user
        user = await UserRepository.create(
            db=async_db_session,
            email="admin@example.com",
            password_hash=hash_password("TestPass123!"),
            role="admin",
        )
        await async_db_session.commit()

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        # Create dashboard
        dashboard = Dashboard(name="test_dashboard")
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        # Create graph
        graph = graph_model.Graph(
            name="test_graph",
            type="bar",
            dashboard_id=dashboard.id,
            config={"xaxis": {"title": "X"}},
            dimensions=["category"],
            metrics=["sales"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()

        response = await async_client.get(
            f"/dashboards/{dashboard.id}/graphs",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
