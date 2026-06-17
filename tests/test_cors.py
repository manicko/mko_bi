"""Tests for CORS preflight (OPTIONS) requests."""

import pytest
from httpx import AsyncClient, ASGITransport

from mkobi.app import create_app


class TestCORSPreflight:
    """Tests for CORS preflight request handling."""

    @pytest.fixture
    async def cors_client(self) -> AsyncClient:
        """Create HTTP client for CORS testing without database dependency.

        CORS middleware operates independently of database, so we create
        a fresh app instance and client without DB setup.
        """
        import os
        os.environ.setdefault("ENV", "test")
        os.environ.setdefault("JWT__SECRET_KEY", "test_secret_key_change_in_production")

        from mkobi.config import clear_config_cache
        clear_config_cache()

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client

    async def test_cors_preflight_returns_200(self, cors_client: AsyncClient) -> None:
        """OPTIONS request returns 200 status code."""
        response = await cors_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200

    async def test_cors_preflight_has_allow_origin_header(
        self, cors_client: AsyncClient
    ) -> None:
        """OPTIONS response includes Access-Control-Allow-Origin header."""
        response = await cors_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers

    async def test_cors_preflight_allow_methods_includes_get_post_put_delete(
        self, cors_client: AsyncClient
    ) -> None:
        """OPTIONS response includes GET, POST, PUT, DELETE in Allow-Methods."""
        response = await cors_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_methods = response.headers.get("access-control-allow-methods", "")
        methods = [m.strip() for m in allow_methods.split(",")]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    async def test_cors_preflight_allow_headers_includes_auth_and_content_type(
        self, cors_client: AsyncClient
    ) -> None:
        """OPTIONS response includes Authorization and Content-Type in Allow-Headers."""
        response = await cors_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
        allow_headers = response.headers.get("access-control-allow-headers", "")
        headers = [h.strip() for h in allow_headers.split(",")]
        assert "Authorization" in headers
        assert "Content-Type" in headers

    async def test_cors_preflight_allow_credentials(
        self, cors_client: AsyncClient
    ) -> None:
        """OPTIONS response includes Access-Control-Allow-Credentials header."""
        response = await cors_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"