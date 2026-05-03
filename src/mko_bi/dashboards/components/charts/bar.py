"""Столбчатая диаграмма.

Этот модуль предоставляет реализацию компонента BarChart
для визуализации агрегированных данных в виде столбчатой диаграммы.

Поддерживает:
- Вертикальную и горизонтальную ориентацию
- Группировку и наложение (barmode)
- Несколько осей Y (secondary_y)
- Группировку по цвету (color)
"""

# mypy: ignore-errors

import logging
from typing import Any

import plotly.graph_objects as go
from mko_bi.models.data import ChartConfig, ChartData
from mko_bi.models.user_roles import OrientationEnum

from .base import BaseChart

logger = logging.getLogger(__name__)


class BarChart(BaseChart):
    """Столбчатая диаграмма.

    Реализует столбчатую диаграмму с поддержкой:
    - Множественных осей Y
    - Группировки по цвету
    - Различных режимов отображения (группировка/наложение)
    - Вертикальной и горизонтальной ориентации

    Логика работы:
    1. Выполняет flatten входных данных
    2. Создает 1 трассу на каждую метрику
    3. Распределяет трассы по осям (основная и дополнительные)
    4. Применяет настройки ориентации и barmode
    """

    def __init__(self, config: ChartConfig) -> None:
        """Инициализация столбчатой диаграммы.

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

        if not self.config.x:
            raise ValueError("Поле 'x' должно быть задано")

        # Проверка, что метрики для secondary_y есть в списке metrics
        if self.config.secondary_y:
            for metric in self.config.secondary_y:
                if metric not in self.config.metrics:
                    logger.warning(
                        "Метрика '%s' из secondary_y отсутствует в списке metrics",
                        metric,
                    )

    def _flatten_data(self, data: ChartData) -> list[dict[str, Any]]:
        """Преобразование данных в плоский формат.

        Гарантирует, что все записи содержат все необходимые поля.
        Заполняет отсутствующие значения нулями.

        Args:
            data: Исходные данные

        Returns:
            Плоский список словарей с данными
        """
        flattened = []
        for item in data.data:
            flat_item = {
                self.config.x: item.get(self.config.x),
            }

            # Добавляем поле цвета, если задано
            if self.config.color:
                flat_item[self.config.color] = item.get(self.config.color)

            # Добавляем все метрики
            for metric in self.config.metrics:
                flat_item[metric] = item.get(metric, 0)

            flattened.append(flat_item)

        logger.debug("Данные преобразованы в плоский формат: %d записей", len(flattened))
        return flattened

    def _group_by_key(self, flattened_data: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Группировка данных по ключу (x + color).

        Args:
            flattened_data: Плоский список данных

        Returns:
            Словарь группированных данных
        """
        grouped: dict = {}
        for item in flattened_data:
            key_parts = [str(item.get(self.config.x, ""))]

            if self.config.color:
                key_parts.append(str(item.get(self.config.color, "")))

            key = "|".join(key_parts)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)

        return grouped

    def build_traces(self, data: ChartData) -> list[go.Bar]:
        """Построение трасс для столбчатой диаграммы.

        Создает отдельную трассу для каждой метрики.
        Метрики, указанные в secondary_y, размещаются на второй оси Y.

        Args:
            data: Данные для графика

        Returns:
            Список объектов Bar (трасс)
        """
        flattened = self._flatten_data(data)
        traces = []

        # Получаем уникальные значения для оси X
        x_values = list({item.get(self.config.x) for item in flattened})

        # Получаем уникальные значения для цвета, если задано
        color_values = None
        if self.config.color:
            color_values = list({item.get(self.config.color) for item in flattened})

        for metric in self.config.metrics:
            # Определяем ось Y
            yaxis = "y2" if metric in self.config.secondary_y else "y"

            if self.config.color and color_values:
                # Создаем отдельную трассу для каждого значения цвета
                for color_val in color_values:
                    # Фильтруем данные для этой комбинации
                    filtered = [
                        item for item in flattened
                        if item.get(self.config.color) == color_val
                    ]

                    # Собираем значения метрики
                    y_values = []
                    for x_val in x_values:
                        value = sum(
                            item.get(metric, 0)
                            for item in filtered
                            if item.get(self.config.x) == x_val
                        )
                        y_values.append(value)

                    trace = go.Bar(
                        x=x_values if self.config.orientation == OrientationEnum.vertical else y_values,
                        y=y_values if self.config.orientation == OrientationEnum.vertical else x_values,
                        name=f"{color_val} - {metric}",
                        legendgroup=color_val,
                        yaxis=yaxis,
                        orientation=self.config.orientation.value,
                    )
                    traces.append(trace)
            else:
                # Без группировки по цвету - одна трасса на метрику
                y_values = [sum(item.get(metric, 0) for item in flattened
                              if item.get(self.config.x) == x_val)
                          for x_val in x_values]

                trace = go.Bar(
                    x=x_values if self.config.orientation == OrientationEnum.vertical else y_values,
                    y=y_values if self.config.orientation == OrientationEnum.vertical else x_values,
                    name=metric,
                    yaxis=yaxis,
                    orientation=self.config.orientation.value,
                )
                traces.append(trace)

        logger.info(
            "Построено %d трасс для графика '%s'",
            len(traces),
            self.__class__.__name__,
        )
        return traces

    def create_figure(self, data: ChartData) -> go.Figure:
        """Создание фигуры столбчатой диаграммы.

        Args:
            data: Данные для графика

        Returns:
            Объект фигуры Plotly
        """
        traces = self.build_traces(data)
        fig = go.Figure(data=traces)

        # Настройка баров
        fig.update_layout(
            barmode=self.config.barmode.value,
        )

        # Настройка осей
        if self.config.orientation == OrientationEnum.vertical:
            fig.update_xaxes(title_text=self.config.x)

            # Настройка основной оси Y
            fig.update_yaxes(title_text="Значение", side="left", showgrid=True)

            # Настройка дополнительной оси Y, если есть метрики для неё
            if self.config.secondary_y:
                fig.update_yaxes(
                    title_text="Значение (вторичная)",
                    side="right",
                    overlaying="y",
                    showgrid=False,
                )
        else:
            fig.update_yaxes(title_text=self.config.x)
            fig.update_xaxes(title_text="Значение", side="bottom", showgrid=True)

            if self.config.secondary_y:
                fig.update_xaxes(
                    title_text="Значение (вторичная)",
                    side="top",
                    overlaying="x",
                    showgrid=False,
                )

        fig = self.update_layout(fig)

        logger.info("Фигура столбчатой диаграммы создана")
        return fig

    def update_layout(self, fig: go.Figure) -> go.Figure:
        """Обновление макета столбчатой диаграммы.

        Args:
            fig: Объект фигуры Plotly

        Returns:
            Обновленный объект фигуры Plotly
        """
        fig = super().update_layout(fig)

        # Применяем заголовок по умолчанию, если не задан
        if not fig.layout.title.text:
            title_parts = [self.config.metrics[0]]
            if self.config.color:
                title_parts.append(f"by {self.config.color}")
            fig.update_layout(title=" ".join(title_parts))

        return fig