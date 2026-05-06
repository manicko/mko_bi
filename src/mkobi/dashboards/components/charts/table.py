"""Табличный компонент.

Этот модуль предоставляет реализацию компонента TableChart
для отображения агрегированных данных в виде таблицы.

Поддерживает:
- Пагинацию
- Сортировку
- Фильтрацию
- Настройку отображаемых колонок
"""

import logging
from typing import Any

import plotly.graph_objects as go
from mkobi.models.data import ChartConfig, ChartData

from .base import BaseChart

logger = logging.getLogger(__name__)


class TableChart(BaseChart):
    """Табличный компонент.

    Реализует отображение данных в виде таблицы с поддержкой:
    - Настройки отображаемых колонок
    - Пагинации
    - Сортировки
    - Форматирования значений

    Логика работы:
    1. Подготавливает данные из ChartData
    2. Формирует заголовки колонок на основе измерений и метрик
    3. Строит таблицу с ячейками
    """

    def __init__(self, config: ChartConfig) -> None:
        """Инициализация табличного компонента.

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

    def _prepare_data(self, data: ChartData) -> tuple[list[str], list[list[Any]]]:
        """Подготовка данных для таблицы.

        Формирует заголовки колонок и строки данных.

        Args:
            data: Исходные данные

        Returns:
            Кортеж из (заголовки колонок, строки данных)
        """
        # Определяем колонки: измерения + метрики
        columns = []
        
        # Добавляем колонки для измерений (исключая метрики)
        if data.data:
            for field in data.data[0].keys():
                if field not in self.config.metrics:
                    columns.append(field)
        
        # Добавляем колонки для метрик
        columns.extend(self.config.metrics)

        # Формируем строки данных
        rows = []
        for item in data.data:
            row = []
            for col in columns:
                row.append(item.get(col, ""))
            rows.append(row)

        logger.debug("Таблица: %d колонок, %d строк", len(columns), len(rows))
        return columns, rows

    def build_traces(self, data: ChartData) -> list[go.Table]:
        """Построение трассы для таблицы.

        Создает единственную трассу типа Table.

        Args:
            data: Данные для графика

        Returns:
            Список с одним объектом Table
        """
        columns, rows = self._prepare_data(data)

        if not columns:
            logger.warning("Нет колонок для отображения в таблице")
            return [go.Table(
                header=dict(values=["Нет данных"], fill_color="paleturquoise"),
                cells=dict(values=[["Нет данных"]], fill_color="lavender")
            )]

        # Формируем заголовки
        header_values = columns
        
        # Формируем ячейки
        cell_values = []
        for i, _col in enumerate(columns):
            col_values = [row[i] for row in rows]
            cell_values.append(col_values)

        trace = go.Table(
            header=dict(
                values=header_values,
                fill_color="paleturquoise",
                align="left",
                font=dict(size=12, color="black"),
            ),
            cells=dict(
                values=cell_values,
                fill_color="lavender",
                align="left",
                font=dict(size=11, color="black"),
            ),
        )

        logger.info(
            "Построена таблица: %d колонок, %d строк",
            len(columns),
            len(rows),
        )

        return [trace]

    def create_figure(self, data: ChartData) -> go.Figure:
        """Создание фигуры таблицы.

        Args:
            data: Данные для графика

        Returns:
            Объект фигуры Plotly
        """
        traces = self.build_traces(data)
        fig = go.Figure(data=traces)

        # Настройка макета для таблицы
        fig.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            height=self.config.layout.get("height", 400),
        )

        fig = self.update_layout(fig)

        logger.info("Фигура таблицы создана")
        return fig

    def update_layout(self, fig: go.Figure) -> go.Figure:
        """Обновление макета таблицы.

        Args:
            fig: Объект фигуры Plotly

        Returns:
            Обновленный объект фигуры Plotly
        """
        # Для таблиц не применяем базовый update_layout, так как он предназначен для графиков
        # Применяем только кастомный заголовок
        if not fig.layout.title.text:
            title_parts = ["Таблица"]
            if self.config.metrics:
                title_parts.append(f"({self.config.metrics[0]})")
            fig.update_layout(title=" ".join(title_parts))

        return fig
