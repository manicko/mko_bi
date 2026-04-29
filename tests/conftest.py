"""Общие фикстуры для тестов.

Этот файл содержит фикстуры, используемые во всех тестах,
включая настройку базы данных, мокирование и вспомогательные функции.
"""

import os

# Устанавливаем обязательные переменные окружения для тестов
# (конфигурация pydantic-settings требует эти переменные)
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_change_in_production")

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mko_bi.db.base import Base


@pytest.fixture(scope="session")
def test_engine():
    """Фикстура для создания тестовой базы данных (SQLite in-memory).

    Создает тестовую базу данных перед запуском тестов и удаляет её
    после завершения всех тестов.
    """
    # Создаем SQLite in-memory engine для тестов
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )

    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)

    yield engine

    # Очищаем базу данных после тестов
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    """Фикстура для создания сессии базы данных для тестов.

    Создает новую сессию для каждого теста и автоматически
    откатывает изменения после завершения теста.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def mock_get_engine(test_engine):
    """Автоматически мокирует get_engine для всех тестов.

    Это позволяет использовать тестовый engine вместо реального
    без использования глобального состояния.
    """
    with patch("mko_bi.db.session.get_engine", return_value=test_engine):
        yield
