"""Common fixtures for tests."""
import os
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# Set required environment variables before ANY mkobi module imports
# This must be at the very top of this file before other imports
# Use setdefault to allow Docker Compose env vars to take precedence in containers
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE__HOST", "localhost")
os.environ.setdefault("DATABASE__PORT", "5432")
os.environ.setdefault("DATABASE__DBNAME", "bidb_test")
os.environ.setdefault("DATABASE__USER", "postgres")
os.environ.setdefault("DATABASE__PASSWORD", "1234")
os.environ.setdefault("DATABASE__ADMIN_PASSWORD", "1234")
os.environ.setdefault("DATABASE__TEST_DBNAME", "bidb_test")
os.environ.setdefault("JWT__SECRET_KEY", "test_secret_key_change_in_production")
os.environ.setdefault("REDIS__HOST", "localhost")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("RECREATE_TEST_DB", "true")


def pytest_load_initial_conftests(early_config, parser, args):
    """Pytest hook that runs before conftest.py is fully loaded.
    
    This ensures environment variables are set before ANY test modules
    are imported during collection.
    """
    # Use setdefault to allow Docker Compose env vars to take precedence in containers
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("DATABASE__HOST", "localhost")
    os.environ.setdefault("DATABASE__PORT", "5432")
    os.environ.setdefault("DATABASE__DBNAME", "bidb_test")
    os.environ.setdefault("DATABASE__USER", "postgres")
    os.environ.setdefault("DATABASE__PASSWORD", "1234")
    os.environ.setdefault("DATABASE__TEST_DBNAME", "bidb_test")
    os.environ.setdefault("JWT__SECRET_KEY", "test_secret_key_change_in_production")
    os.environ.setdefault("REDIS__HOST", "localhost")
    os.environ.setdefault("REDIS__PORT", "6379")
    os.environ.setdefault("RECREATE_TEST_DB", "true")

# Import config module - this will create the singleton with test env vars
from mkobi.config import clear_config_cache, get_config, Settings  # noqa: E402, F401

# Clear any cached config from previous imports and initialize with test env vars
clear_config_cache()
_config = get_config()

# Validate that JWT secret key is set before proceeding
if _config.jwt.secret_key is None:
    raise RuntimeError(
        "JWT__SECRET_KEY must be set in environment before tests run. "
        f"Current value: {repr(_config.jwt.secret_key)}"
    )


def pytest_sessionstart(session):
    """Ensure config is properly initialized at session start.
    
    This hook runs after conftest.py is loaded but before any tests run,
    ensuring all imports have access to the correct test configuration.
    """
    from mkobi.config import clear_config_cache, get_config
    
    # Re-clear and reinitialize to ensure clean state after any early imports
    clear_config_cache()
    config = get_config()
    
    if config.jwt.secret_key is None:
        raise RuntimeError(
            "JWT__SECRET_KEY must be set in environment before tests run. "
            f"Current value: {repr(config.jwt.secret_key)}"
        )


def pytest_configure(config):
    """Ensure config is properly initialized before tests run."""
    # Config should already be initialized above, this is just a sanity check
    _ = _config  # noqa: F841


# Import models for metadata registration (after config is initialized)
from mkobi.db.models import (  # noqa: E402, F401
    AggregatedData,
    Dashboard,
    DashboardAccess,
    Filter,
    Graph,
    Layout,
    ProcessingConfig,
    ProcessingLog,
    User,
)

# Import security functions (after config is initialized)
from mkobi.core.security import (  # noqa: E402, F401
    AsyncRateLimiter,
    create_access_token,
    hash_password,
)
from mkobi.db.repositories.user_repo import UserRepository  # noqa: E402, F401

TEST_ASYNC_DB_URL = str(_config.TEST_DATABASE_URL)


class MockRedis:
    """Mock Redis client for testing rate limiter without real Redis."""

    def __init__(self):
        self._data = {}

    async def get(self, key):
        return self._data.get(key)

    def pipeline(self):
        return MockPipeline(self)

    async def incr(self, key):
        val = int(self._data.get(key, 0)) + 1
        self._data[key] = str(val)
        return val

    async def expire(self, key, ttl):
        pass

    async def execute(self):
        pass

    async def close(self):
        pass


