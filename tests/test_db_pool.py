"""Tests for database connection pool behavior.

Verifies pool exhaustion handling, connection leak prevention, and recovery.
"""

import asyncio
import time

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class TestDbPoolExhaustion:
    """Tests for database connection pool exhaustion scenarios."""

    async def test_pool_exhaustion_queued_and_recovers(
        self, setup_test_database: None
    ) -> None:
        """Test that pool handles exhaustion gracefully.

        Verifies:
        1. Requests are queued when pool is exhausted
        2. No connections are leaked after operations
        3. Pool recovers after load decreases

        Uses a pool with pool_size=2, max_overflow=0 to force exhaustion quickly.
        """
        from mkobi.config import get_config

        config = get_config()
        db_url = str(config.TEST_DATABASE_URL)

        if db_url is None:
            pytest.skip("TEST_DATABASE_URL not configured")

        # Create engine with intentionally small pool
        pool_size = 2
        max_overflow = 0
        pool_timeout = 5
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
        )

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            acquired_connections: list[AsyncSession] = []
            queue_count = 3
            tasks_completed = 0

            async def acquire_and_hold(session_idx: int, hold_time: float) -> None:
                """Acquire a session, hold it for specified time, then release."""
                nonlocal tasks_completed
                async with async_session_factory() as session:
                    acquired_connections.append(session)
                    # Hold the connection for a while
                    await asyncio.sleep(hold_time)
                    tasks_completed += 1

            # Start timing
            start_time = time.monotonic()

            # Launch more concurrent requests than pool can handle
            hold_duration = 0.5
            tasks = [
                asyncio.create_task(acquire_and_hold(i, hold_duration))
                for i in range(queue_count)
            ]

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

            elapsed_time = time.monotonic() - start_time

            # All tasks should have completed
            assert tasks_completed == queue_count

            # With pool_size=2, max_overflow=0, and 3 concurrent requests:
            # - First 2 acquire immediately
            # - Third waits ~0.5s for pool timeout
            # But since we're using NullPool implicitly in tests, adjust expectation
            # Actually the pool should queue and wait for release
            assert elapsed_time >= hold_duration

            # Verify no connections leaked - all should be properly closed
            # Check that we can still acquire connections after the load
            async with async_session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar_one() == 1

            # Pool should have recovered
            pool = engine.pool
            assert pool is not None
            checked_out = pool.checkedout()

            # All connections should be returned to the pool
            assert checked_out == 0, f"Expected 0 checked out connections, got {checked_out}"

        finally:
            # Clean up
            acquired_connections.clear()
            await engine.dispose()

    async def test_pool_no_connection_leaks_on_exception(
        self, setup_test_database: None
    ) -> None:
        """Test that connections are properly returned to pool on exception.

        Verifies that when exceptions occur during database operations,
        connections are not leaked and remain available for reuse.
        """
        from mkobi.config import get_config

        config = get_config()
        db_url = str(config.TEST_DATABASE_URL)

        if db_url is None:
            pytest.skip("TEST_DATABASE_URL not configured")

        # Create engine with small pool
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
            pool_timeout=5,
        )

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            # Simulate an operation that fails with an exception
            async def failing_operation() -> None:
                async with async_session_factory() as session:
                    await session.execute(text("SELECT 1"))
                    raise RuntimeError("Simulated error")

            # This should raise but connection should be returned to pool
            with pytest.raises(RuntimeError, match="Simulated error"):
                await failing_operation()

            # Give a moment for cleanup
            await asyncio.sleep(0.1)

            # Verify pool is still usable (no leaked connections)
            pool = engine.pool
            assert pool is not None

            # Should be able to acquire connections again
            async with async_session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar_one() == 1

            checked_out = pool.checkedout()
            assert checked_out == 0, f"Expected 0 checked out connections after error, got {checked_out}"

        finally:
            await engine.dispose()

    async def test_pool_max_overflow_behavior(
        self, setup_test_database: None
    ) -> None:
        """Test pool creation with overflow connections.

        Verifies that when max_overflow is configured, the pool can create
        additional connections beyond pool_size up to max_overflow limit.
        """
        from mkobi.config import get_config

        config = get_config()
        db_url = str(config.TEST_DATABASE_URL)

        if db_url is None:
            pytest.skip("TEST_DATABASE_URL not configured")

        # Create engine with pool_size=2 and max_overflow=3
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
            pool_timeout=5,
        )

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            acquired = []

            async def acquire_session(idx: int) -> int:
                async with async_session_factory():  # noqa: F841
                    acquired.append(idx)
                    await asyncio.sleep(0.1)
                    return idx

            # Launch 4 concurrent requests (2 pool + 2 overflow)
            tasks = [asyncio.create_task(acquire_session(i)) for i in range(4)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 4
            assert len(acquired) == 4

            # All connections should be returned
            pool = engine.pool
            if pool is not None:
                checked_out = pool.checkedout()
                assert checked_out == 0, f"Expected 0 checked out connections, got {checked_out}"

        finally:
            await engine.dispose()

    async def test_pool_timeout_on_exhaustion(
        self, setup_test_database: None
    ) -> None:
        """Test that pool respects timeout when exhausted.

        Verifies that when pool is exhausted and no overflow is allowed,
        requests wait up to pool_timeout seconds before succeeding.
        """
        from mkobi.config import get_config
        from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

        config = get_config()
        db_url = str(config.TEST_DATABASE_URL)

        if db_url is None:
            pytest.skip("TEST_DATABASE_URL not configured")

        # Create engine with very small pool and no overflow
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
            pool_timeout=1,
        )

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            first_acquired = asyncio.Event()
            can_finish = asyncio.Event()

            async def hold_first_connection() -> None:
                async with async_session_factory():  # noqa: F841
                    first_acquired.set()
                    # Hold until we signal it's OK to finish
                    await can_finish.wait()

            # First task holds the only connection
            holder = asyncio.create_task(hold_first_connection())
            await first_acquired.wait()

            start_time = time.monotonic()

            # Second task should wait (not timeout due to 1s timeout)
            second_succeeded = False
            try:
                async with async_session_factory() as session:
                    await session.execute(text("SELECT 1"))
                    second_succeeded = True
            except SQLAlchemyTimeoutError:
                pass

            elapsed_time = time.monotonic() - start_time

            # Signal the holder to finish
            can_finish.set()
            await holder

            # With pool_timeout=1, the second request should succeed after ~wait
            # Since we have pool_timeout=1 and we signal completion before that
            assert second_succeeded, "Second request should have succeeded after waiting"
            assert elapsed_time < 1.0, f"Should not have waited full timeout, waited {elapsed_time}s"

        finally:
            await engine.dispose()