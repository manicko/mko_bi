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

# Set required environment variables BEFORE importing any mko_bi modules
# Use pydantic-settings nested env vars (double underscore)
os.environ["DATABASE__HOST"] = "localhost"
os.environ["DATABASE__PORT"] = "5432"
os.environ["DATABASE__DBNAME"] = "bidb_test"
os.environ["DATABASE__USER"] = "postgres"
os.environ["DATABASE__PASSWORD"] = "1234"
os.environ["JWT__SECRET_KEY"] = "test_secret_key_change_in_production"
os.environ["REDIS__HOST"] = "localhost"
os.environ["REDIS__PORT"] = "6379"

from mko_bi.main import app
from mko_bi.core.security import hash_password, create_access_token
from mko_bi.db.repositories.user_repo import UserRepository

# Test PostgreSQL database (async)
# Use get_config() to be consistent with the app
from mko_bi.config import get_config
_config = get_config()
TEST_ASYNC_DB_URL = str(_config.database.database_url).replace("postgresql://", "postgresql+asyncpg://", 1)

# Import models for metadata registration
from mko_bi.db.models import (  # noqa: E402, F401
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


# Mock Redis for rate limiter tests
class MockRedis:
    """Mock Redis client for testing rate limiter without real Redis."""

    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def pipeline(self):
        return self

    def incr(self, key):
        val = int(self._data.get(key, 0)) + 1
        self._data[key] = str(val)
        return val

    def expire(self, key, ttl):
        pass

    def execute(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Mock Redis client for all tests to avoid requiring real Redis."""
    from mko_bi.core.security import RateLimiter

    mock_redis_client = MockRedis()

    # Patch get_redis_client to return mock
    import mko_bi.config as config_module
    def mock_get_redis_client():
        return mock_redis_client
    monkeypatch.setattr(config_module, "get_redis_client", mock_get_redis_client)

    # Patch the rate limiter instances in data_service
    import mko_bi.services.data_service as data_service_module
    data_service_module._upload_rate_limiter = RateLimiter(mock_redis_client)

    # Patch auth service rate limiter
    import mko_bi.services.auth_service as auth_service_module
    original_init = auth_service_module.AuthService.__init__
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._rate_limiter = RateLimiter(mock_redis_client)
    monkeypatch.setattr(auth_service_module.AuthService, "__init__", patched_init)


def pytest_sessionstart(session):
    """Setup before test session starts."""
    # Drop and recreate tables directly from metadata
    # This ensures enums are recreated with correct values
    import asyncio
    from mko_bi.db.base import Base
    
    async def recreate_tables():
        engine = create_async_engine(
            TEST_ASYNC_DB_URL,
            echo=False,
        )
        async with engine.begin() as conn:
            # Drop tables first
            await conn.run_sync(Base.metadata.drop_all)
            # Drop enum types if they exist (to recreate with updated values)
            await conn.execute(text("DROP TYPE IF EXISTS processing_status CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS user_role CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS dashboard_permission_level CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS graph_type CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS filter_type CASCADE"))
            # Recreate all tables with correct schema
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    
    asyncio.run(recreate_tables())


@pytest.fixture(scope="session")
async def async_test_engine():
    """Fixture for creating async test DB engine."""
    engine = create_async_engine(
        TEST_ASYNC_DB_URL,
        echo=False,
        pool_pre_ping=True,
    )
    return engine


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
            await conn.execute(text(
                "ALTER SEQUENCE IF EXISTS aggregated_data_id_seq RESTART WITH 1"
            ))


@pytest.fixture
async def async_client():
    """Fixture for creating async HTTP client."""
    import httpx
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
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

    user = await UserRepository.create(
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
