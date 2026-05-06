"""Модуль управления дашбордами.

Этот пакет содержит базовые классы, реестр и реализации
конкретных дашбордов для системы BI-аналитики.
"""

from mkobi.dashboards.base import DashboardBase
from mkobi.dashboards.registry import DashboardRegistry, registry, register
from mkobi.dashboards.components import (
    BaseChart,
    BarChart,
    LineChart,
    FilterPanel,
    DashboardLayout,
)

__all__ = [
    "DashboardBase",
    "DashboardRegistry",
    "registry",
    "register",
    "BaseChart",
    "BarChart",
    "LineChart",
    "FilterPanel",
    "DashboardLayout",
]