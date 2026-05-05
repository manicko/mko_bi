TASK: Add updated_at triggers for tables

FILE: alembic/versions/*.py, src/mko_bi/models/*.py

GOAL: Automatically update updated_at on row modifications

IMPLEMENT:

sql: CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

sql: CREATE TRIGGER update_dashboards_updated_at
BEFORE UPDATE ON dashboards
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

Tables needing updated_at trigger:
- dashboards (has updated_at column)
- processing_configs (has updated_at column)
- layouts (recommended)
- graphs (recommended)
- users (recommended)

LOGIC:

1. Create PostgreSQL function to update updated_at
2. Create triggers on tables with updated_at column
3. Function reuses the same logic for all tables

CONSTRAINTS:

только для таблиц с полем updated_at
использовать IF NOT EXISTS для триггеров
убедиться что колонка updated_at существует перед созданием триггера

DONE:

 функция update_updated_at_column создана
 триггеры добавлены на нужные таблицы
 тест: проверка что updated_at обновляется при UPDATE
