from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mko_bi.config import get_config
from mko_bi.db.base import Base

# Cache for engine and SessionLocal
_engine = None
_SessionLocal = None


def _get_engine():
    """Создает и кеширует SQLAlchemy engine."""
    global _engine
    if _engine is None:
        config = get_config()
        DATABASE_URL = config.DATABASE_URL

        if "sqlite" in DATABASE_URL:
            _engine = create_engine(
                DATABASE_URL,
                echo=False,
                future=True,
                connect_args={"check_same_thread": False},
            )
        else:
            _engine = create_engine(
                DATABASE_URL,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
            )
    return _engine


def _get_SessionLocal():
    """Создает и кеширует sessionmaker."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = _get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False,
            class_=Session,
        )
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Контекстный менеджер для сессий базы данных.
    
    Создает новую сессию и гарантирует её закрытие после использования.
    Рекомендуется использовать через контекстный менеджер:
    
    Example:
        ```python
        with get_session() as db:
            result = db.query(User).all()
        ```
    
    Yields:
        Session: Сессия SQLAlchemy для выполнения операций с БД.
    """
    SessionLocal = _get_SessionLocal()
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Генератор сессий базы данных для использования в зависимостях FastAPI.
    
    Создает новую сессию и гарантирует её закрытие после использования.
    Сохранен для обратной совместимости с существующим кодом.
    Рекомендуется использовать get_session() вместо этого метода.
    
    Yields:
        Session: Сессия SQLAlchemy для выполнения операций с БД.
    
    Example:
        ```python
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    with get_session() as db:
        yield db


def init_db() -> None:
    """Создаёт все таблицы, определённые в моделях.

    Выполняет CREATE TABLE для всех моделей, унаследованных от Base,
    если таблицы ещё не существуют.

    Note:
        В продакшене предпочтительнее использовать миграции (например, Alembic)
        вместо автоматического создания таблиц.
    """
    # noqa: F401 - импорт нужен для регистрации моделей в Base.metadata
    
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Удаляет все таблицы, определённые в моделях.

    Warning:
        Операция разрушительная! Использовать только для тестов
        или при полной переинициализации базы данных.
    """
    # noqa: F401 - импорт нужен для регистрации моделей в Base.metadata
    
    engine = _get_engine()
    Base.metadata.drop_all(bind=engine)

