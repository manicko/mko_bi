TASK: Enhance starter.py to verify alembic_version has value

FILE: src/mko_bi/db/starter.py

GOAL: Ensure alembic_version table not only exists but has correct version

IMPLEMENT:

func: _check_alembic_version_populated() -> bool
  - SELECT COUNT(*) FROM alembic_version
  - return count == 1

func: _handle_missing_version() -> None
  - if not populated: run "alembic stamp head" or INSERT version

LOGIC:

1. Modify _check_schema_exists() to also verify version is recorded
2. If table exists but is empty: treat as missing schema
3. Add method to populate version if empty
4. Integrate with existing startup() flow

CONSTRAINTS:

только для env=development/test (production требует ручного вмешательства)
не должно нарушать существующую логику starter.py
логировать предупреждения при пустой таблице версий

DONE:

 starter.py проверяет что alembic_version содержит 1 запись
 если таблица пустая - версия добавляется автоматически (dev/test)
 тест: проверка поведения starter при пустой alembic_version
