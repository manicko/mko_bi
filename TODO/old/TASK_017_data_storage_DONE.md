TASK: StorageManager для агрегированных данных

FILE:
- src/mko_bi/data/storage/manager.py

GOAL:
Реализовать сохранение агрегированных данных в PostgreSQL
через единую таблицу aggregated_data (JSONB подход)

IMPLEMENT:

class: StorageManager

PUBLIC METHODS:

- save_aggregated_data(
    dashboard_id: UUID,
    graph_id: UUID,
    data: list[dict]
)

- delete_dashboard_data(dashboard_id: UUID)

- upsert_batch(data: list[dict])

LOGIC:

1. save_aggregated_data:
- оборачивается в транзакцию
- удаляет старые данные по dashboard_id
- вставляет новые агрегаты батчем

2. формат data:
[
  {
    "graph_id": UUID,
    "dims": {...},
    "metrics": {...}
  }
]

3. insert:
- использовать batch insert (SQLAlchemy Core)
- не использовать ORM для массовых операций

4. delete:
- DELETE FROM aggregated_data WHERE dashboard_id = ...
- chunk size = 1000 для batch insert

5. индексы:
- учитывать наличие GIN индекса на dims
- использовать graph_id и dashboard_id

CONSTRAINTS:

- НЕ создавать динамические таблицы
- использовать существующую таблицу aggregated_data
- использовать SQLAlchemy Core (не ORM для batch)
- использовать транзакции
- код должен быть идемпотентным

ERROR HANDLING:

- rollback при ошибке
- логирование ошибок

DONE:

- данные сохраняются корректно
- старые данные удаляются
- batch insert работает
- транзакции работают
- Данные консистентны
- Тесты покрывают операции сохранения
 - Тесты: нужны только глубоко тестирующие бизнес-логику.
