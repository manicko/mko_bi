TASK: Создать недостающие таблицы БД: filters, processing_configs, processing_logs

FILE: src/mko_bi/db/models/filters.py, src/mko_bi/db/models/processing_configs.py, src/mko_bi/db/models/processing_logs.py, src/mko_bi/db/repositories/, create_db.sql

GOAL: Создать таблицы БД, требуемые по SPEC.md, с моделями, репозиториями и миграциями

IMPLEMENT:

func: create_filter()
func: get_filter()
func: update_filter()
func: delete_filter()
func: create_processing_config()
func: get_processing_config()
func: update_processing_config()
func: create_processing_log()
func: update_processing_log_status()

LOGIC:

1. Модель Filter (filters):
   - id: UUID PK
   - name: TEXT UNIQUE NOT NULL
   - type: TEXT NOT NULL (select/multiselect/range/date)
   - config: JSONB NOT NULL
   - created_at: TIMESTAMP
2. Модель ProcessingConfig (processing_configs):
   - dashboard_id: UUID PK FK → dashboards
   - settings: JSONB NOT NULL
   - updated_at: TIMESTAMP
3. Модель ProcessingLog (processing_logs):
   - id: UUID PK
   - dashboard_id: UUID FK → dashboards
   - status: TEXT CHECK (started/success/failed)
   - message: TEXT
   - started_at: TIMESTAMP
   - finished_at: TIMESTAMP
4. Репозитории для каждой таблицы:
   - CRUD операции
   - Обработка ошибок
   - Транзакции
5. Обновить create_db.sql:
   - Добавить CREATE TABLE скрипты
   - Добавить индексы

CONSTRAINTS:

- Соблюдать структуру из SPEC.md
- Внешние ключи с ON DELETE CASCADE
- Индексы на часто запрашиваемые поля
- Корректные связи между таблицами
- Использовать SQLAlchemy ORM

DONE:

- Таблицы созданы в БД
- Модели соответствуют SPEC
- Репозитории реализуют CRUD
- Миграции настроены

