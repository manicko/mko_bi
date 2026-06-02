"""Integration tests for force_password_change flag in login response.

Tests verify that the login response includes the force_password_change boolean field
and that it correctly reflects the user's state.
"""

from httpx import AsyncClient


class TestForcePasswordChangeBackend:
    """Test force_password_change flag in login response."""

    async def test_login_includes_force_password_change_flag(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Login response should include force_password_change field."""
        response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "force_password_change" in body["user"]
        assert isinstance(body["user"]["force_password_change"], bool)

    async def test_user_with_force_password_change_true(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """User with force_password_change=True should see True in login response."""
        from mkobi.core.security import hash_password
        from mkobi.db.repositories.user_repo import UserRepository
        from mkobi.models.enums import UserRole

        user_repo = UserRepository()

        # Create a user with force_password_change=True (simulating approved registration)
        user = await user_repo.create(
            db=async_db_session,
            email="force_change_true_test@example.com",
            password_hash=hash_password("TempPass123!"),
            role=UserRole.VIEWER,
        )
        # Manually set the flag to simulate approved registration state
        await user_repo.update(
            user.id, async_db_session,
            force_password_change=True,
        )
        await async_db_session.commit()

        # Login with the user
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "force_change_true_test@example.com",
                "password": "TempPass123!",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["force_password_change"] is True

    async def test_normal_user_has_force_password_change_false(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Normal user should have force_password_change=False in login response."""
        response = await async_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["force_password_change"] is False

    async def test_login_includes_force_password_change_after_admin_reset(
        self, async_client: AsyncClient, async_db_session
    ) -> None:
        """User whose password was reset by admin should see force_password_change=True."""
        from mkobi.core.security import create_access_token, hash_password
        from mkobi.db.repositories.user_repo import UserRepository
        from mkobi.models.enums import UserRole

        user_repo = UserRepository()

        # Create admin user for testing
        admin_user = await user_repo.create(
            db=async_db_session,
            email="admin_reset_check@example.com",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
        )
        await async_db_session.commit()

        admin_token = create_access_token({
            "user_id": str(admin_user.id),
            "email": admin_user.email,
        })

        # Create target user for password reset
        target_user = await user_repo.create(
            db=async_db_session,
            email="reset_target_check@example.com",
            password_hash=hash_password("OriginalPass123!"),
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        # Admin resets target user's password
        reset_response = await async_client.post(
            f"/admin/users/{target_user.id}/reset-password",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert reset_response.status_code == 200
        temp_password = reset_response.json()["temp_password"]

        # Target user logs in with temp password
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": "reset_target_check@example.com",
                "password": temp_password,
            },
        )
        assert login_response.status_code == 200
        body = login_response.json()
        assert body["user"]["force_password_change"] is True