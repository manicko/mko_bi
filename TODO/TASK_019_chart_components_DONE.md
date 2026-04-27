Вот аккуратно **сокращённая версия без потери сути** (убрал повторения и “воду”, но оставил всё важное для модели):

---

## TASK: Dashboard Chart Components

### Goal

Реализовать переиспользуемые компоненты дашбордов на базе Dash + Plotly для визуализации агрегированных данных из backend API.
Поддержка: конфиг, глобальные фильтры, multi-axis, YoY.

---

## Data Contracts

### ChartData

```python
list[dict]
# {"dims": {...}, "metrics": {...}}
```

---

### ChartConfig

```python
{
    "x": str,
    "color": str | None,
    "metrics": list[str],
    "orientation": "v" | "h",
    "barmode": "group" | "stack",
    "secondary_y": list[str],
    "layout": dict,
    "yoy": {
        "enabled": bool,
        "metric": str,
        "mode": "absolute" | "percent",
        "year_field": str,
    },
}
```

---

### FilterState

```python
dict[str, list]
```

---

## Files

```
src/mko_bi/dashboards/components/
  charts/base.py
  charts/bar.py
  charts/line.py
  filters.py
  layout.py
```

---

## Components

### BaseChart (ABC)

* `build_traces(data) -> list`
* `create_figure(data) -> go.Figure`
* `update_layout(fig)`

---

### BarChart

Поддержка:

* orientation, barmode
* multi-axis (`secondary_y`)
* color grouping

Логика:

* flatten ChartData
* 1 trace на метрику
* распределение по осям

---

### LineChart

Поддержка:

* multiple lines
* YoY

YoY:

* current = max(year)
* previous year
* current → solid
* previous → dashed

---

### FilterPanel

* типы: select, multiselect, range, date
* `render()` → UI + Store
* `get_filter_values(inputs)` → FilterState

---

### DashboardLayout

* `assemble(components)`
* grid (Row/Col), responsive
* filters сверху, графики ниже

---

### ChartFactory

```python
registry = {"bar": BarChart, "line": LineChart}
```

* `create(graph_type, ...)`

---

## Constraints

* только Plotly + Dash
* без pandas (list[dict])
* без бизнес-логики в UI
* immutable data
* backend делает агрегацию

---

## Done

* BarChart: multi-axis
* LineChart: корректный YoY
* фильтры применяются ко всем графикам
* layout из config
* без дублирования

---

## Testing

Тестировать:

* BarChart (traces, axes)
* LineChart (YoY)
* FilterPanel (parsing)

Не тестировать:

* UI рендеринг
* Dash callbacks
