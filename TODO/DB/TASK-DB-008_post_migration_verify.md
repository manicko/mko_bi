TASK: Add post-migration verification in starter.py

FILE: src/mko_bi/db/starter.py

GOAL: Verify migration success by checking alembic_version after migration

IMPLEMENT:

func: _verify_migration_success() -> bool
  - SELECT version_num FROM alembic_version
  - return True if exactly 1 row with non-empty version

Modify: _run_migrations()
  - After: to_thread(_sync_migrate)
  - Add: success = await _verify_migration_success()
  - If not success: raise MigrationError("alembic_version not populated after migration")

LOGIC:

1. After running Alembic migration, verify version was recorded
2. If verification fails, raise error and log critical message
3. Prevents silent failures where migration runs but version not tracked

CONSTRAINTS:

должно работать только после _run_migrations()
не блокировать запуск в production если версия не записалась (только warning)
логировать результат верификации

DONE:

 после миграции версия проверяется
 при ошибке записи версии - логируется критическая ошибка
 тест: проверка верификации после миграции
