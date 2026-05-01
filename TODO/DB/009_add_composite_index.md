TASK: Добавить composite index на aggregated_data

FILE: alembic/versions/

GOAL: Улучшить производительность запросов с фильтрацией по dashboard_id и graph_id

IMPLEMENT:

1. Создать миграцию: alembic revision -m "Add composite index on aggregated_data"
2. В миграции добавить индекс:
   - op.create_index('idx_agg_dashboard_graph', 'aggregated_data', ['dashboard_id', 'graph_id'], unique=False)
3. Проверить, что индекс создался: \d aggregated_data в psql

LOGIC:

aggregated_data растет с количеством графиков и данных
Часто нужно фильтровать по dashboard_id И graph_id одновременно
Составной индекс ускорит такие запросы

CONSTRAINTS:

Использовать миграцию Alembic
Создать btree индекс (по умолчанию)
Имя индекса: idx_agg_dashboard_graph

DONE:

 Составной индекс на (dashboard_id, graph_id) создан
 Индекс виден в схеме БД
 Миграция успешно применена
