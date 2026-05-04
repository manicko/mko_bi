TASK: Реализация multi-axis графиков

FILE: src/mko_bi/dashboards/components/charts/
FILE: src/mko_bi/dash_app.py

GOAL: Поддержка отображения нескольких метрик на разных осях (SPEC.md п.176)

IMPLEMENT:

func: добавление поддержки secondary_y в графики

LOGIC:

1. Создать конфигурацию для multi-axis в моделях графиков:
   - Добавить поле `secondary_y: list[str] | None` в Graph конфигурацию
   - Указывать какие метрики отображать на вторичной оси Y

2. Обновить функции создания графиков:
   - `_create_line_chart()` - поддержка secondary axis через `go.Layout(secondary_y=...)`
   - Использовать `make_subplots()` если требуется полноценная поддержка

3. Пример реализации для Plotly:
```
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(..., yaxis="y"), secondary_y=False)
fig.add_trace(go.Scatter(..., yaxis="y2"), secondary_y=True)
```

4. Обновить Dash callbacks для поддержки multi-axis конфигурации

CONSTRAINTS:

- Выполняется ПОСЛЕ TASK-007 (Dash real data)
- Использовать стандартные возможности Plotly
- Не усложнять архитектуру ради редкого кейса (если не требуется часто)
- Конфигурация должна храниться в БД (таблица graphs)

DONE:

- Multi-axis графики отображаются корректно
- Конфигурация secondary_y сохраняется в БД
- Существующие одноосевые графики не сломаны
- `uv run ruff check .` проходит

TEST:

# Создать график с multi-axis через API
# Проверить отображение в Dash
uv run pytest tests/ -k "graph" -v
