TASK: Создать таблицу dashboard_filters

FILE: alembic/versions/

GOAL: Создать отсутствующую таблицу для связи dashboards и filters

IMPLEMENT:

1. Создать миграцию: alembic revision -m "Create dashboard_filters table"
2. В миграции создать таблицу:
   - dashboard_id: UUID, FK to dashboards(id) ON DELETE CASCADE, PK
   - filter_id: UUID, FK to filters(id) ON DELETE CASCADE, PK
   - Составной первичный ключ (dashboard_id, filter_id)
   - Индекс idx_dashboard_filter на (dashboard_id, filter_id)
3. Применить миграцию: alembic upgrade head

LOGIC:

Таблица dashboard_filters определена в ORM (filters.py) но отсутствует в БД
Это ломает many-to-many связь между dashboards и filters
Связь используется в Dashboard.filters и Filter.dashboards

CONSTRAINTS:

Использовать миграцию Alembic
Соблюдать внешние ключи с ON DELETE CASCADE
Создать составной первичный ключ

DONE:

 Таблица dashboard_filters создана в БД
 Связь между dashboards и filters работает
 Миграция успешно применена
