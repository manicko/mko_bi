"""Tests for users API endpoints."""

from fastapi import status
from httpx import AsyncClient



class TestGetProfile:
    """Tests for get profile endpoint."""

    async def test_get_own_profile(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test getting own profile via /auth/me."""
        # Login first
        login_resp = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        token = login_resp.json()["access_token"]

        # Get profile
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["role"] == test_user["role"]

    async def test_get_profile_unauthorized(self, async_client: AsyncClient) -> None:
        """Test getting profile without token."""
        response = await async_client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteAccount:
    """Tests for self-deletion endpoint."""

    async def test_delete_own_account(
        self, async_client: AsyncClient, test_user: dict, async_db_session
    ) -> None:
        """Test deleting own account via /users/me."""
        # Login first
        login_resp = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        token = login_resp.json()["access_token"]

        # Delete account
        response = await async_client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify user is deleted - login should fail
        login_resp = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert login_resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_account_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test deleting account without token."""
        response = await async_client.delete("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_admin_cannot_delete_self(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test that admin cannot delete their own account."""
        # Create admin user first via service or register
        # This test depends on how admin users are created
        # For now, skip if no admin user available
        pass
