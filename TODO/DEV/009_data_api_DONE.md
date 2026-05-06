---
## BLOCK 9: DATA API (детально)
---

### TASK: Aggregated data formatting for React

FILE: `src/mkobi/services/data_service.py`

GOAL: Форматирование агрегированных данных для Plotly.js React (SPEC_FRONTEND.md п.4.6)

IMPLEMENT:

* `def format_for_plotly(graph_config: dict, data: list[dict]) -> dict`:
  * Bar chart: `{x: [], y: [], type: 'bar'}`
  * Line chart: `{x: [], y: [], type: 'scatter', mode: 'lines+markers'}`
  * Pie chart: `{labels: [], values: [], type: 'pie'}`
  * Table: `{columns: [], data: []}`
* `def apply_filters_to_dims(data: list[dict], filters: dict) -> list[dict]`:
  * Фильтрация по JSONB полю dims
  * Поддержка multiple values для фильтров

LOGIC:

1. Преобразование из БД формата (dims JSONB, metrics JSONB) в Plotly format
2. Обработка multi-axis графиков
3. YoY overlay (две линии на одном графике)
4. Комбинированные графики (bar + line)

DONE:

* [x] Форматирование работает для всех типов графиков
* [x] Filters применяются
* [x] Тесты написаны

---

### TASK: Filters application (backend)

FILE: `src/mkobi/services/data_service.py` (дополнение)

GOAL: Применение глобальных фильтров через backend (SPEC.md п.13)

IMPLEMENT:

* `async def get_filtered_data(dashboard_id: UUID, filters: dict, db: AsyncSession) -> dict`:
  * Загрузка всех графиков дашборда
  * Для каждого графика: загрузка aggregated_data
  * Применение фильтров к dims полю
  * Форматирование для React
* `def build_filter_conditions(filters: dict) -> list[Any]`:
  * Использовать SQLAlchemy для JSONB фильтрации
  * `AggregatedData.dims.op('->>')(key) == value`

LOGIC:

1. Глобальные фильтры: year, category, brand
2. Применяются ко всем графикам дашборда
3. SQL WHERE clause через parameterized queries (безопасно)
4. GIN индекс на dims для производительности

DONE:

* [x] Фильтры применяются корректно
* [x] SQL инъекции невозможны
* [x] Тесты написаны

---
