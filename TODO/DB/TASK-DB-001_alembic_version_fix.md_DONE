TASK: Fix alembic_version table - populate with current version

FILE: alembic/versions/*.py, src/mko_bi/db/starter.py

GOAL: Ensure alembic_version table has correct version recorded

IMPLEMENT:

cmd: alembic stamp head
или
func: _check_alembic_version() -> bool
func: _populate_alembic_version() -> None

LOGIC:

1. Check if alembic_version table exists
2. Check if table has exactly 1 row with version value
3. If empty: run "alembic stamp head" or insert version directly
4. Verify version is recorded correctly

CONSTRAINTS:

только для env=development/test
в production требует ручного вмешательства
версия должна соответствовать HEAD ревизии

DONE:

 alembic_version содержит 1 запись с версией HEAD
 alembic upgrade head не пытается переприменить миграции
 тест: проверка что version table не пустая
