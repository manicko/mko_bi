"""Общие фикстуры для тестов.

Этот файл содержит фикстуры, используемые во всех тестах,
включая настройку базы данных, мокирование и вспомогательные функции.
"""

import os
from collections.abc import Generator, AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Устанавливаем обязательные переменные окружения ДО импорта любых модулей mko_bi
os.environ.setdefault("DB_PASSWORD", "1234")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_change_in_production")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "bidb_test")
os.environ.setdefault("DB_USER", "postgres")

from mko_bi.db.base import Base
from mko_bi.main import app
from mko_bi.core.security import hash_password, create_access_token
from mko_bi.db.repositories.user_repo import UserRepository

# Тестовая БД PostgreSQL (синхронная)
TEST_DB_URL = "postgresql://postgres:1234@localhost:5432/bidb_test"
# Тестовая БД PostgreSQL (асинхронная)
TEST_ASYNC_DB_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test"


@pytest.fixture(scope="session")
def test_engine():
    """Фикстура для создания синхронного тестового движка БД (PostgreSQL)."""
    engine = create_engine(
        TEST_DB_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    yield engine

    # Удаляем таблицы
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Generator:
    """Фикстура для создания синхронной сессии БД для тестов."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def async_test_engine():
    """Фикстура для создания асинхронного тестового движка БД (PostgreSQL)."""
    engine = create_async_engine(
        TEST_ASYNC_DB_URL,
        echo=False,
        pool_pre_ping=True,
    )
    return engine


@pytest.fixture(scope="session")
async def async_session_maker(async_test_engine):
    """Фикстура для создания асинхронной фабрики сессий."""
    async_session = async_sessionmaker(
        async_test_engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session


@pytest.fixture(scope="function")
async def async_db_session(async_test_engine, async_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для создания асинхронной сессии БД для тестов."""
    # Создаем таблицы
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            # Удаляем все данные после теста
            async with async_test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Фикстура для создания асинхронного HTTP клиента."""
    import httpx
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def authenticated_client(async_client, auth_headers) -> AsyncGenerator:
    """Возвращает HTTP клиент с установленными заголовками авторизации."""
    async_client.headers.update(auth_headers)
    yield async_client


@pytest.fixture
def test_user(db_session) -> dict:
    """Создает тестового пользователя и возвращает данные с токеном."""
    repo = UserRepository()
    unique_id = str(uuid4())[:8]

    user = repo.create(
        db=db_session,
        email=f"test_{unique_id}@example.com",
        password_hash=hash_password("TestPass123!"),
        role="admin",
    )
    # Commit the transaction so the API can see the user
    db_session.commit()
    
    token = create_access_token({"user_id": str(user.id), "email": user.email})

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "token": token,
    }


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Возвращает заголовки авторизации с JWT токеном."""
    return {"Authorization": f"Bearer {test_user['token']}"}