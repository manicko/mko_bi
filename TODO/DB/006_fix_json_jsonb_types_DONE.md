TASK: Исправить JSON на JSONB в ORM моделях

FILE: src/mko_bi/db/models/dashboard.py, graphs.py, filters.py, processing_configs.py

GOAL: Использовать JSONB из sqlalchemy.dialects.postgresql для PostgreSQL

IMPLEMENT:

1. Обновить импорты в моделях:
   - Заменить from sqlalchemy import JSON на from sqlalchemy.dialects.postgresql import JSONB
2. Обновить колонки:
   - Dashboard.config: JSON -> JSONB
   - Graph.config, dimensions, metrics: JSON -> JSONB
   - Filter.config: JSON -> JSONB
   - ProcessingConfig.settings: JSON -> JSONB
3. Создать миграцию: alembic revision -m "Change JSON to JSONB for PostgreSQL"
4. В миграции использовать op.alter_column для изменения типа

LOGIC:

БД использует jsonb, а ORM использует JSON (generic тип)
JSONB в PostgreSQL эффективнее и поддерживает дополнительные операторы
Нужно привести ORM к использованию JSONB для лучшей совместимости

CONSTRAINTS:

Использовать sqlalchemy.dialects.postgresql.JSONB
Создать миграцию для изменения типа в БД
Для aggregated_data (dims, metrics) уже используется кастомный JSONBType - не трогать

DONE:

 ORM модели используют JSONB
 Миграция применена к bidb
 Типы колонок в БД и ORM совпадают
