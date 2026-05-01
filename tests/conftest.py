"""Общие фикстуры для тестов.

Этот файл содержит фикстуры, используемые во всех тестах,
включая настройку базы данных, мокирование и вспомогательные функции.
"""

import os
from collections.abc import Generator, AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

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
from mko_bi.models.user import UserCreate

# Тестовая БД PostgreSQL (синхронная)
TEST_DB_URL = "postgresql://postgres:1234@localhost:5432/bidb_test"


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


@pytest.fixture(autouse=True)
def clean_db(db_session):
    """Очищает данные после каждого теста."""
    yield
    # Удаляем все данные после теста
    from mko_bi.db.models.access import DashboardAccess
    from mko_bi.db.models.dashboard import Dashboard
    from mko_bi.db.models.user import User
    db_session.execute(DashboardAccess.__table__.delete())
    db_session.execute(Dashboard.__table__.delete())
    db_session.execute(User.__table__.delete())
    db_session.commit()


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
