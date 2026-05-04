# TASK_XXX_fix_migrations_enum_mismatch

## Описание проблемы

Миграции Alembic не синхронизированы с Python-моделями:
1. Enum `processing_status` в БД содержит 3 значения, а в коде — 6
2. При добавлении новых значений в Python-модели миграции не обновляются
3. Тесты обходят эту проблему, пересоздавая схему напрямую из метаданных

## Требуемые изменения

### 1. Исправить начальную миграцию
Обновить файл `alembic/versions/7130ecb0388c_true_initial_migration.py`:
- Добавить недостающие значения в создание enum:
```sql
CREATE TYPE processing_status AS ENUM ('started', 'uploaded', 'processing', 'success', 'failed', 'completed');
```

### 2. Добавить миграцию для обновления enum (если БД уже развернута)
Создать новую миграцию для добавления недостающих значений:
```python
def upgrade() -> None:
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'uploaded'")
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'processing'")
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'completed'")
```

### 3. Настроить автоматическую генерацию миграций
Убедиться, что `alembic/env.py` настроен на отслеживание изменений в enum-типах.

### 4. Вернуть conftest.py к использованию миграций
После исправления миграций, обновить `tests/conftest.py`:
- Удалить временный код пересоздания схемы
- Использовать `alembic.command.upgrade()` для применения миграций в тестах

## Критерии приемки
- [ ] Enum в БД соответствует Python-модели
- [ ] `alembic revision --autogenerate` корректно детектит изменения enum
- [ ] Тесты проходят с использованием реальных миграций (а не `metadata.create_all`)
- [ ] Документация по добавлению новых значений enum

## Контекст
- Файл модели: `src/mko_bi/models/user_roles.py:68-75`
- Начальная миграция: `alembic/versions/7130ecb0388c_true_initial_migration.py:36-38`
- Конфиг Alembic: `alembic/env.py`
- Тестовая БД: `tests/conftest.py` (функция `pytest_sessionstart`)
