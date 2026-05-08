"""Tests for dashboards API endpoints."""

from fastapi import status
from httpx import AsyncClient

from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.models.enums import DashboardPermission, UserRole


class TestGetMyDashboards:
    """Tests for GET /api/v1/dashboards/my endpoint."""

    async def test_get_my_dashboards(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test getting user's dashboards."""
        # Create dashboard and grant access to test_user
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="test_my_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Grant view access to test_user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.commit()

        response = await authenticated_client.get("/dashboards/my")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert any(d["id"] == str(dashboard.id) for d in data)


class TestGetDashboardDetail:
    """Tests for GET /api/v1/dashboards/{id} endpoint."""

    async def test_get_dashboard_detail(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test getting dashboard by ID with access."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="test_detail_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Grant access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.commit()

        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(dashboard.id)
        assert data["name"] == "test_detail_dashboard"

    async def test_get_dashboard_no_access(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test getting dashboard without access returns 404."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="test_no_access_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # No access granted
        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateDashboard:
    """Tests for POST /api/v1/dashboards endpoint."""

    async def test_create_dashboard_admin(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test creating dashboard as admin (success)."""
        response = await authenticated_client.post(
            "/dashboards/",
            json={
                "name": "new_dashboard",
                "description": "Test desc",
                "config": {"graph_types": ["bar"]},
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "new_dashboard"

    async def test_create_dashboard_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test creating dashboard without admin role (403)."""
        # Create viewer user
        from mkobi.db.repositories.user_repo import UserRepository

        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="viewer@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        # Login as viewer
        from mkobi.core.security import create_access_token

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        response = await async_client.post(
            "/dashboards/",
            json={"name": "forbidden_dashboard"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateDashboard:
    """Tests for PUT /api/v1/dashboards/{id} endpoint."""

    async def test_update_dashboard_admin(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test updating dashboard as admin (success)."""
        repo = DashboardRepository()
        access_repo = AccessRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="update_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Grant access
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        response = await authenticated_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "updated_name"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "updated_name"

    async def test_update_dashboard_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test updating dashboard without admin role (403)."""
        # Create viewer user and dashboard
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer2@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="update_forbidden_dashboard",
            created_by=user.id,
        )
        await async_db_session.commit()

        # Login as viewer
        from mkobi.core.security import create_access_token

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        response = await async_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "hacked_name"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteDashboard:
    """Tests for DELETE /api/v1/dashboards/{id} endpoint."""

    async def test_delete_dashboard_admin(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test deleting dashboard as admin (success)."""
        repo = DashboardRepository()
        access_repo = AccessRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="delete_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Grant access
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        response = await authenticated_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_dashboard_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test deleting dashboard without admin role (403)."""
        # Create viewer user and dashboard
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer3@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="delete_forbidden_dashboard",
            created_by=user.id,
        )
        await async_db_session.commit()

        # Login as viewer
        from mkobi.core.security import create_access_token

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAccessControl:
    """Tests for dashboard access control."""

    async def test_access_control_no_access(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test accessing dashboard without access returns 404."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="access_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # No access granted
        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_access_control_with_access(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test accessing dashboard with access returns 200."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="access_test_dashboard2",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Grant access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.commit()

        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_200_OK
