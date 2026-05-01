TASK: Настроить Alembic для PostgreSQL

FILE: alembic/env.py, alembic/versions/, alembic.ini

GOAL: Настроить систему миграций Alembic для управления схемой БД

IMPLEMENT:

1. Установить alembic: uv add alembic
2. Инициализировать Alembic: alembic init alembic
3. Настроить alembic.ini (sqlalchemy.url = config.DATABASE_URL)
4. Настроить alembic/env.py:
   - Импортировать модели из src.mko_bi.db.models
   - Настроить target_metadata = Base.metadata
   - Настроить connection к БД через get_config()
5. Создать первоначальную миграцию: alembic revision --autogenerate -m "Initial migration"
6. Проверить и применить миграцию: alembic upgrade head

LOGIC:

Настроить инфраструктуру версионирования схемы БД
Создать первоначальную миграцию на основе существующих моделей
Обеспечить возможность воспроизведения схемы с нуля

CONSTRAINTS:

Использовать существующие модели в src/mko_bi/db/models/
Не использовать Flask-Migrate (только чистый Alembic)
Настроить для PostgreSQL

DONE:

 Alembic инициализирован
 Первоначальная миграция создана
 Миграция успешно применяется к bidb
 Команда alembic upgrade head работает
