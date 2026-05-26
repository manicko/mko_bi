"""Tests for authentication API endpoints."""

from fastapi import status
from httpx import AsyncClient

from mkobi.core.security import create_refresh_token
from mkobi.db.repositories.registration_request_repo import (
    RegistrationRequestRepository,
)
from mkobi.models.enums import UserRole


class TestLogin:
    """Tests for login endpoint."""

    async def test_login_success(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test successful login with correct credentials."""
        response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Verify user data is included in response
        assert "user" in data
        assert data["user"]["email"] == test_user["email"]
        assert "id" in data["user"]
        assert "role" in data["user"]
        assert "display_name" in data["user"]
        assert "created_at" in data["user"]

    async def test_login_wrong_password(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test login with incorrect password."""
        response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_nonexistent_user(self, async_client: AsyncClient) -> None:
        """Test login with non-existent user email."""
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRegisterRequest:
    """Tests for registration request endpoint."""

    async def test_register_request_success(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test successful registration request creation."""
        response = await async_client.post(
            "/auth/register-request",
            json={"email": "new_user@example.com"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Request submitted"
        assert "id" in data

        # Cleanup
        repo = RegistrationRequestRepository()
        request = await repo.get_by_email("new_user@example.com", async_db_session)
        if request:
            await repo.delete(request.id, async_db_session)
            await async_db_session.flush()

    async def test_register_request_duplicate(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Test registration request with duplicate email."""
        email = "duplicate@example.com"

        # First request
        await async_client.post(
            "/auth/register-request",
            json={"email": email},
        )

        # Second request (duplicate)
        response = await async_client.post(
            "/auth/register-request",
            json={"email": email},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        # Cleanup
        repo = RegistrationRequestRepository()
        request = await repo.get_by_email(email, async_db_session)
        if request:
            await repo.delete(request.id, async_db_session)
            await async_db_session.flush()


class TestGetMe:
    """Tests for get current user endpoint."""

    async def test_get_me_authenticated(
        self, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test getting current user with valid token."""
        response = await authenticated_client.get("/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["role"] == UserRole.ADMIN

    async def test_get_me_unauthenticated(self, async_client: AsyncClient) -> None:
        """Test getting current user without token (401)."""
        response = await async_client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:
    """Tests for logout endpoint."""

    async def test_logout_authenticated(
        self, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test logout with valid token."""
        response = await authenticated_client.post("/auth/logout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logged out successfully"
        # Verify cookie header is present (setting cookie for deletion)
        assert "set-cookie" in response.headers or "refresh_token" in str(
            response.headers.get("set-cookie", "")
        )

    async def test_logout_unauthenticated(self, async_client: AsyncClient) -> None:
        """Test logout without token (401)."""
        response = await async_client.post("/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshToken:
    """Tests for token refresh endpoint."""

    async def test_refresh_missing_cookie(self, async_client: AsyncClient) -> None:
        """Test refresh without cookie returns 401."""
        response = await async_client.post("/auth/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    async def test_refresh_invalid_token(self, async_client: AsyncClient) -> None:
        """Test refresh with invalid token returns 401."""
        response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": "invalid.token.here"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    async def test_refresh_valid_token(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test refresh with valid token returns new access token."""
        # Create a valid refresh token for the test user
        refresh_token = create_refresh_token(
            data={
                "sub": str(test_user["id"]),
                "email": test_user["email"],
                "role": test_user["role"],
            }
        )

        response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": refresh_token},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_nonexistent_user(
        self, async_client: AsyncClient
    ) -> None:
        """Test refresh with token for non-existent user returns 401."""
        # Create a refresh token for a user that doesn't exist
        refresh_token = create_refresh_token(
            data={
                "sub": "00000000-0000-0000-0000-000000000001",
                "email": "nonexistent@example.com",
                "role": "viewer",
            }
        )

        response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": refresh_token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "User not found" in data["detail"]
