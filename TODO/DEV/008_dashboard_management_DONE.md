---
## BLOCK 8: DASHBOARD MANAGEMENT
---

### TASK: Layouts CRUD

FILE: `src/mkobi/api/routes/layouts.py`

GOAL: Управление layout-композициями (SPEC.md п.16.1, таблица layouts)

IMPLEMENT:

* `POST /api/v1/layouts` (admin) - создание
* `GET /api/v1/layouts` - список
* `GET /api/v1/layouts/{layout_id}` - детали
* `PUT /api/v1/layouts/{layout_id}` - обновление
* `DELETE /api/v1/layouts/{layout_id}` - удаление

Логика:
* `definition` JSONB поле содержит grid, graphs, filters, bindings
* Валидация структуры definition через Pydantic

LOGIC:

1. LayoutService для бизнес-логики
2. LayoutRepository для БД операций
3. JSONB definition: `{"grid": [...], "graphs": [...], "filters": [...], "bindings": [...]}`

DONE:

* [ ] CRUD endpoints работают
* [ ] Валидация definition
* [ ] Тесты написаны

---

### TASK: Dashboards CRUD

FILE: `src/mkobi/api/routes/dashboards.py`

GOAL: Управление дашбордами (SPEC.md п.14.2, п.16.1)

IMPLEMENT:

* `GET /api/v1/dashboards/my` - дашборды текущего пользователя (по доступам)
* `GET /api/v1/dashboards/{dashboard_id}` - детали дашборда с конфигом
* `POST /api/v1/dashboards` (admin) - создание
* `PUT /api/v1/dashboards/{dashboard_id}` (admin) - обновление
* `DELETE /api/v1/dashboards/{dashboard_id}` (admin) - удаление

Логика:
* Проверка прав (admin для CRUD, любой с доступом для чтения)
* Связь с layout_id
* created_by = current_user.id

DONE:

* [ ] Dashboard endpoints работают
* [ ] /my возвращает только доступные
* [ ] Тесты написаны

---

### TASK: Graphs CRUD

FILE: `src/mkobi/api/routes/graphs.py` (или в dashboards.py)

GOAL: Управление графиками дашборда (SPEC.md п.16.1, таблица graphs)

IMPLEMENT:

* `POST /api/v1/dashboards/{dashboard_id}/graphs` (admin)
* `GET /api/v1/dashboards/{dashboard_id}/graphs` - список графиков
* `PUT /api/v1/graphs/{graph_id}` (admin)
* `DELETE /api/v1/graphs/{graph_id}` (admin)

Graph config:
* `type`: bar, line, pie, table (GraphType StrEnum)
* `config`: JSONB (axis config, colors, display options)
* `dimensions`: JSONB (список измерений)
* `metrics`: JSONB (список метрик)

DONE:

* [ ] Graph CRUD работает
* [ ] Валидация type (enum)
* [ ] Тесты написаны

---

### TASK: Filters CRUD

FILE: `src/mkobi/api/routes/filters.py`

GOAL: Управление глобальными фильтрами (SPEC.md п.16.1, таблица filters)

IMPLEMENT:

* `POST /api/v1/filters` (admin)
* `GET /api/v1/filters` - список (переиспользуемые)
* `PUT /api/v1/filters/{filter_id}` (admin)
* `DELETE /api/v1/filters/{filter_id}` (admin)
* `POST /api/v1/dashboards/{dashboard_id}/filters` - привязка фильтра к дашборду
* `DELETE /api/v1/dashboards/{dashboard_id}/filters/{filter_id}` - отвязка

Filter config пример:
* `{"field": "year", "source": "dims", "multi": false, "type": "select"}`

DONE:

* [ ] Filter CRUD работает
* [ ] Привязка к дашборду работает
* [ ] Тесты написаны

---

### TASK: Dashboard Access management

FILE: `src/mkobi/api/routes/dashboards.py` (дополнение)

GOAL: Управление доступом user ↔ dashboard (SPEC.md п.15, таблица dashboard_access)

IMPLEMENT:

* `POST /api/v1/dashboards/{dashboard_id}/access` (admin) - выдать доступ
  * Body: `{"user_id": UUID, "permission": "view" | "edit" | "admin"}`
* `DELETE /api/v1/dashboards/{dashboard_id}/access/{user_id}` (admin) - отозвать
* `GET /api/v1/dashboards/{dashboard_id}/access` (admin) - список доступов

LOGIC:

1. Проверка существования user и dashboard
2. Уникальность (user_id, dashboard_id)
3. Permission enum (DashboardPermission)

DONE:

* [ ] Выдача доступа работает
* [ ] Отзыв работает
* [ ] Тесты написаны

---

### TASK: Dashboard service

FILE: `src/mkobi/services/dashboard_service.py`

GOAL: Бизнес-логика дашбордов

IMPLEMENT:

* `class DashboardService`:
  * `async def get_user_dashboards(user_id: UUID, db: AsyncSession) -> list[DashboardSummary]`
  * `async def get_with_config(dashboard_id: UUID, db: AsyncSession) -> DashboardDetail | None`
  * `async def create_dashboard(data: DashboardCreate, user_id: UUID, db: AsyncSession) -> DashboardResponse`
  * `async def update_dashboard(...)` 
  * `async def delete_dashboard(...)`
  * `async def grant_access(...)`
  * `async def revoke_access(...)`

DONE:

* [ ] Service методы работают
* [ ] Интеграция с API
* [ ] Тесты написаны

---
