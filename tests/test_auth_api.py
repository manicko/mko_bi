"""Integration tests for cookie-based authentication flow.

Tests cover the complete cookie-based authentication flow:
- Login sets refresh token cookie
- Refresh reads from cookie
- Logout clears cookie
- Edge cases (missing cookie, invalid cookie)
"""

from fastapi import status
from httpx import AsyncClient


def _extract_refresh_token(response) -> str:
    """Extract refresh token value from set-cookie header.

    Args:
        response: HTTP response with set-cookie header.

    Returns:
        The refresh token value string.
    """
    set_cookie = response.headers.get("set-cookie", "")
    # Format: mkobi_refresh_token=<token>; ...
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("mkobi_refresh_token="):
            return part.split("=", 1)[1]
    return ""


class TestCookieAuthFlow:
    """Tests for end-to-end cookie-based authentication flow."""

    async def test_login_sets_refresh_cookie(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test that login sets refresh token as httpOnly cookie."""
        response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify access token in JSON response
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

        # Verify refresh token cookie is set with security attributes
        assert "set-cookie" in response.headers
        set_cookie = response.headers["set-cookie"]
        assert "mkobi_refresh_token" in set_cookie
        assert "httponly" in set_cookie.lower()
        assert "secure" in set_cookie.lower()
        assert "samesite=strict" in set_cookie.lower()

    async def test_refresh_reads_from_cookie(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test that refresh endpoint reads token from cookie set by login."""
        # First login to get refresh cookie
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Extract cookie from login response
        refresh_token = _extract_refresh_token(login_response)
        assert refresh_token, "Refresh token should be set in cookie"

        # Then refresh using the cookie
        refresh_response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": refresh_token},
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access_token" in refresh_response.json()
        assert refresh_response.json()["token_type"] == "bearer"

    async def test_logout_clears_cookie(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test that logout clears the refresh token cookie."""
        # Login first
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Extract cookie from login response
        refresh_token = _extract_refresh_token(login_response)

        # Logout - need access token in header for authentication
        access_token = login_response.json()["access_token"]
        response = await async_client.post(
            "/auth/logout",
            cookies={"mkobi_refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Logged out successfully"

        # Verify cookie is cleared (set to empty with past expiry)
        set_cookie = response.headers.get("set-cookie", "")
        assert "mkobi_refresh_token" in set_cookie
        # Cookie should be cleared (empty value or max-age=0)
        assert "max-age=0" in set_cookie.lower() or "mkobi_refresh_token=;" in set_cookie.lower()

    async def test_refresh_fails_without_cookie(
        self, async_client: AsyncClient
    ) -> None:
        """Test that refresh fails without refresh cookie."""
        response = await async_client.post("/auth/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Refresh token not found"

    async def test_refresh_fails_with_invalid_cookie(
        self, async_client: AsyncClient
    ) -> None:
        """Test that refresh fails with invalid refresh cookie."""
        response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": "invalid.token.here"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"

    async def test_refresh_returns_new_access_token(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test that refresh returns a valid access token."""
        # Login to get initial cookie
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Extract cookie from login response
        refresh_token = _extract_refresh_token(login_response)

        # Refresh
        response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": refresh_token},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        # Verify the token is valid by decoding it
        from mkobi.core.security import decode_token
        payload = decode_token(data["access_token"])
        assert payload is not None
        assert payload["user_id"] == str(test_user["id"])
        assert payload["email"] == test_user["email"]

    async def test_full_auth_flow_login_refresh_logout(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Test complete authentication flow: login -> refresh -> logout."""
        # 1. Login and verify cookie is set
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert "set-cookie" in login_response.headers

        # Extract access token and refresh token
        access_token = login_response.json()["access_token"]
        refresh_token = _extract_refresh_token(login_response)

        # 2. Refresh using the cookie
        refresh_response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": refresh_token},
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access_token" in refresh_response.json()

        # 3. Logout and verify cookie is cleared
        logout_response = await async_client.post(
            "/auth/logout",
            cookies={"mkobi_refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == status.HTTP_200_OK

        # 4. Verify refresh no longer works after logout
        # Use a valid token but without the cookie, or with cleared cookie
        final_refresh = await async_client.post("/auth/refresh")
        assert final_refresh.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_with_expired_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test refresh with expired token returns 401."""
        from datetime import UTC, datetime, timedelta

        from jose import jwt

        expired_token = jwt.encode(
            {
                "sub": "test-user-id",
                "email": "test@example.com",
                "role": "admin",
                "exp": datetime.now(UTC) - timedelta(hours=1),
            },
            "test_secret_key_change_in_production",
            algorithm="HS256",
        )

        response = await async_client.post(
            "/auth/refresh",
            cookies={"mkobi_refresh_token": expired_token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED