"""Tests for resource-level access control on dashboard update/delete endpoints.

This module tests that users cannot modify or delete dashboards
unless they have explicit access grants or admin privileges.
"""

from fastapi import status
from httpx import AsyncClient

from mkobi.core.security import create_access_token
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import DashboardPermission, UserRole


class TestResourceAccessControlUpdate:
    """Tests for PUT /api/v1/dashboards/{id} resource-level access control."""

    async def test_no_access_user_cannot_update(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """User without dashboard access should get 403 on update."""
        # Create editor user (has editor role but no dashboard access)
        user_repo = UserRepository()
        editor_user = await user_repo.create(
            db=async_db_session,
            email="no_access_update@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create another user and their dashboard
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_update_owner@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_no_update_access",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Login as editor without access to this dashboard
        token = create_access_token(
            {"user_id": str(editor_user.id), "email": editor_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Editor has role but no access grant - should get 403
        response = await async_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "Hacked Name"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_admin_can_update_any_dashboard(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Admin should bypass resource-level checks on update."""
        # Create admin user
        user_repo = UserRepository()
        admin_user = await user_repo.create(
            db=async_db_session,
            email="admin_update_bypass@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        await async_db_session.flush()

        # Create another user and their dashboard (admin has no explicit access)
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_admin_update@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_admin_update_bypass",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Login as admin
        token = create_access_token(
            {"user_id": str(admin_user.id), "email": admin_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Admin should be able to update without explicit access
        response = await async_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "Admin Updated"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Admin Updated"

    async def test_user_with_edit_access_can_update(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """User with explicit edit access can update dashboard."""
        # Create editor user
        user_repo = UserRepository()
        editor_user = await user_repo.create(
            db=async_db_session,
            email="has_edit_access@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create another user and their dashboard
        other_user = await user_repo.create(
            db=async_db_session,
            email="dashboard_edit_owner@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_with_edit_access",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Grant edit access to editor user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=editor_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.flush()

        # Login as editor with access
        token = create_access_token(
            {"user_id": str(editor_user.id), "email": editor_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Editor with explicit access should succeed
        response = await async_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "Editor Updated"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Editor Updated"


class TestResourceAccessControlDelete:
    """Tests for DELETE /api/v1/dashboards/{id} resource-level access control."""

    async def test_no_access_user_cannot_delete(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """User without dashboard admin access should get 403 on delete."""
        # Create editor user (has required role but no admin access to dashboard)
        user_repo = UserRepository()
        editor_user = await user_repo.create(
            db=async_db_session,
            email="no_access_delete@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create another user and their dashboard
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_delete_owner@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_no_delete_access",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Grant edit access (not admin) to editor
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=editor_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.flush()

        # Login as editor with edit but not admin access
        token = create_access_token(
            {"user_id": str(editor_user.id), "email": editor_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Editor has role and edit access but not admin - should get 403
        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_admin_can_delete_any_dashboard(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Admin should bypass resource-level checks on delete."""
        # Create admin user
        user_repo = UserRepository()
        admin_user = await user_repo.create(
            db=async_db_session,
            email="admin_delete_bypass@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        await async_db_session.flush()

        # Create another user and their dashboard (admin has no explicit access)
        other_user = await user_repo.create(
            db=async_db_session,
            email="other_admin_delete@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_admin_delete_bypass",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Login as admin
        token = create_access_token(
            {"user_id": str(admin_user.id), "email": admin_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Admin should be able to delete without explicit access
        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_user_with_admin_access_can_delete(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """User with explicit admin access on dashboard can delete it."""
        # Create editor user
        user_repo = UserRepository()
        editor_user = await user_repo.create(
            db=async_db_session,
            email="admin_access_delete@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create another user and their dashboard
        other_user = await user_repo.create(
            db=async_db_session,
            email="dashboard_delete_owner@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_with_admin_access",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Grant admin access to editor user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=editor_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.ADMIN,
        )
        await async_db_session.flush()

        # Login as editor with admin access
        token = create_access_token(
            {"user_id": str(editor_user.id), "email": editor_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Editor with admin access on dashboard should succeed
        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestDashboardOwnerAccess:
    """Tests for dashboard owner access rights."""

    async def test_owner_can_update_own_dashboard(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Dashboard owner can update their own dashboard."""
        # Create editor user who will own the dashboard
        user_repo = UserRepository()
        owner_user = await user_repo.create(
            db=async_db_session,
            email="owner_update@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create dashboard owned by owner_user
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="owner_update_dashboard",
            created_by=owner_user.id,
        )
        await async_db_session.flush()

        # Grant admin access to owner (simulates owner access grant on creation)
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=owner_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.ADMIN,
        )
        await async_db_session.flush()

        # Login as owner
        token = create_access_token(
            {"user_id": str(owner_user.id), "email": owner_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Owner should be able to update
        response = await async_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "Owner Updated"},
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_owner_can_delete_own_dashboard(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Dashboard owner can delete their own dashboard."""
        # Create editor user who will own the dashboard
        user_repo = UserRepository()
        owner_user = await user_repo.create(
            db=async_db_session,
            email="owner_delete@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create dashboard owned by owner_user
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="owner_delete_dashboard",
            created_by=owner_user.id,
        )
        await async_db_session.flush()

        # Grant admin access to owner (simulates owner access grant on creation)
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=owner_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.ADMIN,
        )
        await async_db_session.flush()

        # Login as owner
        token = create_access_token(
            {"user_id": str(owner_user.id), "email": owner_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Owner has admin access to their dashboard, should be able to delete
        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestAccessControlListChecked:
    """Tests that access list is checked, not just role level."""

    async def test_role_not_enough_without_access(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Having editor role is not enough without explicit dashboard access."""
        # Create editor user
        user_repo = UserRepository()
        editor_user = await user_repo.create(
            db=async_db_session,
            email="role_not_enough@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        # Create dashboard owned by another user
        other_user = await user_repo.create(
            db=async_db_session,
            email="dashboard_role_test_owner@example.com",
            password_hash="hash",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="dashboard_role_test",
            created_by=other_user.id,
        )
        await async_db_session.flush()

        # Login as editor with no access to this dashboard
        token = create_access_token(
            {"user_id": str(editor_user.id), "email": editor_user.email}
        )
        async_client.headers.update({"Authorization": f"Bearer {token}"})

        # Having editor role alone should NOT be enough for update
        response = await async_client.put(
            f"/dashboards/{dashboard.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Same for delete (requires admin permission on dashboard)
        response = await async_client.delete(f"/dashboards/{dashboard.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN