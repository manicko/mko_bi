TASK: Добавить GIN индекс на aggregated_data.dims для оптимизации фильтрации

FILE: create_db.sql, src/mko_bi/db/base.py

GOAL: Оптимизировать производительность фильтрации по JSONB полю dims в таблице aggregated_data

IMPLEMENT:

SQL: CREATE INDEX CONCURRENTLY idx_agg_dims_gin ON aggregated_data USING GIN (dims);

LOGIC:

1. Добавить в create_db.sql:
   - CREATE INDEX для GIN индекса на dims
2. Если используется Alembic:
   - Создать миграцию для добавления индекса
3. Проверить существующие индексы:
   - Убедиться, что все индексы из SPEC созданы
4. Добавить индексы при необходимости:
   - idx_agg_graph_id
   - idx_agg_dashboard_id
   - idx_access_user
   - idx_access_dashboard

CONSTRAINTS:

- Использовать GIN индекс для JSONB
- Индекс должен создаваться CONCURRENTLY в production
- Не блокировать таблицу при создании
- Проверить, нет ли уже существующих индексов

DONE:

- GIN индекс создан на aggregated_data.dims
- Запросы фильтрации работают быстро
- EXPLAIN ANALYZE показывает использование индекса
- Нет деградации производительности
