TASK: Add composite index on aggregated_data(dashboard_id, graph_id)

FILE: alembic/versions/*.py, src/mko_bi/db/starter.py

GOAL: Improve query performance for (dashboard_id, graph_id) lookups

IMPLEMENT:

sql: CREATE INDEX idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id);

migration: add composite index

LOGIC:

1. Create new migration to add composite index
2. Index covers queries filtering by both dashboard_id AND graph_id
3. Keep existing single-column indexes for single-column queries

CONSTRAINTS:

не должен дублировать существующие индексы
использовать IF NOT EXISTS для идемпотентности
имя индекса: idx_aggregated_data_dashboard_graph

DONE:

 индекс idx_aggregated_data_dashboard_graph создан
 запросы по (dashboard_id, graph_id) используют индекс
 тест: проверка существования индекса в БД
