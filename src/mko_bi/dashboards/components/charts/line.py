"""Линейный график.

Этот модуль предоставляет реализацию компонента LineChart
для визуализации агрегированных данных в виде линейного графика.

Поддерживает:
- Множественные линии
- Сравнение год-к-году (YoY)
- Группировку по цвету
"""

import logging
from typing import Any

import plotly.graph_objects as go
from mko_bi.models.data import ChartConfig, ChartData
from mko_bi.models.user_roles import YoyModeEnum

from .base import BaseChart

logger = logging.getLogger(__name__)


class LineChart(BaseChart):
    """Линейный график.

    Реализует линейный график с поддержкой:
    - Множественных линий
    - Сравнения год-к-году (YoY)
    - Группировки по цвету

    YoY (Year-over-Year) сравнение:
    - Текущий год отображается сплошной линией
    - Предыдущий год отображается пунктирной линией
    - Поддерживает абсолютные и процентные значения
    """

    def __init__(self, config: ChartConfig) -> None:
        """Инициализация линейного графика.

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

        # Проверка конфигурации YoY
        if self.config.yoy:
            yoy_config = self.config.yoy
            required_fields = ["enabled", "metric", "mode", "year_field"]
            for field in required_fields:
                if field not in yoy_config:
                    raise ValueError(
                        f"В конфигурации YoY отсутствует обязательное поле: {field}"
                    )

            if yoy_config["metric"] not in self.config.metrics:
                raise ValueError(
                    f"Метрика YoY '{yoy_config['metric']}' должна быть в списке metrics"
                )

            if yoy_config["mode"] not in [mode.value for mode in YoyModeEnum]:
                raise ValueError(
                    f"Некорректный режим YoY: {yoy_config['mode']}"
                )

    def _prepare_data(self, data: ChartData) -> dict[str, Any]:
        """Подготовка данных для построения линий.

        Группирует данные по оси X и (опционально) по цвету.
        Сохраняет все поля из исходных данных для использования в YoY.

        Args:
            data: Исходные данные

        Returns:
            Словарь с подготовленными данными
        """
        prepared = {}

        for item in data.data:
            x_val = item.get(self.config.x)
            if x_val is None:
                continue

            key = str(x_val)
            if key not in prepared:
                prepared[key] = {
                    self.config.x: x_val,
                    "metrics": {},
                    "_all_items": [],  # Сохраняем все исходные записи
                }

                # Добавляем значение цвета, если задано
                if self.config.color:
                    prepared[key][self.config.color] = item.get(self.config.color)

                # Копируем все поля для использования в YoY
                for field_name, field_value in item.items():
                    if field_name not in [self.config.x, self.config.color] + self.config.metrics:
                        if field_name not in prepared[key]:
                            prepared[key][field_name] = []
                        prepared[key][field_name].append(field_value)

            # Сохраняем исходную запись
            prepared[key]["_all_items"].append(item)

            # Сохраняем значения метрик
            for metric in self.config.metrics:
                if metric not in prepared[key]["metrics"]:
                    prepared[key]["metrics"][metric] = []
                prepared[key]["metrics"][metric].append(item.get(metric))

        # Вычисляем средние значения для дублирующихся X
        for key in prepared:
            for metric in self.config.metrics:
                values = prepared[key]["metrics"][metric]
                if values:
                    prepared[key]["metrics"][metric] = sum(values) / len(values)
                else:
                    prepared[key]["metrics"][metric] = 0

        logger.debug("Данные подготовлены: %d уникальных значений X", len(prepared))
        return prepared

    def _build_yoy_data(self, prepared_data: dict[str, Any]) -> dict[str, Any]:
        """Построение данных для сравнения год-к-году.

        Args:
            prepared_data: Подготовленные данные

        Returns:
            Данные с разделением на текущий и предыдущий год
        """
        if not self.config.yoy or not self.config.yoy.get("enabled"):
            return prepared_data

        year_field = self.config.yoy["year_field"]
        metric = self.config.yoy["metric"]

        # Группируем по годам
        years_data = {}
        for key, item in prepared_data.items():
            year = item.get(year_field)
            if year is None:
                continue

            if year not in years_data:
                years_data[year] = {}

            # Копируем данные без поля года для группировки
            group_key = key.replace(str(year), "").strip("|-")
            years_data[year][group_key] = item

        # Находим текущий и предыдущий год
        if years_data:
            sorted_years = sorted(years_data.keys(), reverse=True)
            current_year = sorted_years[0]
            previous_year = sorted_years[1] if len(sorted_years) > 1 else None
        else:
            return prepared_data

        # Собираем данные для текущего и предыдущего года
        result = {
            "current": {},
            "previous": {},
            "years": {"current": current_year, "previous": previous_year},
        }

        # Текущий год
        for group_key, item in years_data[current_year].items():
            result["current"][group_key] = item

        # Предыдущий год (если есть)
        if previous_year and previous_year in years_data:
            for group_key, item in years_data[previous_year].items():
                result["previous"][group_key] = item

        logger.info(
            "Данные YoY подготовлены: текущий год=%d, предыдущий год=%s",
            current_year,
            previous_year,
        )
        return result

    def build_traces(self, data: ChartData) -> list[go.Scatter]:
        """Построение трасс для линейного графика.

        Создает отдельную трассу для каждой метрики и (опционально)
        для сравнения год-к-году.

        Args:
            data: Данные для графика

        Returns:
            Список объектов Scatter (трасс)
        """
        prepared = self._prepare_data(data)

        # Проверяем, нужно ли строить YoY
        if self.config.yoy and self.config.yoy.get("enabled"):
            return self._build_yoy_traces(prepared)

        # Обычный режим - без YoY
        traces = []
        x_values = sorted(
            prepared.keys(),
            key=lambda k: prepared[k][self.config.x]
            if isinstance(prepared[k][self.config.x], (int, float))
            else str(prepared[k][self.config.x]),
        )

        if self.config.color:
            # Группировка по цвету
            color_values = list(
                {prepared[k].get(self.config.color) for k in x_values}
            )

            for color_val in color_values:
                x_line = []
                y_lines = {metric: [] for metric in self.config.metrics}

                for x_key in x_values:
                    item = prepared[x_key]
                    if item.get(self.config.color) == color_val:
                        x_line.append(item[self.config.x])
                        for metric in self.config.metrics:
                            y_lines[metric].append(item["metrics"][metric])

                for metric in self.config.metrics:
                    trace = go.Scatter(
                        x=x_line,
                        y=y_lines[metric],
                        mode="lines+markers",
                        name=f"{color_val} - {metric}",
                        legendgroup=color_val,
                    )
                    traces.append(trace)
        else:
            # Без группировки по цвету
            for metric in self.config.metrics:
                x_line = [prepared[k][self.config.x] for k in x_values]
                y_line = [prepared[k]["metrics"][metric] for k in x_values]

                trace = go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines+markers",
                    name=metric,
                )
                traces.append(trace)

        logger.info(
            "Построено %d трасс для линейного графика",
            len(traces),
        )
        return traces

    def _build_yoy_traces(self, prepared_data: dict[str, Any]) -> list[go.Scatter]:
        """Построение трасс для сравнения год-к-году.

        Args:
            prepared_data: Подготовленные данные

        Returns:
            Список объектов Scatter (трасс)
        """
        traces = []
        yoy_config = self.config.yoy
        metric = yoy_config["metric"]
        mode = yoy_config["mode"]
        year_field = yoy_config["year_field"]

        # Собираем все уникальные года из данных
        all_years = set()
        for key, item in prepared_data.items():
            if year_field in item and isinstance(item[year_field], list):
                all_years.update(item[year_field])

        if not all_years:
            logger.warning("Не найдены данные для поля года: %s", year_field)
            return traces

        sorted_years = sorted(all_years, reverse=True)
        current_year = sorted_years[0]
        previous_year = sorted_years[1] if len(sorted_years) > 1 else None

        # Текущий год - сплошная линия
        # Собираем данные для текущего года
        current_x = []
        current_y = []

        for key, item in prepared_data.items():
            if year_field in item and isinstance(item[year_field], list):
                # Проверяем, есть ли текущий год в данных для этого X
                if current_year in item[year_field]:
                    current_x.append(item[self.config.x])
                    current_y.append(item["metrics"][metric])

        if current_x:
            # Сортируем по X
            sorted_pairs = sorted(zip(current_x, current_y), key=lambda p: p[0])
            current_x, current_y = zip(*sorted_pairs) if sorted_pairs else ([], [])

            trace = go.Scatter(
                x=list(current_x),
                y=list(current_y),
                mode="lines+markers",
                name=f"{metric} ({current_year})",
                line=dict(
                    color="#1f77b4",
                    width=3,
                    dash="solid",
                ),
            )
            traces.append(trace)

        # Предыдущий год - пунктирная линия
        if previous_year:
            previous_x = []
            previous_y = []

            for key, item in prepared_data.items():
                if year_field in item and isinstance(item[year_field], list):
                    if previous_year in item[year_field]:
                        previous_x.append(item[self.config.x])
                        previous_y.append(item["metrics"][metric])

            if mode == YoyModeEnum.percent and current_x:
                # Процентное изменение
                # Создаем словарь для быстрого доступа к текущим значениям
                current_dict = dict(zip(current_x, current_y))

                pct_x = []
                pct_y = []

                for px, py in zip(previous_x, previous_y):
                    if px in current_dict and py != 0:
                        pct_change = ((current_dict[px] - py) / py) * 100
                        pct_x.append(px)
                        pct_y.append(pct_change)

                if pct_x:
                    sorted_pairs = sorted(zip(pct_x, pct_y), key=lambda p: p[0])
                    pct_x, pct_y = zip(*sorted_pairs) if sorted_pairs else ([], [])

                    trace = go.Scatter(
                        x=list(pct_x),
                        y=list(pct_y),
                        mode="lines+markers",
                        name=f"Изменение YoY (%)",
                        line=dict(
                            color="#ff7f0e",
                            width=2,
                            dash="dash",
                        ),
                        yaxis="y2",
                    )
                    traces.append(trace)
            else:
                # Абсолютное значение
                if previous_x:
                    sorted_pairs = sorted(zip(previous_x, previous_y), key=lambda p: p[0])
                    previous_x, previous_y = zip(*sorted_pairs) if sorted_pairs else ([], [])

                    trace = go.Scatter(
                        x=list(previous_x),
                        y=list(previous_y),
                        mode="lines+markers",
                        name=f"{metric} ({previous_year})",
                        line=dict(
                            color="#ff7f0e",
                            width=2,
                            dash="dash",
                        ),
                    )
                    traces.append(trace)

        logger.info(
            "Построено %d трасс для YoY сравнения",
            len(traces),
        )
        return traces

    def create_figure(self, data: ChartData) -> go.Figure:
        """Создание фигуры линейного графика.

        Args:
            data: Данные для графика

        Returns:
            Объект фигуры Plotly
        """
        traces = self.build_traces(data)
        fig = go.Figure(data=traces)

        # Настройка осей
        fig.update_xaxes(title_text=self.config.x)
        fig.update_yaxes(title_text="Значение", side="left", showgrid=True)

        # Если есть YoY в процентах, добавляем вторую ось Y
        if self.config.yoy and self.config.yoy.get("enabled"):
            if self.config.yoy.get("mode") == YoyModeEnum.percent.value:
                fig.update_yaxes(
                    title_text="Изменение (%)",
                    side="right",
                    overlaying="y",
                    showgrid=False,
                )

        fig = self.update_layout(fig)

        logger.info("Фигура линейного графика создана")
        return fig

    def update_layout(self, fig: go.Figure) -> go.Figure:
        """Обновление макета линейного графика.

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
            if self.config.yoy and self.config.yoy.get("enabled"):
                title_parts.append("(YoY)")
            fig.update_layout(title=" ".join(title_parts))

        return fig