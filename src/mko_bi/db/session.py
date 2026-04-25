from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mko_bi.config import config
from mko_bi.db.base import Base


# Проверяем, запущены ли тесты (по переменной окружения)
if os.environ.get("DB_DRIVER") == "sqlite":
    # Для тестов используем SQLite in-memory
    DATABASE_URL = "sqlite:///:memory:"
else:
    # Для продакшена используем PostgreSQL
    DATABASE_URL = config.DATABASE_URL

# Создаём engine для подключения к базе данных
# echo=False для отключения логирования SQL-запросов в продакшене
# future=True для использования SQLAlchemy 2.0 API
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,  # Проверка соединений перед использованием
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
    )


# SessionLocal для управления сессиями базы данных
# expire_on_commit=False чтобы объекты оставались доступными после коммита
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=Session,
)


# Глобальная переменная для хранения тестового engine
_test_engine = None


def override_engine_for_testing(test_engine):
    """Переопределяет engine для тестов.

    Args:
        test_engine: Engine для тестов.
    """
    global _test_engine, engine, SessionLocal
    _test_engine = test_engine
    engine = test_engine
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
        class_=Session,
    )


def reset_engine():
    """Сбрасывает engine к исходному состоянию."""
    global _test_engine, engine, SessionLocal
    if _test_engine is not None:
        if "sqlite" in DATABASE_URL:
            engine = create_engine(
                DATABASE_URL,
                echo=False,
                future=True,
                connect_args={"check_same_thread": False},
            )
        else:
            engine = create_engine(
                DATABASE_URL,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
            )
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False,
            class_=Session,
        )
        _test_engine = None


def get_db() -> Generator[Session, None, None]:
    """Генератор сессий базы данных для использования в зависимостях FastAPI.

    Yields:
        Session: Сессия SQLAlchemy для выполнения операций с БД.

    Example:
        ```python
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```

    При выходе из контекста сессия автоматически закрывается,
    возвращая соединение в пул.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создаёт все таблицы, определённые в моделях.

    Выполняет CREATE TABLE для всех моделей, унаследованных от Base,
    если таблицы ещё не существуют.

    Note:
        В продакшене предпочтительнее использовать миграции (например, Alembic)
        вместо автоматического создания таблиц.
    """
    # noqa: F401 - импорт нужен для регистрации моделей в Base.metadata
    from mko_bi.db.models import access, dashboard, user  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Удаляет все таблицы, определённые в моделях.

    Warning:
        Операция разрушительная! Использовать только для тестов
        или при полной переинициализации базы данных.
    """
    # noqa: F401 - импорт нужен для регистрации моделей в Base.metadata
    from mko_bi.db.models import access, dashboard, user  # noqa: F401

    Base.metadata.drop_all(bind=engine)
