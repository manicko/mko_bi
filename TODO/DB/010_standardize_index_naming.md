TASK: Стандартизировать именование индексов

FILE: alembic/versions/

GOAL: Привести имена всех индексов к единому стандарту

IMPLEMENT:

1. Создать миграцию: alembic revision -m "Standardize index naming"
2. Переименовать индексы согласно стандарту idx_<table>_<columns>:
   - users_pkey -> оставить как есть (PK)
   - users_email_key -> idx_users_email (UNIQUE)
   - ix_users_role -> idx_users_role
   - layouts_pkey -> оставить
   - layouts_name_key -> idx_layouts_name (UNIQUE)
   - dashboards_pkey -> оставить
   - dashboards_name_key -> idx_dashboards_name (UNIQUE)
   - graphs_pkey -> оставить
   - graphs_dashboard_id_name_key -> idx_graphs_dashboard_name (UNIQUE)
   - filters_pkey -> оставить
   - filters_name_key -> idx_filters_name (UNIQUE)
   - dashboard_access_pkey -> оставить
   - idx_access_user -> idx_dashboard_access_user
   - idx_access_dashboard -> idx_dashboard_access_dashboard
   - processing_configs_pkey -> оставить
   - processing_logs_pkey -> оставить
   - aggregated_data_pkey -> оставить
   - idx_agg_dashboard_id -> idx_aggregated_data_dashboard_id
   - idx_agg_graph_id -> idx_aggregated_data_graph_id
   - idx_agg_dims_gin -> idx_aggregated_data_dims_gin
   - idx_dashboard_filter -> idx_dashboard_filters_dashboard_filter

LOGIC:

В БД есть индексы с разными стилями именования (idx_*, *_key, *_pkey)
Это затрудняет поддержку и понимание структуры
Нужно привести к единому стандарту

CONSTRAINTS:

Использовать миграцию Alembic
PK индексы обычно не переименовывают (это сделает Alembic)
UNIQUE индексы переименовать с префиксом idx_
GIN индексы тоже с префиксом idx_

DONE:

 Все индексы приведены к стандарту idx_<table>_<columns>
 В схеме БД единообразные имена
 Миграция успешно применена
