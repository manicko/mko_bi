TASK: Remove redundant index idx_dashboard_filters_dashboard_filter

FILE: alembic/versions/*.py

GOAL: Drop unnecessary index that duplicates PRIMARY KEY

IMPLEMENT:

sql: DROP INDEX IF EXISTS idx_dashboard_filters_dashboard_filter;

migration: drop redundant index

LOGIC:

1. Create new migration to drop the index
2. PRIMARY KEY (dashboard_id, filter_id) already covers the same query pattern
3. Removing index saves disk space and improves INSERT/UPDATE/DELETE performance

CONSTRAINTS:

проверить что индекс существует перед удалением
идемпотентная операция (IF EXISTS)
не удалять PRIMARY KEY!

DONE:

 индекс idx_dashboard_filters_dashboard_filter удален
 PRIMARY KEY (dashboard_id, filter_id) остался
 тест: проверка отсутствия дублирующего индекса
