"""Общие фикстуры для тестов.

Этот файл содержит фикстуры, используемые во всех тестах,
включая настройку базы данных, мокирование и вспомогательные функции.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from mko_bi.db.session import SessionLocal, override_engine_for_testing, reset_engine
from mko_bi.db.base import Base
from mko_bi.models.user import UserDB


@pytest.fixture(scope="session")
def test_db():
    """Фикстура для создания тестовой базы данных (SQLite in-memory).

    Создает тестовую базу данных перед запуском тестов и удаляет её
    после завершения всех тестов.
    """
    # Создаем SQLite in-memory engine для тестов
    from sqlalchemy import create_engine
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    
    # Переопределяем engine для тестов
    override_engine_for_testing(test_engine)
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Очищаем базу данных после тестов
    Base.metadata.drop_all(bind=test_engine)
    reset_engine()


@pytest.fixture
def db_session(test_db):
    """Фикстура для создания сессии базы данных для тестов.

    Создает новую сессию для каждого теста и автоматически
    откатывает изменения после завершения теста.
    """
    connection = test_db.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_user():
    """Фикстура для создания мока пользователя.

    Возвращает мок пользователя с предопределенными значениями.
    """
    user = MagicMock(spec=UserDB)
    user.id = 1
    user.email = "test@example.com"
    user.role = "viewer"
    user.password_hash = "$2b$12$examplehash"
    return user


@pytest.fixture
def mock_admin_user():
    """Фикстура для создания мока администратора.

    Возвращает мок администратора с предопределенными значениями.
    """
    user = MagicMock(spec=UserDB)
    user.id = 1
    user.email = "admin@example.com"
    user.role = "admin"
    user.password_hash = "$2b$12$examplehash"
    return user


@pytest.fixture
def mock_editor_user():
    """Фикстура для создания мока редактора.

    Возвращает мок редактора с предопределенными значениями.
    """
    user = MagicMock(spec=UserDB)
    user.id = 2
    user.email = "editor@example.com"
    user.role = "editor"
    user.password_hash = "$2b$12$examplehash"
    return user