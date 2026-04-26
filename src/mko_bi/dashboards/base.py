"""Базовый класс для дашбордов.

Этот модуль предоставляет абстрактный базовый класс для всех дашбордов,
определяющий интерфейс и базовое поведение.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from mko_bi.models.dashboard import DashboardConfig

logger = logging.getLogger(__name__)


class DashboardBase(ABC):
    """Абстрактный базовый класс для дашбордов.

    Все конкретные реализации дашбордов должны наследоваться от этого класса
    и реализовывать все абстрактные методы.

    Attributes:
        config: Конфигурация дашборда типа DashboardConfig
    """

    def __init__(self, config: DashboardConfig) -> None:
        """Инициализация базового дашборда.

        Args:
            config: Конфигурация дашборда
        """
        self.config = config
        logger.info(
            "Создан экземпляр дашборда %s с конфигурацией: %s",
            self.__class__.__name__,
            config.title or "Без названия",
        )

    @abstractmethod
    def get_data(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Получение данных для дашборда с применением фильтров.

        Этот метод должен быть реализован в конкретных классах дашбордов
        для получения данных из источника (база данных, API, файлы и т.д.)
        с учетом переданных фильтров.

        Args:
            filters: Словарь фильтров, где ключ - имя фильтра,
                     значение - значение фильтра

        Returns:
            Список словарей с данными. Каждый словарь представляет
            одну запись/точку данных.

        Example:
            >>> dashboard.get_data({"year": 2024, "category": "electronics"})
            [{"category": "electronics", "revenue": 100000}, ...]
        """
        ...

    @abstractmethod
    def apply_filters(self, data: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Применение фильтров к уже полученным данным.

        Этот метод фильтрует данные на стороне приложения, когда
        фильтрация на уровне источника данных невозможна или неэффективна.

        Args:
            data: Список словарей с данными для фильтрации
            filters: Словарь фильтров, где ключ - имя поля,
                     значение - значение для фильтрации

        Returns:
            Отфильтрованный список словарей с данными

        Example:
            >>> data = [{"year": 2023, "revenue": 100}, {"year": 2024, "revenue": 200}]
            >>> dashboard.apply_filters(data, {"year": 2024})
            [{"year": 2024, "revenue": 200}]
        """
        ...

    @abstractmethod
    def render(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Рендеринг данных в формат для отображения.

        Преобразует сырые данные в формат, готовый для отображения
        в веб-интерфейсе (например, в формате Plotly или табличном виде).

        Args:
            data: Список словарей с данными для рендеринга

        Returns:
            Словарь с отрендеренными данными, готовыми для передачи
            во фронтенд. Структура зависит от типа дашборда.

        Example:
            >>> data = [{"category": "A", "value": 100}, {"category": "B", "value": 200}]
            >>> dashboard.render(data)
            {"type": "bar", "data": {...}, "layout": {...}}
        """
        ...