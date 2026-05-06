---
## BLOCK 6: DATA PROCESSING
---

### TASK: Data pipeline orchestration

FILE: `src/mkobi/data/processing/registry.py` (переиспользовать или создать base.py)

GOAL: Оркестрация обработки данных (SPEC.md п.9)

IMPLEMENT:

* `class DataPipeline`:
  * `async def run(self, df: pl.DataFrame, dashboard_id: UUID, mode: UploadMode, db: AsyncSession) -> ProcessingLogResponse`:
    1. Трансформация (transform)
    2. Агрегация (aggregate)
    3. Сохранение (save to storage)
    4. Обновление processing_log статуса
  * `def _update_status(self, log_id: UUID, status: ProcessingStatus, db: AsyncSession)`

LOGIC:

1. Пайплайн выполняется асинхронно (через task queue)
2. Каждый шаг логируется
3. При ошибке - status=FAILED, message=error
4. В конце - status=COMPLETED

DONE:

* [ ] Пайплайн работает
* [ ] Статусы обновляются
* [ ] Тесты написаны

---

### TASK: Transformations

FILE: `src/mkobi/data/processing/transformations.py`

GOAL: Трансформация данных согласно конфигу (SPEC.md п.9)

IMPLEMENT:

* `def apply_transformations(df: pl.DataFrame, config: dict) -> pl.DataFrame`:
  * Фильтрация строк (where conditions)
  * Вычисляемые поля (computed columns)
  * Переименование колонок
  * Типизация колонок
* `def _apply_filters(df: pl.DataFrame, filters: list[dict]) -> pl.DataFrame`
* `def _add_computed_fields(df: pl.DataFrame, fields: list[dict]) -> pl.DataFrame`

LOGIC:

1. Использовать Polars expressions (не pandas!)
2. `df.filter()`, `df.with_columns()`
3. Поддержка различных типов фильтров (eq, gt, lt, in, etc.)
4. Вычисляемые поля через `polars.col()` expressions

DONE:

* [ ] Трансформации применяются
* [ ] Фильтры работают
* [ ] Вычисляемые поля работают
* [ ] Тесты написаны

---

### TASK: Aggregations

FILE: `src/mkobi/data/processing/aggregations.py` (или registry.py)

GOAL: Агрегация данных (SPEC.md п.9)

IMPLEMENT:

* `def aggregate_data(df: pl.DataFrame, graph_configs: list[dict]) -> list[dict]`:
  * Group by (dimensions)
  * Агрегатные функции (sum, mean, count, min, max, etc.)
  * YoY (Year-over-Year) расчеты
  * Доли (shares) расчеты
  * Кастомные метрики
* `def _calculate_yoy(df: pl.DataFrame, date_column: str, metrics: list[str]) -> pl.DataFrame`
* `def _calculate_shares(df: pl.DataFrame, share_column: str, metrics: list[str]) -> pl.DataFrame`

LOGIC:

1. Использовать `df.group_by().agg()` Polars
2. YoY: группировка по году, расчет изменений
3. Shares: доля от общего итога
4. Результат - список словарей для JSONB сохранения

DONE:

* [ ] Агрегации считаются
* [ ] YoY работает
* [ ] Shares работают
* [ ] Тесты написаны

---

### TASK: Processing configs service

FILE: `src/mkobi/services/processing_config_service.py`

GOAL: Управление настройками обработки (SPEC.md п.16.1, таблица processing_configs)

IMPLEMENT:

* `class ProcessingConfigService`:
  * `async def get_by_dashboard_id(dashboard_id: UUID, db: AsyncSession) -> ProcessingConfigResponse | None`
  * `async def upsert(dashboard_id: UUID, settings: dict, db: AsyncSession) -> ProcessingConfigResponse`
  * `async def delete(dashboard_id: UUID, db: AsyncSession) -> bool`

LOGIC:

1. Только настройки, без бизнес-логики
2. Пример settings: `{"loader": "sales_loader", "date_column": "event_date", "timezone": "UTC"}`
3. JSONB поле settings хранит произвольные настройки

DONE:

* [ ] Service методы работают
* [ ] API интеграция
* [ ] Тесты написаны

---
