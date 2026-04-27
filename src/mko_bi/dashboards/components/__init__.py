"""Компоненты дашбордов.

Этот пакет содержит переиспользуемые компоненты для построения дашбордов:
- Графики (базовый класс, столбчатые, линейные, круговые, таблицы)
- Панель фильтров
- Макет дашборда
"""

from mko_bi.dashboards.components.charts.bar import BarChart
from mko_bi.dashboards.components.charts.base import BaseChart
from mko_bi.dashboards.components.charts.line import LineChart
from mko_bi.dashboards.components.charts.pie import PieChart
from mko_bi.dashboards.components.charts.table import TableChart
from mko_bi.dashboards.components.filters import FilterPanel
from mko_bi.dashboards.components.layout import DashboardLayout

__all__ = [
    "BaseChart",
    "BarChart",
    "LineChart",
    "PieChart",
    "TableChart",
    "FilterPanel",
    "DashboardLayout",
]