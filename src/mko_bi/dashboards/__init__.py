"""Модуль управления дашбордами.

Этот пакет содержит базовые классы, реестр и реализации
конкретных дашбордов для системы BI-аналитики.
"""

from mko_bi.dashboards.base import DashboardBase
from mko_bi.dashboards.registry import DashboardRegistry, registry, register

__all__ = [
    "DashboardBase",
    "DashboardRegistry",
    "registry",
    "register",
]