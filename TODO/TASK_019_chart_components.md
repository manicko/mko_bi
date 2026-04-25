TASK: Компоненты графиков дашбордов

FILE: src/mko_bi/dashboards/components/charts/bar.py
FILE: src/mko_bi/dashboards/components/charts/dot.py
FILE: src/mko_bi/dashboards/components/filters.py
FILE: src/mko_bi/dashboards/components/layout.py

GOAL: Реализовать компоненты для визуализации данных

IMPLEMENT:

class: BarChart
class: LineChart (в dot.py)
class: FilterPanel
class: DashboardLayout

LOGIC:
- BarChart: bar chart через Plotly с поддержкой multi-axis
- LineChart: line chart с YoY линиями
- FilterPanel: глобальные фильтры (year, category, brand)
- DashboardLayout: компоновка графиков и фильтров

CONSTRAINTS:
- Использовать Plotly для графиков
- Поддержка комбинированных графиков
- Фильтры применяются ко всем графикам
- Responsive layout
- Экспорт в PNG (опционально)

DONE:
- BarChart рендерит столбчатые диаграммы
- LineChart рендерит линейные графики
- FilterPanel предоставляет интерфейс фильтрации
- DashboardLayout компонует элементы
- Графики интерактивные