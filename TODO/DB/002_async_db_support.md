TASK: Переход на асинхронный движок БД (asyncpg)

FILE: src/mko_bi/db/session.py, pyproject.toml

GOAL: Заменить синхронный SQLAlchemy на асинхронный для работы с FastAPI

IMPLEMENT:

1. Перенести asyncpg из dev в основные зависимости: uv add asyncpg
2. Обновить src/mko_bi/db/session.py:
   - Заменить create_engine на create_async_engine из sqlalchemy.ext.asyncio
   - Заменить sessionmaker на async_sessionmaker
   - Заменить Session на AsyncSession
   - Обновить get_session() для работы с AsyncSession (async with)
   - Обновить get_db() для использования AsyncSession в FastAPI Depends
3. Обновить все сервисы и роуты для работы с AsyncSession

LOGIC:

FastAPI использует async def эндпоинты, но БД синхронная - это блокирует event loop
Нужно использовать asyncpg + AsyncSession для неблокирующей работы с БД
Все вызовы db.query() заменить на await db.execute(select(...))

CONSTRAINTS:

Использовать sqlalchemy.ext.asyncio
Использовать asyncpg драйвер
Обеспечить обратную совместимость через контекстный менеджер

DONE:

 asyncpg установлен как основная зависимость
 session.py использует AsyncSession
 get_db() возвращает асинхронную сессию
 Все роуты работают с AsyncSession без блокировки event loop
