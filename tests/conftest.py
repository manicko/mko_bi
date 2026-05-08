"""Common fixtures for tests."""
import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# Set required environment variables BEFORE importing any mkobi modules
# Use pydantic-settings nested env vars (double underscore)
os.environ["ENV"] = "test"
os.environ["DATABASE__HOST"] = "localhost"
os.environ["DATABASE__PORT"] = "5432"
os.environ["DATABASE__DBNAME"] = "bidb_test"
os.environ["DATABASE__USER"] = "postgres"
os.environ["DATABASE__PASSWORD"] = "1234"
os.environ["DATABASE__TEST_DBNAME"] = "bidb_test"
os.environ["JWT__SECRET_KEY"] = "test_secret_key_change_in_production"
os.environ["REDIS__HOST"] = "localhost"
os.environ["REDIS__PORT"] = "6379"
os.environ["RECREATE_TEST_DB"] = "true"

# Test PostgreSQL database (async)
# Use get_config() to be consistent with the app
from mkobi.config import get_config
from mkobi.core.security import create_access_token, hash_password
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.main import app

_config = get_config()
# Use TEST_DATABASE_URL for test async engine (explicitly for test database)
TEST_ASYNC_DB_URL = str(_config.TEST_DATABASE_URL)

# Import models for metadata registration
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


class MockRedis:
    """Mock Redis client for testing rate limiter without real Redis."""

    def __init__(self):
        self._data = {}
        self._pipeline_data = {}

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
def mock_redis(monkeypatch):
    """Mock Redis client for all tests to avoid requiring real Redis."""
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

    # Patch auth service rate limiter
    import mkobi.services.auth_service as auth_service_module

    original_init = auth_service_module.AuthService.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Make check_rate_limit always return True (allow all)
        async def always_true(*a, **kw):
            return True
        self._rate_limiter.check_rate_limit = always_true

    monkeypatch.setattr(auth_service_module.AuthService, "__init__", patched_init)


@pytest.fixture(scope="session")
async def setup_test_database():
    """Fixture to set up test database before tests run.
    
    Uses pytest-asyncio event loop to avoid loop conflicts.
    Recreates the test database and applies migrations.
    This fixture has session scope to run once before all tests.
    """
    from mkobi.db.starter import DatabaseStarter, DatabaseStarterConfig

    config = DatabaseStarterConfig(
        test_database_url=os.environ.get("TEST_DATABASE_URL"),
        recreate_test_db=True,
    )
    await DatabaseStarter(config).recreate_test_database()
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
async def async_db_session(async_test_engine, async_session_maker):
    """Fixture for creating async DB session for tests."""
    async with async_session_maker() as session:
        yield session
    # Clean up after test
    async with async_test_engine.begin() as conn:
        from sqlalchemy import inspect

        table_names = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        if table_names:
            tables_sql = ", ".join(f'"{table}"' for table in table_names)
            await conn.execute(text(f"TRUNCATE TABLE {tables_sql} CASCADE"))
            # Reset sequences after TRUNCATE
            await conn.execute(
                text("ALTER SEQUENCE IF EXISTS aggregated_data_id_seq RESTART WITH 1")
            )


@pytest.fixture
async def async_client():
    """Fixture for creating async HTTP client."""
    import httpx
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver/api/v1"
    ) as client:
        yield client


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
