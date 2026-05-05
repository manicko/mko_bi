TASK: Implement processing_logs cleanup/retention policy

FILE: src/mko_bi/db/starter.py, alembic/versions/*.py

GOAL: Prevent unbounded growth of processing_logs table

IMPLEMENT:

func: cleanup_old_logs(retention_days: int = 30) -> int
  - DELETE FROM processing_logs 
    WHERE started_at < NOW() - INTERVAL '{retention_days} days'
  - return number of deleted rows

func: schedule_logs_cleanup() - optional async task

Integration options:
1. Run cleanup on startup (in DatabaseStarter.startup())
2. Run cleanup periodically (background task)
3. Add cleanup as separate CLI command

Recommended: Option 1 (simple) + Option 3 (manual cleanup)

LOGIC:

1. Add cleanup method to DatabaseStarter
2. Call cleanup on startup (before/after migration) or expose as CLI
3. Default retention: 30 days (configurable via YAML)
4. Log number of deleted records

CONSTRAINTS:

не удалять логи с статусом 'started' или 'processing' (они могут быть активными)
использовать настройку retention_days из конфигурации
логировать результат очистки

DONE:

 старые логи удаляются (старше retention_days)
 активные логи (started/processing) не удаляются
 настройка retention_days доступна через конфигурацию
 тест: проверка что старые логи удаляются, а новые - нет
