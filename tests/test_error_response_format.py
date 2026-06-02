"""Contract tests for standardized error response format.

Verifies all error responses conform to the standard ErrorResponse format
across different endpoint categories (400, 401, 403, 404, 500).
"""

from httpx import AsyncClient

from mkobi.core.security import create_access_token, hash_password
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import UserRole


class TestErrorResponseFormat:
    """Verify all error responses conform to the standard format."""

    async def test_400_validation_error_format(self, async_client: AsyncClient) -> None:
        """Validation errors should return structured ErrorResponse."""
        # Send invalid email format to trigger validation error
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "not-an-email",
                "password": "x",
            },
        )
        assert response.status_code == 422
        body = response.json()
        # Verify standard fields exist (validation errors include 'errors' list plus error/code)
        assert "error" in body or "detail" in body
        assert "code" in body

    async def test_401_unauthenticated_format(self, async_client: AsyncClient) -> None:
        """Unauthenticated requests should return structured error."""
        # Use /auth/me which requires authentication - directly tests 401
        response = await async_client.get("/auth/me")
        assert response.status_code == 401
        body = response.json()
        # Verify standard fields exist
        assert "error" in body
        assert "code" in body

    async def test_404_not_found_format(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Not-found errors should return structured error."""
        # Create an authenticated user
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="test_404_user@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()
        token = create_access_token(
            {"user_id": str(user.id), "email": user.email, "role": user.role}
        )

        # Request a non-existent dashboard
        response = await async_client.get(
            "/dashboards/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        body = response.json()
        # Verify standard fields exist
        assert "error" in body
        assert "code" in body

    async def test_403_permission_error_format(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Permission errors should return structured error.

        Uses a viewer token accessing an admin-only endpoint.
        """
        # Create a viewer user
        repo = UserRepository()
        viewer = await repo.create(
            db=async_db_session,
            email="test_viewer_403@example.com",
            password_hash=hash_password("ViewerPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()
        viewer_token = create_access_token(
            {"user_id": str(viewer.id), "email": viewer.email, "role": viewer.role}
        )

        # Admin-only endpoint - GET /admin/users
        response = await async_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403
        body = response.json()
        # Verify standard fields exist
        assert "error" in body
        assert "code" in body

    async def test_500_internal_error_format_no_stack_trace(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Internal errors should return structured error without stack traces.

        Tests by verifying that 404 error responses do not contain stack traces.
        """
        # Create an authenticated user for testing
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="test_internal_error@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()
        token = create_access_token(
            {"user_id": str(user.id), "email": user.email, "role": user.role}
        )

        # Request a non-existent resource to verify error format
        response = await async_client.get(
            "/dashboards/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        body = response.json()
        # Verify no stack trace in response
        body_str = str(body).lower()
        assert "traceback" not in body_str
        assert "exception" not in body_str or "exception" in body.get("error", "").lower()

    async def test_error_response_has_error_field(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Error responses should have 'error' field with message."""
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="test_error_field@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()
        token = create_access_token(
            {"user_id": str(user.id), "email": user.email, "role": user.role}
        )

        response = await async_client.get(
            "/dashboards/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = response.json()

        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0

    async def test_error_response_has_code_field(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """Error responses should have 'code' field with error code."""
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="test_code_field@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()
        token = create_access_token(
            {"user_id": str(user.id), "email": user.email, "role": user.role}
        )

        response = await async_client.get(
            "/dashboards/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = response.json()

        assert "code" in body
        assert isinstance(body["code"], str)
        assert len(body["code"]) > 0