class MockPipeline:
    """Mock pipeline that supports async with."""

    def __init__(self, redis_client):
        self._redis = redis_client
        self._commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def incr(self, key):
        return await self._redis.incr(key)

    async def expire(self, key, ttl):
        return await self._redis.expire(key, ttl)

    async def execute(self):
        """Mock execute - commands are already applied."""
        pass


@pytest.fixture(autouse=True)
def _auto_mock_redis(monkeypatch):
    """Auto-mock Redis client for all tests to avoid requiring a real Redis server.

    This fixture is always active and patches get_async_redis_client and
    get_redis_client to use an in-memory MockRedis instance. It also
    patches AuthService to bypass rate limiting by default, so existing
    tests don't break. Tests that need real rate limiting behavior should
    use the strict_redis fixture.
    """
    mock_redis_client = MockRedis()

    import mkobi.core.redis_client as redis_client_module

    def mock_get_async_redis_client():
        return mock_redis_client

    def mock_get_redis_client():
        return mock_redis_client

    monkeypatch.setattr(redis_client_module, "get_async_redis_client", mock_get_async_redis_client)
    monkeypatch.setattr(redis_client_module, "get_redis_client", mock_get_redis_client)

    # Patch the rate limiter instances in data_service
    from mkobi.core.security import AsyncRateLimiter
    import mkobi.services.data_service as data_service_module

    data_service_module._upload_rate_limiter = AsyncRateLimiter(mock_redis_client)

    # Patch auth service rate limiter to always allow (backward compatibility)
    import mkobi.services.auth_service as auth_service_module

    original_init = auth_service_module.AuthService.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Make check_rate_limit always return True (allow all)
        async def always_true(*a, **kw):
            return True

        self._rate_limiter.check_rate_limit = always_true

    monkeypatch.setattr(auth_service_module.AuthService, "__init__", patched_init)


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client for tests that need to bypass rate limiting.

    Opt-in fixture - only use when rate limiting should be explicitly
    bypassed. Applies a patched AuthService that always allows login attempts.
    """
    from mkobi.core.security import AsyncRateLimiter

    mock_redis_client = MockRedis()

    # Patch get_async_redis_client to return mock
    import mkobi.core.redis_client as redis_client_module

    def mock_get_async_redis_client():
        return mock_redis_client

    monkeypatch.setattr(redis_client_module, "get_async_redis_client", mock_get_async_redis_client)

    # Patch the rate limiter instances in data_service
    import mkobi.services.data_service as data_service_module

    data_service_module._upload_rate_limiter = AsyncRateLimiter(mock_redis_client)

    # Patch auth service rate limiter to always allow
    import mkobi.services.auth_service as auth_service_module

    original_init = auth_service_module.AuthService.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Make check_rate_limit always return True (allow all)
        async def always_true(*a, **kw):
            return True

        self._rate_limiter.check_rate_limit = always_true

    monkeypatch.setattr(auth_service_module.AuthService, "__init__", patched_init)


@pytest.fixture
def strict_redis(monkeypatch):
    """Provide real rate limiting behavior for tests.

    Uses an in-memory MockRedis client that tracks state, allowing rate
    limiting logic to be properly tested without a real Redis server.
    Unlike the default autouse mock, this does NOT patch check_rate_limit
    — the AsyncRateLimiter will actually count attempts and block excess
    requests.
    """
    from mkobi.core.security import AsyncRateLimiter

    mock_redis_client = MockRedis()

    # Patch get_async_redis_client to return mock
    import mkobi.core.redis_client as redis_client_module

    def mock_get_async_redis_client():
        return mock_redis_client

    monkeypatch.setattr(redis_client_module, "get_async_redis_client", mock_get_async_redis_client)

    # Patch the rate limiter instances in data_service
    import mkobi.services.data_service as data_service_module

    data_service_module._upload_rate_limiter = AsyncRateLimiter(mock_redis_client)

    # Auth service uses real rate limiting behavior - do NOT patch check_rate_limit


@pytest.fixture(scope="session")
async def setup_test_database():
    """Fixture to set up test database before tests run.
    
    Uses pytest-asyncio event loop to avoid loop conflicts.
    Recreates the test database and applies migrations.
    This fixture has session scope to run once before all tests.
    """
    from mkobi.db.starter import DatabaseStarter, DatabaseStarterConfig
    from mkobi.config import get_config, clear_config_cache

    clear_config_cache()
    config = get_config()
    starter_config = DatabaseStarterConfig(
        main_database_url=config.DATABASE_URL,
        test_database_url=config.test_database_url,
        test_admin_database_url=config.test_admin_database_url,
        recreate_test_db=True,
    )
    await DatabaseStarter(starter_config).recreate_test_database()
    yield
    # Optional: cleanup after all tests
    # Could drop the test database here if needed


@pytest.fixture(scope="session")
async def async_test_engine(setup_test_database):
    """Fixture for creating async test DB engine.
    
    Uses NullPool to prevent connection pooling issues in tests:
    - Avoids zombie connections
    - Prevents "database is being accessed by other users" errors
    - Eliminates asyncpg stale connection issues
    - Reduces intermittent CI failures
    """
    engine = create_async_engine(
        TEST_ASYNC_DB_URL,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def async_session_maker(async_test_engine):
    """Fixture for creating async session factory."""
    async_session = async_sessionmaker(
        async_test_engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session


@pytest.fixture(scope="function")
async def async_db_session(async_session_maker):
    """Fixture for creating async DB session for tests.

    Uses SAVEPOINT pattern (session.begin_nested()) for proper rollback:
    - Starts a SAVEPOINT before each test
    - Yields the session for test use
    - Automatically rolls back the SAVEPOINT at the end
    - No TRUNCATE needed, faster, no deadlocks
    """
    from sqlalchemy import event

    async with async_session_maker() as session:
        # Register a listener to start a new SAVEPOINT after each commit/rollback
        # This allows tests to use commit() while maintaining isolation
        # Note: Must listen on sync_session for AsyncSession
        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(sess, trans):
            if trans.nested and not trans._parent.nested:
                # End the current nested transaction
                sess.begin_nested()

        # Start the initial SAVEPOINT
        await session.begin_nested()
        try:
            yield session
        finally:
            # Rollback to SAVEPOINT
            await session.rollback()
            await session.close()


@pytest.fixture(scope="session")
async def baseline_data(setup_test_database):
    """Load minimal reference data once per test session.

    This fixture is a placeholder for future reference data loading.
    Currently ensures the test database is properly initialized.
    """
    yield


@pytest.fixture
def mock_db():
    """Mock AsyncSession for unit tests that don't need a real database.

    Service methods now require db as a mandatory parameter.
    This fixture provides a MagicMock that satisfies the type checker
    for unit tests with mocked repositories.
    """
    from unittest.mock import AsyncMock
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
async def async_client(async_db_session):
    """Fixture for creating async HTTP client.

    Overrides the get_db_dependency to use the test's session.
    This ensures the API and test use the same session.
    """
    from mkobi.api.deps import get_db_dependency
    from mkobi.main import app
    import httpx
    from httpx import ASGITransport

    # Override the database dependency to use test session
    async def override_get_db() -> AsyncSession:
        yield async_db_session

    app.dependency_overrides[get_db_dependency] = override_get_db

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver/api/v1"
    ) as client:
        yield client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(async_client, auth_headers):
    """Returns HTTP client with authorization headers set."""
    async_client.headers.update(auth_headers)
    yield async_client


@pytest.fixture
async def test_user(async_db_session) -> dict[str, str | object]:
    """Creates test user and returns data with token."""
    unique_id = str(uuid4())[:8]

    # UserRepository doesn't store db - it's passed to each method
    repo = UserRepository()
    user = await repo.create(
        db=async_db_session,
        email=f"test_{unique_id}@example.com",
        password_hash=hash_password("TestPass123!"),
        role="admin",
    )
    # Commit the user so the API can see it
    await async_db_session.commit()

    token = create_access_token({"user_id": str(user.id), "email": user.email})

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "token": token,
    }


@pytest.fixture
def auth_headers(test_user) -> dict[str, str]:
    """Returns authorization headers with JWT token."""
    return {"Authorization": f"Bearer {test_user['token']}"}
