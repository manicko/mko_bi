"""Tests for dashboard access cascade delete behavior."""

from uuid import uuid4

from httpx import AsyncClient

from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import DashboardPermission, UserRole


class TestDashboardAccessCascadeDelete:
    """Tests for cascade delete of access records when dashboard is deleted."""

    async def test_dashboard_access_cascade_delete(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test that access records are deleted when dashboard is deleted."""

        # Create a second user to grant access
        user_repo = UserRepository()
        other_user = await user_repo.create(
            db=async_db_session,
            email=f"access_user_{uuid4().hex[:8]}@example.com",
            password_hash="hash",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        # Create dashboard
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name=f"cascade-test-dashboard-{uuid4().hex[:8]}",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant access to other_user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=other_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

        # Verify access exists before deletion
        access_before = await access_repo.get_by_dashboard(dashboard.id, async_db_session)
        assert len(access_before) >= 1, "Access record should exist before deletion"
        access_for_user = await access_repo.check_access(
            other_user.id, dashboard.id, async_db_session
        )
        assert access_for_user == DashboardPermission.VIEW.value

        # Delete the dashboard via API (as admin)
        response = await authenticated_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == 204, "Dashboard deletion should succeed"

        # Verify access record is also deleted (no orphaned records)
        access_after = await access_repo.get_by_dashboard(dashboard.id, async_db_session)
        assert len(access_after) == 0, "Access records should be deleted with dashboard"

        access_after_for_user = await access_repo.check_access(
            other_user.id, dashboard.id, async_db_session
        )
        assert access_after_for_user is None, "User should no longer have access after dashboard deletion"