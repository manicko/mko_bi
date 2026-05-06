---
## BLOCK 14: FRONTEND DASHBOARDS
---

### TASK: Dashboard list page

FILE: `frontend/src/features/dashboards/ui/DashboardList.tsx`

GOAL: Список дашбордов пользователя (SPEC_FRONTEND.md п.4.3)

IMPLEMENT:

* Заголовок "Мои дашборды"
* Список карточек/таблица с дашбордами
* Каждая карточка: название, описание, ссылка "Открыть"
* Ссылка на профиль (header)

LOGIC:

1. GET /api/v1/dashboards/my (TanStack Query)
2. Рендер списка
3. Клик → navigate to /dashboard/:id

DONE:

* [ ] Список загружается
* [ ] Карточки рендерятся
* [ ] Навигация работает

---

### TASK: Dashboard view page

FILE: `frontend/src/features/dashboards/ui/DashboardView.tsx`

GOAL: Просмотр графиков дашборда (SPEC_FRONTEND.md п.4.6)

IMPLEMENT:

* Заголовок дашборда
* **Filters Panel** (слева/сверху):
  * Select/Range/Date фильтры (динамически по конфигу)
* **Charts Grid** (основная область):
  * Графики (Plotly.js React)
  * Таблицы
* **Upload Button** (видна для editor+)

LOGIC:

1. GET /api/v1/dashboards/:id (конфигурация)
2. GET /api/v1/data/aggregated?dashboard_id=:id&filters=...
3. Рендер графиков согласно config (layout, graphs)
4. При изменении фильтров → invalidate query

DONE:

* [ ] Конфиг загружается
* [ ] Графики рендерятся
* [ ] Фильтры работают
* [ ] Upload button видна для editor+

---

### TASK: Dashboard filters component

FILE: `frontend/src/features/dashboards/ui/DashboardFilters.tsx`

GOAL: Панель фильтров (SPEC_FRONTEND.md п.4.6)

IMPLEMENT:

* Динамический рендер фильтров на основе dashboard config
* Типы: Select, Multiselect, Range, Date
* Применение фильтров → обновление данных графиков

LOGIC:

1. Чтение config.dashboard_filters
2. Для каждого фильтра: определение типа, рендер соответствующего компонента
3. Изменение фильтра → вызов onFiltersChange callback

DONE:

* [ ] Фильтры рендерятся
* [ ] Типы фильтров работают
* [ ] Данные обновляются

---

### TASK: Plotly chart components

FILE: `frontend/src/features/dashboards/ui/charts/`

GOAL: Компоненты для графиков (SPEC_FRONTEND.md п.2.1)

IMPLEMENT:

* `PlotlyChart.tsx` - обертка над react-plotly.js
* `BarChart.tsx`, `LineChart.tsx`, `PieChart.tsx`, `TableChart.tsx`
* Поддержка multi-axis, combined charts, YoY

LOGIC:

1. Использовать `react-plotly.js` компонент
2. Данные форматируются согласно graph type
3. Layout из graph.config

DONE:

* [ ] Графики рендерятся
* [ ] Все типы работают
* [ ] Multi-axis работает

---

### TASK: Dashboards API

FILE: `frontend/src/features/dashboards/api/dashboardApi.ts`

GOAL: API функции для дашбордов

IMPLEMENT:

* `getMyDashboards(): Promise<DashboardSummary[]>`
* `getDashboard(id: string): Promise<DashboardDetail>`
* `getAggregatedData(dashboardId: string, filters?: object): Promise<GraphData[]>`

LOGIC:

1. TanStack Query hooks: useQuery для загрузки
2. Инвалидация кэша при изменении фильтров

DONE:

* [ ] API функции работают
* [ ] Query hooks работают

---
