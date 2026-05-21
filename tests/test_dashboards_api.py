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
            name="test-my-dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant view access to test_user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

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
            name="test-detail-dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(dashboard.id)
        assert data["name"] == "test-detail-dashboard"

    async def test_get_dashboard_no_access(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test getting dashboard without access returns 403 for non-admin."""
        # Create a viewer user (non-admin) to test access control
        from mkobi.db.repositories.user_repo import UserRepository
        from mkobi.core.security import create_access_token

        user_repo = UserRepository()
        viewer_user = await user_repo.create(
            db=async_db_session,
            email="viewer_no_access@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        # Create a dashboard owned by another user
        repo = DashboardRepository()
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_owner@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()
        dashboard = await repo.create(
            db=async_db_session,
            name="test-no-access-dashboard",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Login as viewer (no access to this dashboard)
        token = create_access_token({"user_id": str(viewer_user.id), "email": viewer_user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        # No access granted - should return 403 Forbidden
        response = await async_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_dashboard_not_found(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test getting non-existent dashboard returns 404."""
        from uuid import uuid4
        from mkobi.db.repositories.user_repo import UserRepository
        from mkobi.core.security import create_access_token

        user_repo = UserRepository()
        viewer_user = await user_repo.create(
            db=async_db_session,
            email="viewer_not_found@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        # Login as viewer
        token = create_access_token({"user_id": str(viewer_user.id), "email": viewer_user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        # Request non-existent dashboard
        fake_id = uuid4()
        response = await async_client.get(f"/dashboards/{fake_id}")
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
                "name": "new-dashboard",
                "description": "Test desc",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "new-dashboard"
        assert data["description"] == "Test desc"

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
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        response = await async_client.post(
            "/dashboards/",
            json={"name": "forbidden-dashboard"},
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
            name="update-test-dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant access
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.flush()

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
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="update-forbidden-dashboard",
            created_by=user.id,
        )
        await async_db_session.flush()

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
            name="delete-test-dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant access
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.flush()

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
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="delete-forbidden-dashboard",
            created_by=user.id,
        )
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token

        token = create_access_token({"user_id": str(user.id), "email": user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAccessControl:
    """Tests for dashboard access control."""

    async def test_access_control_no_access(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test accessing dashboard without access returns 403 for non-admin."""
        # Create a viewer user (non-admin) to test access control
        from mkobi.db.repositories.user_repo import UserRepository
        from mkobi.core.security import create_access_token

        user_repo = UserRepository()
        viewer_user = await user_repo.create(
            db=async_db_session,
            email="viewer_no_access2@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        # Create a dashboard owned by another user
        repo = DashboardRepository()
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_owner2@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()
        dashboard = await repo.create(
            db=async_db_session,
            name="access-test-dashboard",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Login as viewer (no access to this dashboard)
        token = create_access_token({"user_id": str(viewer_user.id), "email": viewer_user.email})
        async_client.headers["Authorization"] = f"Bearer {token}"

        # No access granted - should return 403 Forbidden
        response = await async_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_access_control_with_access(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test accessing dashboard with access returns 200."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="access-test-dashboard2",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_200_OK


class TestAdminBypass:
    """Tests for admin bypass functionality."""

    async def test_admin_sees_all_dashboards(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test that admin user sees all dashboards without explicit access."""
        # Create another user and their dashboard (admin has no explicit access)
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_user_admin_test@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        repo = DashboardRepository()
        other_dashboard = await repo.create(
            db=async_db_session,
            name="other-user-dashboard",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Admin requests their dashboards - should include dashboard they have no access to
        response = await authenticated_client.get("/dashboards/my")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Admin should see this dashboard even without explicit access
        assert any(d["id"] == str(other_dashboard.id) for d in data)

    async def test_admin_can_access_any_dashboard(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test that admin can access any dashboard by direct URL."""
        # Create another user and their dashboard (admin has no explicit access)
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_user_detail_test@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="dashboard_for_admin_bypass",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Admin requests dashboard they have no explicit access to
        response = await authenticated_client.get(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(dashboard.id)
        assert data["name"] == "dashboard_for_admin_bypass"
