````md
# TASK: Dashboard Chart Components (Improved Version)

##  Goal
Реализовать переиспользуемые компоненты дашбордов на базе Dash + Plotly для визуализации агрегированных данных из backend API.  
Компоненты должны быть конфигурируемыми, поддерживать глобальные фильтры, multi-axis графики и YoY анализ.

---

## Data Contracts

### 1. ChartData (из API)
```python
ChartData = list[dict]

# пример:
[
    {
        "dims": {"year": 2023, "category": "A"},
        "metrics": {"revenue": 1000, "profit": 200}
    },
    {
        "dims": {"year": 2024, "category": "A"},
        "metrics": {"revenue": 1200, "profit": 250}
    }
]
````

---

### 2. ChartConfig

```python
ChartConfig = {
    "x": "year",
    "color": "category",  # optional
    "metrics": ["revenue", "profit"],
    "orientation": "v",  # v | h
    "barmode": "group",  # group | stack
    "secondary_y": ["profit"],  # метрики для правой оси
    "layout": {},
    "yoy": {
        "enabled": True,
        "metric": "revenue",
        "mode": "absolute",  # absolute | percent
        "year_field": "year",
    },
}
```

---

### 3. FilterState

```python
FilterState = {"year": [2023, 2024], "category": ["A", "B"], "brand": ["X"]}
```

---

##  File Structure

```
src/mko_bi/dashboards/components/
    charts/
        base.py
        bar.py
        line.py
    filters.py
    layout.py
```

---

## Components

---

### 1. `charts/base.py`

```python
class BaseChart(ABC):
    def __init__(self, graph_id: str, config: dict):
        self.graph_id = graph_id
        self.config = config

    @abstractmethod
    def build_traces(self, data: ChartData) -> list:
        pass

    def create_figure(self, data: ChartData) -> go.Figure:
        traces = self.build_traces(data)
        fig = go.Figure(data=traces)
        self.update_layout(fig)
        return fig

    def update_layout(self, fig: go.Figure) -> None:
        fig.update_layout(**self.config.get("layout", {}))
```

---

### 2. `charts/bar.py`

```python
class BarChart(BaseChart):
```

#### Features:

* vertical / horizontal (`orientation`)
* grouped / stacked (`barmode`)
* multi-axis (left + right Y)

#### Logic:

* преобразовать ChartData → плоскую структуру
* построить trace на каждую метрику
* распределить метрики по осям (`secondary_y`)
* поддержка color grouping

---

### 3. `charts/line.py`

```python
class LineChart(BaseChart):
```

#### Features:

* multiple lines
* markers / smoothing / fill
* YoY линии

#### YoY Logic:

* определить текущий год (max)
* взять предыдущий год
* построить:

  * текущий → solid line
  * предыдущий → dashed line

---

### 4. `filters.py`

```python
class FilterPanel:
    def __init__(self, filter_configs: list[dict], store_id: str = "filter-store"):
        self.filter_configs = filter_configs
        self.store_id = store_id
```

#### Supported filter types:

* select
* multiselect
* range
* date

#### Methods:

```python
def render(self) -> html.Div
```

* создаёт UI + `dcc.Store`

```python
def get_filter_values(self, inputs: dict) -> dict
```

* преобразует Dash inputs → FilterState

---

### 5. `layout.py`

```python
class DashboardLayout:
    def __init__(self, layout_config: dict, store_id: str = "filter-store"):
        self.layout_config = layout_config
        self.store_id = store_id
```

#### Layout config:

```json
{
  "cells": [
    {"component_id": "bar-chart", "width": 6},
    {"component_id": "line-chart", "width": 6},
    {"component_id": "filter-panel", "width": 12}
  ]
}
```

#### Method:

```python
def assemble(self, components: dict) -> dbc.Container
```

#### Logic:

* использовать `dbc.Row` / `dbc.Col`
* responsive layout
* filters сверху
* графики ниже

---

##  Chart Factory (обязательно)

```python
class ChartFactory:
    registry = {"bar": BarChart, "line": LineChart}

    @classmethod
    def create(cls, graph_type: str, *args, **kwargs):
        return cls.registry[graph_type](*args, **kwargs)
```

---

## Constraints

* Plotly only
* Dash only
* без pandas (использовать list[dict])
* без сложной логики в UI
* immutable data processing
* backend отвечает за агрегацию

---

## Optional

* экспорт графиков:

```python
fig.write_image("chart.png")
```

(через kaleido)

---

##  Done Criteria

* BarChart поддерживает multi-axis
* LineChart корректно строит YoY
* фильтры применяются ко всем графикам
* layout соответствует config
* компоненты переиспользуемые
* код без дублирования

---

##  Testing

Тестировать:

### BarChart

* корректное разбиение на traces
* распределение по осям

### LineChart

* корректный YoY
* сортировка данных

### FilterPanel

* корректный parsing state

 НЕ тестировать:

* UI рендеринг
* Dash callbacks
