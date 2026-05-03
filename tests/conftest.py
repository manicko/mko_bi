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
os.environ.setdefault("DB_PASSWORD", "1234")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_change_in_production")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "bidb_test")
os.environ.setdefault("DB_USER", "postgres")

from mko_bi.main import app
from mko_bi.core.security import hash_password, create_access_token
from mko_bi.db.repositories.user_repo import UserRepository

# Test PostgreSQL database (async)
TEST_ASYNC_DB_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test"

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


def pytest_sessionstart(session):
    """Setup before test session starts."""
    # Migrations assumed to be already applied
    pass


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
