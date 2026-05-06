---
## BLOCK 7: DATA STORAGE
---

### TASK: Storage manager

FILE: `src/mkobi/data/storage/manager.py`

GOAL: Сохранение агрегированных данных в PostgreSQL (SPEC.md п.10)

IMPLEMENT:

* `class StorageManager`:
  * `async def save_aggregated_data(dashboard_id: UUID, graph_id: UUID, aggregated_results: list[dict], mode: UploadMode, db: AsyncSession) -> None`:
    * При OVERWRITE: удаление старых данных для graph_id
    * При APPEND: добавление новых данных
    * Сохранение в aggregated_data таблицу
  * `async def delete_by_graph(graph_id: UUID, db: AsyncSession) -> None`
  * `async def delete_by_dashboard(dashboard_id: UUID, db: AsyncSession) -> None`

LOGIC:

1. Использовать AggregatedDataRepository
2. JSONB для dims и metrics
3. Массовая вставка (bulk insert) для производительности
4. Транзакция на весь save

DONE:

* [ ] Сохранение работает
* [ ] Overwrite режим работает
* [ ] Append режим работает
* [ ] Тесты написаны

---

### TASK: Aggregated data repository

FILE: `src/mkobi/db/repositories/aggregated_data_repo.py`

GOAL: Репозиторий для работы с aggregated_data (SPEC.md п.16.1)

IMPLEMENT:

* `class AggregatedDataRepository(BaseRepository[AggregatedData])`:
  * `async def get_by_graph_id(graph_id: UUID, filters: dict | None = None) -> list[AggregatedData]`
  * `async def get_by_dashboard_id(dashboard_id: UUID) -> list[AggregatedData]`
  * `async def delete_by_graph_id(graph_id: UUID) -> None`
  * `async def delete_by_dashboard_id(dashboard_id: UUID) -> None`
  * `async def bulk_insert(records: list[dict]) -> None`
  * `async def get_dims_values(graph_id: UUID, dim_name: str) -> list[str]` (для фильтров)

LOGIC:

1. Использовать `sqlalchemy.future.select()`
2. Фильтрация по JSONB полям (dims) через `column.op('->>')` или GIN индекс
3. Bulk insert через `insert().values()`

DONE:

* [ ] Repository методы работают
* [ ] Фильтрация по JSONB работает
* [ ] Тесты написаны

---

### TASK: Data API endpoint

FILE: `src/mkobi/api/routes/data.py`

GOAL: Endpoint для получения агрегированных данных (SPEC.md п.14.3)

IMPLEMENT:

* `GET /api/v1/data/aggregated?dashboard_id=:id&filters=...`:
  * `dashboard_id: UUID` (query param)
  * `filters: str | None` (JSON string, опционально)
  * `current_user: User = Depends(get_current_user)`
  * Response: `list[GraphDataResponse]` (данные для всех графиков дашборда)
  * Логика:
    1. Проверка доступа пользователя к дашборду
    2. Получение конфигурации графиков
    3. Загрузка aggregated_data с применением фильтров
    4. Форматирование для React (Plotly.js)

LOGIC:

1. Фильтры приходят как JSON: `{"year": 2024, "category": "Electronics"}`
2. Применение фильтров к JSONB полю `dims`
3. Группировка данных по graph_id
4. Формат ответа: `{"graphs": [{"graph_id": "...", "data": [...]}]}`

DONE:

* [ ] Endpoint возвращает данные
* [ ] Фильтры применяются
* [ ] Проверка доступа работает
* [ ] Тесты написаны

---
