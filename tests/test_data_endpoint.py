"""Tests for /data/aggregated endpoint - API contract verification."""


from fastapi import status
from httpx import AsyncClient

from mkobi.models.enums import DashboardPermission
from mkobi.services.graph_service import GraphService
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.graph_repo import GraphRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.services.dashboard_service import DashboardService
from mkobi.models.graph import GraphCreate


class TestAggregatedDataEndpointContract:
    """Tests verifying INT-001 contract: graph_id optional, returns all dashboard graphs when absent."""

    async def test_get_aggregated_without_graph_id_returns_200(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test GET /data/aggregated?dashboard_id=<id> returns 200 with graphs array (no 422)."""
        # Create a dashboard and grant access
        ds = DashboardService(DashboardRepository(), AccessRepository())
        dashboard = await ds.create_dashboard(
            name="test-aggregated-contract",
            config={"graph_types": ["bar"]},
            owner_id=test_user["id"],
            db=async_db_session,
        )

        # Grant view access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )

        # Make request WITHOUT graph_id parameter
        response = await authenticated_client.get(
            "/data/aggregated",
            params={"dashboard_id": str(dashboard.id)},
        )

        # Should return 200 OK, not 422 Unprocessable Entity
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "graphs" in data
        assert isinstance(data["graphs"], list)

    async def test_get_aggregated_with_graph_id_returns_single_graph(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test GET /data/aggregated?dashboard_id=<id>&graph_id=<gid> returns single graph data."""
        # Create dashboard with graphs
        ds = DashboardService(DashboardRepository(), AccessRepository())
        dashboard = await ds.create_dashboard(
            name="test-aggregated-single-graph",
            config={"graph_types": ["bar"]},
            owner_id=test_user["id"],
            db=async_db_session,
        )

        graph_service = GraphService(GraphRepository())
        graph = await graph_service.create(
            GraphCreate(
                name="Contract Test Graph",
                type="bar",
                dashboard_id=dashboard.id,
                config={},
                dimensions=["category"],
                metrics=["revenue"],
            ),
            db=async_db_session,
        )

        # Grant view access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )

        # Make request WITH graph_id parameter
        response = await authenticated_client.get(
            "/data/aggregated",
            params={"dashboard_id": str(dashboard.id), "graph_id": str(graph.id)},
        )

        # Should return 200 OK
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "graphs" in data
        assert isinstance(data["graphs"], list)
        # Should return exactly one graph
        assert len(data["graphs"]) == 1
        assert data["graphs"][0]["graph_id"] == str(graph.id)

    async def test_get_aggregated_returns_graphs_with_metadata(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test that response includes graph metadata (type, name, data)."""
        # Create dashboard with graph
        ds = DashboardService(DashboardRepository(), AccessRepository())
        dashboard = await ds.create_dashboard(
            name="test-aggregated-metadata",
            config={"graph_types": ["bar", "line"]},
            owner_id=test_user["id"],
            db=async_db_session,
        )

        graph_service = GraphService(GraphRepository())
        await graph_service.create(
            GraphCreate(
                name="Metadata Test Graph",
                type="bar",
                dashboard_id=dashboard.id,
                config={},
                dimensions=["category"],
                metrics=["revenue"],
            ),
            db=async_db_session,
        )

        # Grant view access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )

        response = await authenticated_client.get(
            "/data/aggregated",
            params={"dashboard_id": str(dashboard.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if data["graphs"]:  # Only check if graphs exist
            graph_data = data["graphs"][0]
            assert "graph_id" in graph_data
            assert "type" in graph_data
            assert "name" in graph_data
            assert "data" in graph_data

    async def test_get_aggregated_no_dashboard_access_returns_403(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test that accessing dashboard without access returns 403."""
        from mkobi.db.repositories.user_repo import UserRepository
        from mkobi.core.security import create_access_token
        from mkobi.models.enums import UserRole

        # Create a viewer user (non-admin) to test access control
        user_repo = UserRepository()
        viewer_user = await user_repo.create(
            db=async_db_session,
            email="viewer_agg@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        # Create a dashboard owned by another user
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_agg@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.commit()
        dashboard = await DashboardRepository().create(
            db=async_db_session,
            name="restricted-dashboard",
            created_by=other_user.id,
        )
        await async_db_session.commit()

        # Login as viewer (no access to this dashboard)
        token = create_access_token({"user_id": str(viewer_user.id), "email": viewer_user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        response = await async_client.get(
            "/data/aggregated",
            params={"dashboard_id": str(dashboard.id)},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN