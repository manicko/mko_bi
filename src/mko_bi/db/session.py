from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager

from mko_bi.config import get_config
from mko_bi.db.base import Base

logger = logging.getLogger(__name__)

# Global engine and sessionmaker (initialized once)
_engine = None
_SessionLocal = None


async def get_async_engine():
    """Возвращает инициализированный SQLAlchemy async engine (создаёт при первом вызове).
    
    Returns:
        AsyncEngine: SQLAlchemy async engine для работы с базой данных.
    """
    global _engine
    if _engine is None:
        config = get_config()
        DATABASE_URL = config.DATABASE_URL
        
        # Replace postgresql:// with postgresql+asyncpg://
        if DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        logger.info("Initializing async engine for %s", DATABASE_URL.split("@")[-1])
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
        )
    return _engine


async def get_async_sessionlocal() -> async_sessionmaker[AsyncSession]:
    """Возвращает инициализированный async_sessionmaker (создаёт при первом вызове).
    
    Returns:
        async_sessionmaker: Сконфигурированный фабрика асинхронных сессий.
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = await get_async_engine()
        _SessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _SessionLocal


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный контекстный менеджер для сессий базы данных.
    
    Создаёт новую асинхронную сессию и гарантирует её закрытие после использования.
    
    Example:
        ```python
        async with get_session() as db:
            result = await db.execute(select(User))
        ```
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    SessionLocal = await get_async_sessionlocal()
    async with SessionLocal() as db:
        yield db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронных сессий для использования в зависимостях FastAPI.
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with get_session() as db:
        yield db


async def init_db() -> None:
    """Создаёт все таблицы, определённые в моделях.
    
    Note:
        В продакшене предпочтительнее использовать миграции (например, Alembic)
        вместо автоматического создания таблиц.
    """
    logger.info("Initializing database tables...")
    engine = await get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")


async def drop_db() -> None:
    """Удаляет все таблицы, определённые в моделях.

    Warning:
        Операция разрушительная! Использовать только для тестов
        или при полной переинициализации базы данных.
    """
    logger.warning("Dropping all database tables!")
    engine = await get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
