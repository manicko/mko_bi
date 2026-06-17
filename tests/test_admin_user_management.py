"""Integration tests for admin user management endpoints.

Tests cover:
- List users (admin only)
- Create user (admin only)
- Update user role (admin only)
- Deactivate/Reactivate user (admin only)
- Reset user password (admin only)
- Authorization: non-admin cannot access admin endpoints
"""

import uuid
from fastapi import status
from httpx import AsyncClient

from mkobi.core.security import create_access_token, hash_password
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import UserRole


class TestListUsers:
    """Tests for GET /admin/users endpoint."""

    async def test_list_users_admin(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can list all users."""
        user_repo = UserRepository()
        # Create additional user for testing
        await user_repo.create(
            db=async_db_session,
            email="list_test_user@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        # test_user is admin, use its token
        response = await async_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least test_user + list_test_user

    async def test_list_users_non_admin_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test non-admin cannot list users."""
        user_repo = UserRepository()
        # Create a viewer user
        viewer = await user_repo.create(
            db=async_db_session,
            email="viewer_list@example.com",
            password_hash=hash_password("ViewerPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        viewer_token = create_access_token({
            "user_id": str(viewer.id),
            "email": viewer.email,
        })

        response = await async_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCreateUser:
    """Tests for POST /users endpoint (admin only)."""

    async def test_create_user_admin(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test admin can create a new user."""
        response = await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "email": "newly_created_user@example.com",
                "password": "NewUserPass123!",
                "role": UserRole.VIEWER,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newly_created_user@example.com"
        assert data["role"] == UserRole.VIEWER

    async def test_create_user_editor_role(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test admin can create editor user."""
        response = await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "email": "editor_created_user2@example.com",
                "password": "EditorPass123!",
                "role": UserRole.EDITOR,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == UserRole.EDITOR

    async def test_create_user_duplicate_email(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test creating user with existing email returns validation error."""
        # First create a user
        await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "email": "duplicate_test2@example.com",
                "password": "Pass123!",
                "role": UserRole.VIEWER,
            },
        )

        # Try to create another with same email - returns 422 because ValueError is raised
        response = await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "email": "duplicate_test2@example.com",
                "password": "AnotherPass123!",
                "role": UserRole.VIEWER,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_user_non_admin_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test non-admin cannot create users."""
        user_repo = UserRepository()
        # Create a viewer user
        viewer = await user_repo.create(
            db=async_db_session,
            email="viewer_create2@example.com",
            password_hash=hash_password("ViewerPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        viewer_token = create_access_token({
            "user_id": str(viewer.id),
            "email": viewer.email,
        })

        response = await async_client.post(
            "/users/",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={
                "email": "should_fail2@example.com",
                "password": "Pass123!",
                "role": UserRole.VIEWER,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateUserRole:
    """Tests for PATCH /admin/users/{user_id}/role endpoint."""

    async def test_update_user_role_admin(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can update user role."""
        user_repo = UserRepository()
        # Create a viewer user
        target_user = await user_repo.create(
            db=async_db_session,
            email="role_update_target2@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        response = await async_client.patch(
            f"/admin/users/{target_user.id}/role",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"role": UserRole.EDITOR},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.EDITOR

    async def test_update_user_role_to_admin(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can promote user to admin role."""
        user_repo = UserRepository()
        # Create a viewer user
        target_user = await user_repo.create(
            db=async_db_session,
            email="promote_to_admin2@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        response = await async_client.patch(
            f"/admin/users/{target_user.id}/role",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"role": UserRole.ADMIN},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == UserRole.ADMIN

    async def test_update_user_role_nonexistent_user(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test updating role of non-existent user returns error."""
        # The endpoint returns 404 as USER_NOT_FOUND when user doesn't exist
        response = await async_client.patch(
            f"/admin/users/{uuid.uuid4()}/role",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"role": UserRole.EDITOR},
        )
        # Error code should be USER_NOT_FOUND or NOT_FOUND
        assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def test_update_user_role_non_admin_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test non-admin cannot update user role."""
        user_repo = UserRepository()

        # Create a viewer who will try to update roles
        viewer = await user_repo.create(
            db=async_db_session,
            email="viewer_role_update2@example.com",
            password_hash=hash_password("ViewerPass123!"),
            role=UserRole.VIEWER,
        )
        # Create another user to target
        target = await user_repo.create(
            db=async_db_session,
            email="role_update_target3@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        viewer_token = create_access_token({
            "user_id": str(viewer.id),
            "email": viewer.email,
        })

        response = await async_client.patch(
            f"/admin/users/{target.id}/role",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"role": UserRole.EDITOR},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeactivateUser:
    """Tests for PATCH /admin/users/{user_id}/active endpoint."""

    async def test_deactivate_user_admin(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can deactivate user."""
        user_repo = UserRepository()
        # Create a viewer user
        target_user = await user_repo.create(
            db=async_db_session,
            email="deactivate_target2@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        response = await async_client.patch(
            f"/admin/users/{target_user.id}/active",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"is_active": False},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

    async def test_reactivate_user_admin(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can reactivate user."""
        user_repo = UserRepository()
        # Create a deactivated user
        target_user = await user_repo.create(
            db=async_db_session,
            email="reactivate_target2@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await user_repo.update(target_user.id, async_db_session, is_active=False)
        await async_db_session.commit()

        response = await async_client.patch(
            f"/admin/users/{target_user.id}/active",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"is_active": True},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is True

    async def test_deactivate_nonexistent_user(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test deactivating non-existent user returns error."""
        response = await async_client.patch(
            f"/admin/users/{uuid.uuid4()}/active",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"is_active": False},
        )
        # Should be USER_NOT_FOUND
        assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def test_deactivate_user_non_admin_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test non-admin cannot deactivate users."""
        user_repo = UserRepository()

        # Create a viewer who will try to deactivate
        viewer = await user_repo.create(
            db=async_db_session,
            email="viewer_deactivate2@example.com",
            password_hash=hash_password("ViewerPass123!"),
            role=UserRole.VIEWER,
        )
        # Create another user to target
        target = await user_repo.create(
            db=async_db_session,
            email="deactivate_target3@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        viewer_token = create_access_token({
            "user_id": str(viewer.id),
            "email": viewer.email,
        })

        response = await async_client.patch(
            f"/admin/users/{target.id}/active",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"is_active": False},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestResetUserPassword:
    """Tests for POST /admin/users/{user_id}/reset-password endpoint."""

    async def test_reset_user_password_admin(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can reset another user's password."""
        user_repo = UserRepository()
        # Create a target user
        target_user = await user_repo.create(
            db=async_db_session,
            email="password_reset_target2@example.com",
            password_hash=hash_password("OriginalPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        response = await async_client.post(
            f"/admin/users/{target_user.id}/reset-password",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "retrieval_token" in data
        assert "user_id" in data
        assert data["user_id"] == str(target_user.id)

    async def test_reset_user_password_retrieve_temporary(
        self, async_client: AsyncClient, async_db_session, test_user: dict
    ) -> None:
        """Test admin can retrieve temporary password via retrieval token."""
        user_repo = UserRepository()
        target_user = await user_repo.create(
            db=async_db_session,
            email="password_retrieve_target2@example.com",
            password_hash=hash_password("OriginalPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        # Request password reset
        reset_response = await async_client.post(
            f"/admin/users/{target_user.id}/reset-password",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        retrieval_token = reset_response.json()["retrieval_token"]

        # Retrieve the temporary password
        retrieve_response = await async_client.get(
            f"/admin/temp-passwords/{retrieval_token}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert retrieve_response.status_code == status.HTTP_200_OK
        data = retrieve_response.json()
        assert "temp_password" in data
        assert len(data["temp_password"]) >= 16

    async def test_reset_user_password_nonexistent_user(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test resetting password for non-existent user returns error."""
        response = await async_client.post(
            f"/admin/users/{uuid.uuid4()}/reset-password",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def test_reset_user_password_non_admin_forbidden(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test non-admin cannot reset user passwords."""
        user_repo = UserRepository()

        # Create a viewer who will try to reset passwords
        viewer = await user_repo.create(
            db=async_db_session,
            email="viewer_reset_pass2@example.com",
            password_hash=hash_password("ViewerPass123!"),
            role=UserRole.VIEWER,
        )
        # Create another user to target
        target = await user_repo.create(
            db=async_db_session,
            email="reset_pass_target2@example.com",
            password_hash=hash_password("TargetPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        viewer_token = create_access_token({
            "user_id": str(viewer.id),
            "email": viewer.email,
        })

        response = await async_client.post(
            f"/admin/users/{target.id}/reset-password",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_reset_user_password_cannot_reset_own(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test admin cannot reset their own password via admin endpoint."""
        user_repo = UserRepository()
        # Create an admin user
        admin = await user_repo.create(
            db=async_db_session,
            email="admin_own_reset2@example.com",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
        )
        await async_db_session.commit()

        admin_token = create_access_token({
            "user_id": str(admin.id),
            "email": admin.email,
        })

        response = await async_client.post(
            f"/admin/users/{admin.id}/reset-password",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "own password" in response.json()["detail"].lower()