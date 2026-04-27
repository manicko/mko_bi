"""Тесты для компонентов графиков дашборда.

Тестирует:
- Базовый класс графика (BaseChart)
- Столбчатую диаграмму (BarChart)
- Линейный график (LineChart)
- Панель фильтров (FilterPanel)
- Макет дашборда (DashboardLayout)
"""

import pytest
from mko_bi.dashboards.components.charts.base import BaseChart
from mko_bi.dashboards.components.charts.bar import BarChart
from mko_bi.dashboards.components.charts.line import LineChart
from mko_bi.dashboards.components.filters import FilterPanel, FilterType
from mko_bi.dashboards.components.layout import DashboardLayout
from mko_bi.models.data import ChartConfig, ChartData, FilterState
from mko_bi.models.user_roles import (
    BarmodeEnum,
    OrientationEnum,
    YoyModeEnum,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_chart_data():
    """Фикстура: пример данных для графика."""
    return ChartData(
        data=[
            {"category": "A", "revenue": 1000, "sales": 500, "year": 2023},
            {"category": "B", "revenue": 2000, "sales": 800, "year": 2023},
            {"category": "C", "revenue": 1500, "sales": 600, "year": 2023},
            {"category": "A", "revenue": 1200, "sales": 550, "year": 2024},
            {"category": "B", "revenue": 2200, "sales": 900, "year": 2024},
            {"category": "C", "revenue": 1700, "sales": 650, "year": 2024},
        ]
    )


@pytest.fixture
def basic_chart_config():
    """Фикстура: базовая конфигурация графика."""
    return ChartConfig(
        x="category",
        metrics=["revenue"],
        orientation=OrientationEnum.vertical,
        barmode=BarmodeEnum.group,
    )


@pytest.fixture
def bar_chart_config():
    """Фикстура: конфигурация для столбчатой диаграммы."""
    return ChartConfig(
        x="category",
        color="year",
        metrics=["revenue", "sales"],
        orientation=OrientationEnum.vertical,
        barmode=BarmodeEnum.group,
        layout={"title": "Test Bar Chart"},
    )


@pytest.fixture
def line_chart_config():
    """Фикстура: конфигурация для линейного графика."""
    return ChartConfig(
        x="category",
        color="year",
        metrics=["revenue"],
        layout={"title": "Test Line Chart"},
    )


@pytest.fixture
def line_chart_yoy_config():
    """Фикстура: конфигурация для линейного графика с YoY."""
    return ChartConfig(
        x="category",
        metrics=["revenue"],
        yoy={
            "enabled": True,
            "metric": "revenue",
            "mode": YoyModeEnum.absolute,
            "year_field": "year",
        },
        layout={"title": "Test Line Chart YoY"},
    )


@pytest.fixture
def line_chart_yoy_percent_config():
    """Фикстура: конфигурация для линейного графика с YoY в процентах."""
    return ChartConfig(
        x="category",
        metrics=["revenue"],
        yoy={
            "enabled": True,
            "metric": "revenue",
            "mode": YoyModeEnum.percent,
            "year_field": "year",
        },
        layout={"title": "Test Line Chart YoY %"},
    )


# ============================================================================
# BaseChart Tests
# ============================================================================

class TestBaseChart:
    """Тесты для базового класса графика BaseChart."""

    def test_is_abstract_class(self):
        """Проверка, что BaseChart является абстрактным классом."""
        assert issubclass(BaseChart, object)

    def test_has_abstract_methods(self):
        """Проверка наличия абстрактных методов."""
        abstract_methods = BaseChart.__abstractmethods__
        assert "build_traces" in abstract_methods
        assert "create_figure" in abstract_methods

    def test_init_stores_config(self, basic_chart_config):
        """Проверка сохранения конфигурации при инициализации."""
        chart = BarChart(basic_chart_config)
        assert chart.config == basic_chart_config
        assert chart.config.x == "category"
        assert chart.config.metrics == ["revenue"]


# ============================================================================
# BarChart Tests
# ============================================================================

class TestBarChart:
    """Тесты для столбчатой диаграммы BarChart."""

    def test_init(self, bar_chart_config):
        """Тест инициализации BarChart."""
        chart = BarChart(bar_chart_config)
        assert chart.config == bar_chart_config
        assert chart.config.x == "category"
        assert chart.config.color == "year"

    def test_init_invalid_config_empty_metrics(self):
        """Тест ошибки при пустом списке метрик."""
        config = ChartConfig(
            x="category",
            metrics=[],
        )
        with pytest.raises(ValueError, match="Список метрик не может быть пустым"):
            BarChart(config)

    def test_init_invalid_config_no_x(self):
        """Тест ошибки при отсутствии поля x."""
        config = ChartConfig(
            x="",
            metrics=["revenue"],
        )
        with pytest.raises(ValueError, match="Поле 'x' должно быть задано"):
            BarChart(config)

    def test_flatten_data(self, bar_chart_config, sample_chart_data):
        """Тест преобразования данных в плоский формат."""
        chart = BarChart(bar_chart_config)
        flattened = chart._flatten_data(sample_chart_data)

        assert len(flattened) == 6
        for item in flattened:
            assert "category" in item
            assert "year" in item
            assert "revenue" in item
            assert "sales" in item

    def test_build_traces_without_color(self, basic_chart_config, sample_chart_data):
        """Тест построения трасс без группировки по цвету."""
        chart = BarChart(basic_chart_config)
        traces = chart.build_traces(sample_chart_data)

        assert len(traces) == 1

    def test_build_traces_with_color(self, bar_chart_config, sample_chart_data):
        """Тест построения трасс с группировкой по цвету."""
        chart = BarChart(bar_chart_config)
        traces = chart.build_traces(sample_chart_data)

        assert len(traces) == 4

    def test_build_traces_with_secondary_y(self):
        """Тест построения трасс с дополнительной осью Y."""
        config = ChartConfig(
            x="category",
            metrics=["revenue", "sales"],
            secondary_y=["sales"],
        )
        chart = BarChart(config)
        data = ChartData(
            data=[
                {"category": "A", "revenue": 1000, "sales": 500},
                {"category": "B", "revenue": 2000, "sales": 800},
            ]
        )
        traces = chart.build_traces(data)

        assert len(traces) == 2

    def test_create_figure(self, bar_chart_config, sample_chart_data):
        """Тест создания фигуры."""
        chart = BarChart(bar_chart_config)
        fig = chart.create_figure(sample_chart_data)

        assert fig is not None
        assert len(fig.data) == 4
        assert fig.layout.barmode == "group"

    def test_create_figure_horizontal(self):
        """Тест создания горизонтальной диаграммы."""
        config = ChartConfig(
            x="category",
            metrics=["revenue"],
            orientation=OrientationEnum.horizontal,
        )
        chart = BarChart(config)
        data = ChartData(
            data=[
                {"category": "A", "revenue": 1000},
                {"category": "B", "revenue": 2000},
            ]
        )
        fig = chart.create_figure(data)

        assert fig is not None
        assert fig.data[0].orientation == "h"

    def test_create_figure_stacked(self):
        """Тест создания диаграммы с наложением."""
        config = ChartConfig(
            x="category",
            color="year",
            metrics=["revenue"],
            barmode=BarmodeEnum.stack,
        )
        chart = BarChart(config)
        data = ChartData(
            data=[
                {"category": "A", "revenue": 1000, "year": 2023},
                {"category": "B", "revenue": 2000, "year": 2023},
            ]
        )
        fig = chart.create_figure(data)

        assert fig.layout.barmode == "stack"

    def test_update_layout(self, bar_chart_config, sample_chart_data):
        """Тест обновления макета."""
        chart = BarChart(bar_chart_config)
        fig = chart.create_figure(sample_chart_data)
        updated_fig = chart.update_layout(fig)

        assert updated_fig is not None
        assert updated_fig.layout.title.text == "Test Bar Chart"


# ============================================================================
# LineChart Tests
# ============================================================================

class TestLineChart:
    """Тесты для линейного графика LineChart."""

    def test_init(self, line_chart_config):
        """Тест инициализации LineChart."""
        chart = LineChart(line_chart_config)
        assert chart.config == line_chart_config

    def test_init_invalid_config_empty_metrics(self):
        """Тест ошибки при пустом списке метрик."""
        config = ChartConfig(
            x="category",
            metrics=[],
        )
        with pytest.raises(ValueError, match="Список метрик не может быть пустым"):
            LineChart(config)

    def test_init_invalid_yoy_config(self):
        """Тест ошибки при некорректной конфигурации YoY."""
        config = ChartConfig(
            x="category",
            metrics=["revenue"],
            yoy={
                "enabled": True,
                "metric": "revenue",
                # Отсутствует mode
                "year_field": "year",
            },
        )
        with pytest.raises(ValueError, match="mode"):
            LineChart(config)

    def test_init_invalid_yoy_metric(self):
        """Тест ошибки при метрике YoY, отсутствующей в metrics."""
        config = ChartConfig(
            x="category",
            metrics=["sales"],
            yoy={
                "enabled": True,
                "metric": "revenue",  # Нет в metrics
                "mode": YoyModeEnum.absolute,
                "year_field": "year",
            },
        )
        with pytest.raises(ValueError, match="должна быть в списке metrics"):
            LineChart(config)

    def test_prepare_data(self, line_chart_config, sample_chart_data):
        """Тест подготовки данных."""
        chart = LineChart(line_chart_config)
        prepared = chart._prepare_data(sample_chart_data)

        assert len(prepared) == 3
        for key, item in prepared.items():
            assert "category" in item
            assert "metrics" in item
            assert "revenue" in item["metrics"]

    def test_build_traces_without_color(self, line_chart_config, sample_chart_data):
        """Тест построения трасс без группировки по цвету."""
        config = ChartConfig(
            x="category",
            metrics=["revenue"],
        )
        chart = LineChart(config)
        data = ChartData(
            data=[
                {"category": "A", "revenue": 1000},
                {"category": "B", "revenue": 2000},
            ]
        )
        traces = chart.build_traces(data)

        assert len(traces) == 1

    def test_build_traces_with_color(self, line_chart_config, sample_chart_data):
        """Тест построения трасс с группировкой по цвету."""
        chart = LineChart(line_chart_config)
        traces = chart.build_traces(sample_chart_data)

        assert len(traces) >= 1

    def test_build_yoy_traces_absolute(self, line_chart_yoy_config):
        """Тест построения трасс YoY (абсолютные значения)."""
        chart = LineChart(line_chart_yoy_config)
        data = ChartData(
            data=[
                {"category": "A", "revenue": 1000, "year": 2023},
                {"category": "A", "revenue": 1200, "year": 2024},
                {"category": "B", "revenue": 2000, "year": 2023},
                {"category": "B", "revenue": 2200, "year": 2024},
            ]
        )
        traces = chart.build_traces(data)

        assert len(traces) >= 1

    def test_build_yoy_traces_percent(self, line_chart_yoy_percent_config):
        """Тест построения трасс YoY (процентное изменение)."""
        chart = LineChart(line_chart_yoy_percent_config)
        data = ChartData(
            data=[
                {"category": "A", "revenue": 1000, "year": 2023},
                {"category": "A", "revenue": 1200, "year": 2024},
                {"category": "B", "revenue": 2000, "year": 2023},
                {"category": "B", "revenue": 2200, "year": 2024},
            ]
        )
        traces = chart.build_traces(data)

        assert len(traces) >= 1

    def test_create_figure(self, line_chart_config, sample_chart_data):
        """Тест создания фигуры."""
        chart = LineChart(line_chart_config)
        fig = chart.create_figure(sample_chart_data)

        assert fig is not None
        assert len(fig.data) >= 1

    def test_create_figure_yoy(self, line_chart_yoy_config, sample_chart_data):
        """Тест создания фигуры с YoY."""
        chart = LineChart(line_chart_yoy_config)
        fig = chart.create_figure(sample_chart_data)

        assert fig is not None

    def test_update_layout(self, line_chart_config, sample_chart_data):
        """Тест обновления макета."""
        chart = LineChart(line_chart_config)
        fig = chart.create_figure(sample_chart_data)
        updated_fig = chart.update_layout(fig)

        assert updated_fig is not None
        assert updated_fig.layout.title.text == "Test Line Chart"


# ============================================================================
# FilterPanel Tests
# ============================================================================

class TestFilterPanel:
    """Тесты для панели фильтров FilterPanel."""

    def test_init(self):
        """Тест инициализации FilterPanel."""
        panel = FilterPanel()
        assert panel.filters == []
        assert panel.state == FilterState()

    def test_init_with_filters(self):
        """Тест инициализации с фильтрами."""
        filters = [
            {"field": "year", "type": FilterType.SELECT, "label": "Год"},
        ]
        panel = FilterPanel(filters)
        assert len(panel.filters) == 1

    def test_add_filter(self):
        """Тест добавления фильтра."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT, label="Год")
        assert len(panel.filters) == 1
        assert panel.filters[0]["field"] == "year"

    def test_add_filter_invalid_type(self):
        """Тест ошибки при добавлении фильтра с некорректным типом."""
        panel = FilterPanel()
        with pytest.raises(ValueError, match="Некорректный тип фильтра"):
            panel.add_filter("year", "invalid_type")

    def test_remove_filter(self):
        """Тест удаления фильтра."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        assert len(panel.filters) == 1

        removed = panel.remove_filter("year")
        assert removed is True
        assert len(panel.filters) == 0

    def test_remove_nonexistent_filter(self):
        """Тест удаления несуществующего фильтра."""
        panel = FilterPanel()
        removed = panel.remove_filter("nonexistent")
        assert removed is False

    def test_update_filter_value(self):
        """Тест обновления значения фильтра."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        panel.update_filter_value("year", 2023)
        assert panel.state.filters["year"] == 2023

    def test_update_filter_value_nonexistent(self):
        """Тест ошибки при обновлении несуществующего фильтра."""
        panel = FilterPanel()
        with pytest.raises(KeyError, match="не найден"):
            panel.update_filter_value("nonexistent", 2023)

    def test_get_filter_values(self):
        """Тест получения значений фильтров."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        panel.update_filter_value("year", 2023)

        state = panel.get_filter_values()
        assert state.filters["year"] == 2023

    def test_get_filter_values_with_inputs(self):
        """Тест получения значений фильтров с входными данными."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)

        state = panel.get_filter_values({"year": 2024})
        assert state.filters["year"] == 2024

    def test_apply_filters_select(self):
        """Тест применения фильтра типа select."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        panel.update_filter_value("year", 2023)

        data = [
            {"category": "A", "year": 2023, "revenue": 1000},
            {"category": "B", "year": 2024, "revenue": 2000},
        ]
        filtered = panel.apply_filters(data)

        assert len(filtered) == 1
        assert filtered[0]["year"] == 2023

    def test_apply_filters_multiselect(self):
        """Тест применения фильтра типа multiselect."""
        panel = FilterPanel()
        panel.add_filter("category", FilterType.MULTISELECT)
        panel.update_filter_value("category", ["A", "B"])

        data = [
            {"category": "A", "revenue": 1000},
            {"category": "B", "revenue": 2000},
            {"category": "C", "revenue": 3000},
        ]
        filtered = panel.apply_filters(data)

        assert len(filtered) == 2

    def test_apply_filters_range(self):
        """Тест применения фильтра типа range."""
        panel = FilterPanel()
        panel.add_filter("revenue", FilterType.RANGE)
        panel.update_filter_value("revenue", [1000, 2000])

        data = [
            {"category": "A", "revenue": 500},
            {"category": "B", "revenue": 1500},
            {"category": "C", "revenue": 2500},
        ]
        filtered = panel.apply_filters(data)

        assert len(filtered) == 1
        assert filtered[0]["category"] == "B"

    def test_apply_filters_no_filters(self):
        """Тест применения фильтров при отсутствии активных фильтров."""
        panel = FilterPanel()
        data = [{"category": "A", "revenue": 1000}]
        filtered = panel.apply_filters(data)

        assert len(filtered) == 1

    def test_reset(self):
        """Тест сброса фильтров."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        panel.update_filter_value("year", 2023)
        panel.reset()

        assert panel.state.filters == {}

    def test_active_filters(self):
        """Тест получения активных фильтров."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        panel.add_filter("category", FilterType.SELECT)
        panel.update_filter_value("year", 2023)

        active = panel.active_filters
        assert "year" in active
        assert "category" not in active

    def test_repr(self):
        """Тест строкового представления."""
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        panel.update_filter_value("year", 2023)

        repr_str = repr(panel)
        assert "FilterPanel" in repr_str


# ============================================================================
# DashboardLayout Tests
# ============================================================================

class TestDashboardLayout:
    """Тесты для макета дашборда DashboardLayout."""

    def test_init(self):
        """Тест инициализации DashboardLayout."""
        layout = DashboardLayout()
        assert layout.components == []
        assert layout.filter_panel is None

    def test_add_filter_panel(self):
        """Тест добавления панели фильтров."""
        layout = DashboardLayout()
        panel = FilterPanel()
        layout.add_filter_panel(panel)
        assert layout.filter_panel == panel

    def test_add_component(self):
        """Тест добавления компонента."""
        layout = DashboardLayout()
        fig = "test_figure"
        layout.add_component(fig, title="Test Chart", width=6)
        assert len(layout.components) == 1
        assert layout.components[0]["title"] == "Test Chart"
        assert layout.components[0]["width"] == 6

    def test_add_component_invalid_width(self):
        """Тест ошибки при добавлении компонента с некорректной шириной."""
        layout = DashboardLayout()
        with pytest.raises(ValueError, match="Ширина должна быть в диапазоне 1-12"):
            layout.add_component("test", width=13)

    def test_assemble_with_filters(self):
        """Тест сборки макета с фильтрами."""
        layout = DashboardLayout()
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        layout.add_filter_panel(panel)

        rows = layout.assemble()
        assert len(rows) == 1

    def test_assemble_with_components(self):
        """Тест сборки макета с компонентами."""
        layout = DashboardLayout()
        layout.add_component("chart1", title="Chart 1", width=6)
        layout.add_component("chart2", title="Chart 2", width=6)

        rows = layout.assemble()
        assert len(rows) == 1

    def test_assemble_complete(self):
        """Тест полной сборки макета."""
        layout = DashboardLayout()
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        layout.add_filter_panel(panel)

        layout.add_component("chart1", title="Chart 1", width=6)
        layout.add_component("chart2", title="Chart 2", width=6)

        rows = layout.assemble()
        assert len(rows) == 2

    def test_assemble_with_filter_state(self):
        """Тест сборки макета с состоянием фильтров."""
        layout = DashboardLayout()
        panel = FilterPanel()
        panel.add_filter("year", FilterType.SELECT)
        layout.add_filter_panel(panel)

        state = FilterState(filters={"year": [2023]})
        rows = layout.assemble(state)
        assert len(rows) == 1

    def test_clear(self):
        """Тест очистки макета."""
        layout = DashboardLayout()
        layout.add_filter_panel(FilterPanel())
        layout.add_component("chart", title="Chart", width=6)
        layout.clear()

        assert layout.components == []
        assert layout.filter_panel is None

    def test_component_count(self):
        """Тест свойства component_count."""
        layout = DashboardLayout()
        assert layout.component_count == 0

        layout.add_component("chart1", width=6)
        assert layout.component_count == 1

        layout.add_component("chart2", width=6)
        assert layout.component_count == 2

    def test_repr(self):
        """Тест строкового представления."""
        layout = DashboardLayout()
        layout.add_filter_panel(FilterPanel())
        layout.add_component("chart", width=6)

        repr_str = repr(layout)
        assert "DashboardLayout" in repr_str
        assert "has_filters=True" in repr_str


# ============================================================================
# Integration Tests
# ============================================================================

class TestChartIntegration:
    """Интеграционные тесты для компонентов графиков."""

    def test_bar_chart_workflow(self, bar_chart_config, sample_chart_data):
        """Тест полного цикла работы со столбчатой диаграммой."""
        chart = BarChart(bar_chart_config)
        traces = chart.build_traces(sample_chart_data)
        assert len(traces) > 0
        fig = chart.create_figure(sample_chart_data)
        assert fig is not None
        assert len(fig.data) == len(traces)
        updated_fig = chart.update_layout(fig)
        assert updated_fig is not None

    def test_line_chart_workflow(self, line_chart_config, sample_chart_data):
        """Тест полного цикла работы с линейным графиком."""
        chart = LineChart(line_chart_config)
        traces = chart.build_traces(sample_chart_data)
        assert len(traces) > 0
        fig = chart.create_figure(sample_chart_data)
        assert fig is not None
        updated_fig = chart.update_layout(fig)
        assert updated_fig is not None

    def test_dashboard_with_filters_and_charts(self):
        """Тест создания дашборда с фильтрами и графиками."""
        filter_panel = FilterPanel()
        filter_panel.add_filter("year", FilterType.SELECT)
        filter_panel.add_filter("category", FilterType.MULTISELECT)

        bar_config = ChartConfig(
            x="category",
            metrics=["revenue"],
        )
        bar_chart = BarChart(bar_config)

        line_config = ChartConfig(
            x="category",
            metrics=["sales"],
        )
        line_chart = LineChart(line_config)

        layout = DashboardLayout()
        layout.add_filter_panel(filter_panel)
        layout.add_component(bar_chart, title="Revenue by Category", width=6)
        layout.add_component(line_chart, title="Sales by Category", width=6)

        rows = layout.assemble()
        assert len(rows) == 2

        data = [
            {"category": "A", "year": 2023, "revenue": 1000, "sales": 500},
            {"category": "B", "year": 2024, "revenue": 2000, "sales": 800},
        ]
        state = filter_panel.get_filter_values({"year": 2023})
        filtered_data = filter_panel.apply_filters(data, state)

        assert len(filtered_data) <= len(data)