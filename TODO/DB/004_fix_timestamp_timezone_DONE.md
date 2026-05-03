TASK: Исправить timestamp columns (добавить timezone)

FILE: alembic/versions/

GOAL: Изменить все timestamp колонки на TIMESTAMP WITH TIME ZONE

IMPLEMENT:

1. Создать миграцию: alembic revision -m "Add timezone to timestamp columns"
2. В миграции изменить колонки:
   - users.created_at
   - layouts.created_at
   - dashboards.created_at
   - dashboards.updated_at
   - graphs.created_at
   - filters.created_at
   - processing_configs.updated_at
   - processing_logs.started_at
   - processing_logs.finished_at
3. Использовать: op.alter_column(table, column, type_=sa.TIMESTAMP(timezone=True))

LOGIC:

ORM модели используют DateTime(timezone=True), но БД имеет timestamp without time zone
Это приводит к потере timezone информации и багам при работе с датами
Нужно привести БД к виду, ожидаемому ORM

CONSTRAINTS:

Использовать миграцию Alembic (не ручной SQL)
Проверить, что ORM модели имеют timezone=True

DONE:

 Миграция создана
 Все timestamp колонки изменены на TIMESTAMP WITH TIME ZONE
 Миграция успешно применена к bidb
