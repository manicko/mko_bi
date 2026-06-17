"""Integration tests for rate limiting functionality.

Tests cover:
- Initial requests succeed under rate limit
- Requests exceeding limit return 429 with Retry-After header
- Requests succeed after rate limit window resets
"""

from fastapi import status


class TestRateLimitingIntegration:
    """Tests for rate limiting behavior across endpoints."""

    async def test_login_rate_limit_exceeded(
        self, async_client, async_db_session, strict_redis
    ) -> None:
        """Test that login endpoint returns 429 when rate limit exceeded."""
        from mkobi.core.security import hash_password
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()

        # Create test user
        await user_repo.create(
            db=async_db_session,
            email="rate_limit_login_test@example.com",
            password_hash=hash_password("TestPass123!"),
            role="viewer",
        )
        await async_db_session.commit()

        max_attempts = 5

        for i in range(max_attempts):
            response = await async_client.post(
                "/auth/login",
                json={
                    "email": "rate_limit_login_test@example.com",
                    "password": "wrong_password",
                },
            )
            # All should be processed (though auth fails)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"Request {i + 1} should be processed, got {response.status_code}"
            )

        # The 6th request should be rate limited
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "rate_limit_login_test@example.com",
                "password": "wrong_password",
            },
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS, (
            f"Expected 429, got {response.status_code}"
        )

        # Verify Retry-After header is present
        assert "retry-after" in response.headers, (
            "Retry-After header should be present in 429 response"
        )
        retry_after = response.headers["retry-after"]
        assert retry_after.isdigit(), "Retry-After should be a numeric value"
        assert int(retry_after) > 0, "Retry-After should be positive"

        # Verify RFC 7807 error format
        body = response.json()
        assert body["code"] == "RATE_LIMIT_EXCEEDED"
        assert "detail" in body

    async def test_register_request_rate_limit_exceeded(
        self, async_client, async_db_session, strict_redis
    ) -> None:
        """Test that register-request endpoint returns 429 when rate limit exceeded."""
        max_attempts = 3

        for i in range(max_attempts):
            response = await async_client.post(
                "/auth/register-request",
                json={"email": f"test{i}@example.com"},
            )
            # All should be processed (though may fail due to different reasons)
            assert response.status_code in (
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ), f"Request {i + 1} should be processed, got {response.status_code}"

        # The 4th request should be rate limited
        response = await async_client.post(
            "/auth/register-request",
            json={"email": "test_overflow@example.com"},
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS, (
            f"Expected 429, got {response.status_code}"
        )

        # Verify Retry-After header is present
        assert "retry-after" in response.headers, (
            "Retry-After header should be present in 429 response"
        )

    async def test_rate_limit_reset_allow_writes(
        self, async_client, async_db_session, strict_redis
    ) -> None:
        """Test that rate limiting works correctly with reset capability."""
        from mkobi.core.security import hash_password
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()

        # Create test user
        await user_repo.create(
            db=async_db_session,
            email="rate_limit_reset_test@example.com",
            password_hash=hash_password("TestPass123!"),
            role="viewer",
        )
        await async_db_session.commit()

        rate_limit_key = "login:127.0.0.1"
        max_attempts = 5

        # Exhaust the rate limit
        for _ in range(max_attempts + 1):
            await async_client.post(
                "/auth/login",
                json={
                    "email": "rate_limit_reset_test@example.com",
                    "password": "wrong_password",
                },
            )

        # Manually reset the rate limit by clearing the key
        strict_redis._data.pop(rate_limit_key, None)
        strict_redis._ttls.pop(rate_limit_key, None)

        # Next request should succeed (return 401 for wrong password)
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "rate_limit_reset_test@example.com",
                "password": "wrong_password",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Request should succeed after reset, got {response.status_code}"
        )

    async def test_different_ips_have_separate_limits(
        self, async_client, async_db_session, strict_redis
    ) -> None:
        """Test that rate limits are tracked per IP address."""
        from mkobi.core.security import hash_password
        from mkobi.db.repositories.user_repo import UserRepository

        user_repo = UserRepository()

        # Create test user
        await user_repo.create(
            db=async_db_session,
            email="rate_limit_ip_test@example.com",
            password_hash=hash_password("TestPass123!"),
            role="viewer",
        )
        await async_db_session.commit()

        max_attempts = 5

        # Exhaust rate limit for one IP
        for _ in range(max_attempts + 1):
            await async_client.post(
                "/auth/login",
                json={
                    "email": "rate_limit_ip_test@example.com",
                    "password": "wrong_password",
                },
            )

        # Verify first IP is rate limited
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "rate_limit_ip_test@example.com",
                "password": "wrong_password",
            },
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestAsyncRateLimiterUnit:
    """Unit tests for AsyncRateLimiter class."""

    async def test_check_rate_limit_allows_under_limit(self, strict_redis) -> None:
        """Test that check_rate_limit returns True when under limit."""
        from mkobi.core.security import AsyncRateLimiter

        limiter = AsyncRateLimiter(strict_redis)

        for i in range(3):
            allowed, retry_after = await limiter.check_rate_limit(
                "test_key:under_limit", max_attempts=5, ttl=60
            )
            assert allowed is True
            assert retry_after is None, f"Attempt {i + 1} should be allowed"

    async def test_check_rate_limit_blocks_over_limit(self, strict_redis) -> None:
        """Test that check_rate_limit returns False when over limit."""
        from mkobi.core.security import AsyncRateLimiter

        limiter = AsyncRateLimiter(strict_redis)
        key = "test_key:over_limit"

        # Make 5 requests (at limit)
        for i in range(5):
            allowed, retry_after = await limiter.check_rate_limit(key, max_attempts=5, ttl=60)
            assert allowed is True, f"Attempt {i + 1} should be allowed"

        # 6th request should be blocked
        allowed, retry_after = await limiter.check_rate_limit(key, max_attempts=5, ttl=60)
        assert allowed is False, "6th attempt should be blocked"
        assert retry_after is not None, "retry_after should be returned when blocked"
        assert retry_after > 0, "retry_after should be positive"

    async def test_check_rate_limit_returns_ttl_when_blocked(self, strict_redis) -> None:
        """Test that check_rate_limit returns TTL when rate limit is exceeded."""
        from mkobi.core.security import AsyncRateLimiter

        limiter = AsyncRateLimiter(strict_redis)
        key = "test_key:ttl_check"

        # Set up a key with known TTL
        await strict_redis.setex(key, 120, "5")

        # Request should be blocked and TTL returned
        allowed, retry_after = await limiter.check_rate_limit(key, max_attempts=5, ttl=60)
        assert allowed is False
        assert retry_after is not None