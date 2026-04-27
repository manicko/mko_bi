"""Базовый класс для всех компонентов графиков.

Этот модуль предоставляет абстрактный базовый класс для создания
переиспользуемых компонентов визуализации на базе Plotly.
"""

import logging
from abc import ABC, abstractmethod

import plotly.graph_objects as go
from mko_bi.models.data import ChartConfig, ChartData

logger = logging.getLogger(__name__)


class BaseChart(ABC):
    """Абстрактный базовый класс для компонентов графиков.

    Все конкретные реализации графиков должны наследоваться от этого класса
    и реализовывать все абстрактные методы.

    Атрибуты:
        config: Конфигурация графика типа ChartConfig
    """

    def __init__(self, config: ChartConfig) -> None:
        """Инициализация базового графика.

        Args:
            config: Конфигурация графика
        """
        self.config = config
        logger.info(
            "Создан экземпляр графика %s с конфигурацией: x=%s, metrics=%s",
            self.__class__.__name__,
            config.x,
            config.metrics,
        )

    @abstractmethod
    def build_traces(self, data: ChartData) -> list[go.Scatter | go.Bar]:
        """Построение трасс (следов) для графика.

        Этот метод должен быть реализован в конкретных классах графиков
        для создания набора трасс Plotly на основе входных данных.

        Args:
            data: Данные для графика в формате ChartData

        Returns:
            Список объектов трасс Plotly (Scatter, Bar и т.д.)

        Example:
            >>> chart = BarChart(config)
            >>> traces = chart.build_traces(data)
            >>> len(traces)  # Количество трасс
            3
        """
        ...

    @abstractmethod
    def create_figure(self, data: ChartData) -> go.Figure:
        """Создание фигуры Plotly.

        Создает полную фигуру Plotly с трассами и базовым макетом.

        Args:
            data: Данные для графика в формате ChartData

        Returns:
            Объект фигуры Plotly

        Example:
            >>> chart = LineChart(config)
            >>> fig = chart.create_figure(data)
            >>> fig.show()
        """
        ...

    def update_layout(self, fig: go.Figure) -> go.Figure:
        """Обновление макета фигуры.

        Применяет настройки макета из конфигурации к фигуре.
        Может быть переопределен в дочерних классах для
        специфических настроек.

        Args:
            fig: Объект фигуры Plotly

        Returns:
            Обновленный объект фигуры Plotly

        Example:
            >>> fig = chart.create_figure(data)
            >>> fig = chart.update_layout(fig)
        """
        if self.config.layout:
            fig.update_layout(**self.config.layout)

        # Применяем оси по умолчанию, если не заданы
        if not fig.layout.xaxis.title.text:
            fig.update_xaxes(title_text=self.config.x)

        logger.debug(
            "Макет графика %s обновлен",
            self.__class__.__name__,
        )
        return fig