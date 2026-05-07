"""Tests for authentication API endpoints."""

from fastapi import status
from httpx import AsyncClient

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
        repo = RegistrationRequestRepository
        request = await repo.get_by_email("new_user@example.com", async_db_session)
        if request:
            await repo.delete(request.id, async_db_session)
            await async_db_session.commit()
            await async_db_session.commit()

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
        repo = RegistrationRequestRepository
        request = await repo.get_by_email(email, async_db_session)
        if request:
            await repo.delete(request.id, async_db_session)
            await async_db_session.commit()


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
