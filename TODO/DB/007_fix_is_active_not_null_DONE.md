TASK: Добавить NOT NULL constraint для users.is_active

FILE: alembic/versions/

GOAL: Синхронизировать ограничение NOT NULL между ORM и БД

IMPLEMENT:

1. Создать миграцию: alembic revision -m "Add NOT NULL to users.is_active"
2. В миграции:
   - Установить NULL значения в FALSE (для существующих записей)
   - Добавить ограничение: op.alter_column('users', 'is_active', existing_type=sa.Boolean(), nullable=False)
3. Проверить, что ORM модель User имеет nullable=False

LOGIC:

ORM модель User.is_active имеет nullable=False
Но в БД колонка позволяет NULL значения
Это может приводить к неконсистентным состояниям

CONSTRAINTS:

Использовать миграцию Alembic
Сначала заполнить NULL значения (например, False)
Затем добавить NOT NULL constraint

DONE:

 users.is_active имеет NOT NULL в БД
 Данные консистентны (нет NULL значений)
 Миграция успешно применена
