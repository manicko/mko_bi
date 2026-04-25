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


