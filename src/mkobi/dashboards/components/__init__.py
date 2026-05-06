"""Компоненты дашбордов.

Этот пакет содержит переиспользуемые компоненты для построения дашбордов:
- Графики (базовый класс, столбчатые, линейные, круговые, таблицы)
- Панель фильтров
- Макет дашборда
"""

from mkobi.dashboards.components.charts.bar import BarChart
from mkobi.dashboards.components.charts.base import BaseChart
from mkobi.dashboards.components.charts.line import LineChart
from mkobi.dashboards.components.charts.pie import PieChart
from mkobi.dashboards.components.charts.table import TableChart
from mkobi.dashboards.components.filters import FilterPanel
from mkobi.dashboards.components.layout import DashboardLayout

__all__ = [
    "BaseChart",
    "BarChart",
    "LineChart",
    "PieChart",
    "TableChart",
    "FilterPanel",
    "DashboardLayout",
]