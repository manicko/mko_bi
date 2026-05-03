TASK: Настроить Alembic для работы с async (asyncpg)

FILE: alembic/env.py

GOAL: Обновить Alembic для поддержки асинхронных миграций

IMPLEMENT:

1. Обновить alembic/env.py:
   - Использовать async_engine из sqlalchemy.ext.asyncio
   - Настроить run_migrations_online() для работы с asyncpg
   - Использовать AsyncConnection вместо Connection
   - Добавить настройку для async миграций (sqlalchemy_url с +asyncpg)
2. Обновить alembic.ini:
   - sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/bidb

LOGIC:

После перехода на asyncpg (Задача 002), Alembic должен уметь применять миграции
Используем async_engine и асинхронные соединения для миграций
Необходимо правильно настроить env.py для работы с async

CONSTRAINTS:

Использовать настройки из config.py (DATABASE_URL с asyncpg)
Миграции должны работать с асинхронным движком

DONE:

 alembic/env.py настроен для async миграций
 Команда alembic upgrade head работает с asyncpg
 Миграции применяются корректно
