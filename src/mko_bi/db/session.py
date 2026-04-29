from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mko_bi.config import get_config
from mko_bi.db.base import Base


def get_engine():
    """Создает и возвращает SQLAlchemy engine.
    
    Использует конфигурацию из переменных окружения через get_config().
    
    Returns:
        Engine: SQLAlchemy engine для подключения к базе данных.
    """
    # Получаем конфигурацию
    config = get_config()
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
    
    return engine


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
    engine = get_engine()
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
        class_=Session,
    )
    
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
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Удаляет все таблицы, определённые в моделях.
    
    Warning:
        Операция разрушительная! Использовать только для тестов
        или при полной переинициализации базы данных.
    """
    # noqa: F401 - импорт нужен для регистрации моделей в Base.metadata
    
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)

