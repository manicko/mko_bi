"""Круговая диаграмма.

Этот модуль предоставляет реализацию компонента PieChart
для визуализации агрегированных данных в виде круговой диаграммы.

Поддерживает:
- Группировку по цвету
- Отображение процентов
- Настройку макета
"""

import logging

import plotly.graph_objects as go
from mko_bi.models.data import ChartConfig, ChartData

from .base import BaseChart

logger = logging.getLogger(__name__)


class PieChart(BaseChart):
    """Круговая диаграмма.

    Реализует круговую диаграмму с поддержкой:
    - Группировки по цвету
    - Отображения процентов
    - Настройки макета

    Логика работы:
    1. Группирует данные по измерениям
    2. Суммирует метрики для каждой группы
    3. Строит сектора пропорционально значениям метрик
    """

    def __init__(self, config: ChartConfig) -> None:
        """Инициализация круговой диаграммы.

        Args:
            config: Конфигурация графика
        """
        super().__init__(config)
        self._validate_config()

    def _validate_config(self) -> None:
        """Проверка валидности конфигурации.

        Raises:
            ValueError: Если конфигурация некорректна
        """
        if not self.config.metrics:
            raise ValueError("Список метрик не может быть пустым")

        if len(self.config.metrics) > 1:
            logger.warning(
                "Для круговой диаграммы задано несколько метрик. "
                "Будет использована только первая: %s",
                self.config.metrics[0],
            )

    def _prepare_data(self, data: ChartData) -> dict[str, float]:
        """Подготовка данных для круговой диаграммы.

        Группирует данные по измерениям и суммирует метрики.

        Args:
            data: Исходные данные

        Returns:
            Словарь с ключами (строковое представление измерений)
            и суммированными значениями метрик
        """
        grouped: dict[str, float] = {}
        metric = self.config.metrics[0]

        for item in data.data:
            # Формируем ключ на основе измерений
            if self.config.color:
                key = str(item.get(self.config.color, ""))
            else:
                # Если нет поля для группировки, используем все измерения
                key_parts = []
                for field in item.keys():
                    if field != metric:
                        key_parts.append(f"{field}:{item.get(field)}")
                key = " | ".join(key_parts) if key_parts else "Total"

            if key not in grouped:
                grouped[key] = 0
            grouped[key] += item.get(metric, 0)

        logger.debug("Данные сгруппированы: %d категорий", len(grouped))
        return grouped

    def build_traces(self, data: ChartData) -> list[go.Pie]:
        """Построение трасс для круговой диаграммы.

        Создает единственную трассу типа Pie с секторами
        для каждой категории данных.

        Args:
            data: Данные для графика

        Returns:
            Список с одной объектом Pie
        """
        grouped_data = self._prepare_data(data)

        if not grouped_data:
            logger.warning("Нет данных для построения круговой диаграммы")
            return [go.Pie(labels=["Нет данных"], values=[0])]

        labels = list(grouped_data.keys())
        values = list(grouped_data.values())

        trace = go.Pie(
            labels=labels,
            values=values,
            hole=0 if not self.config.layout.get("hole") else self.config.layout["hole"],
            textinfo="label+percent" if self.config.layout.get("show_percent", True) else "label+value",
            textposition="auto",
        )

        logger.info(
            "Построена круговая диаграмма: %d секторов, сумма=%s",
            len(labels),
            sum(values),
        )

        return [trace]

    def create_figure(self, data: ChartData) -> go.Figure:
        """Создание фигуры круговой диаграммы.

        Args:
            data: Данные для графика

        Returns:
            Объект фигуры Plotly
        """
        traces = self.build_traces(data)
        fig = go.Figure(data=traces)

        # Настройка макета
        fig.update_layout(
            showlegend=self.config.layout.get("show_legend", True),
        )

        fig = self.update_layout(fig)

        logger.info("Фигура круговой диаграммы создана")
        return fig

    def update_layout(self, fig: go.Figure) -> go.Figure:
        """Обновление макета круговой диаграммы.

        Args:
            fig: Объект фигуры Plotly

        Returns:
            Обновленный объект фигуры Plotly
        """
        fig = super().update_layout(fig)

        # Применяем заголовок по умолчанию, если не задан
        if not fig.layout.title.text:
            metric = self.config.metrics[0] if self.config.metrics else "value"
            title_parts = [metric]
            if self.config.color:
                title_parts.append(f"by {self.config.color}")
            fig.update_layout(title=" ".join(title_parts))

        return fig
