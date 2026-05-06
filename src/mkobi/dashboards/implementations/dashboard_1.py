"""Реализация дашборда 1.

Этот модуль содержит реализацию Dashboard1 с поддержкой:
- Столбчатой диаграммы (bar chart)
- Линейного графика (line chart)
- Фильтров по году и категории

Дашборд использует компоненты визуализации для отображения
агрегированных данных, загруженных через DataService.
"""

import logging
from typing import Any

from mkobi.dashboards.base import DashboardBase
from mkobi.dashboards.components.charts.bar import BarChart
from mkobi.dashboards.components.charts.line import LineChart
from mkobi.dashboards.components.layout import DashboardLayout
from mkobi.models.dashboard import DashboardConfig
from mkobi.models.data import ChartConfig, ChartData

logger = logging.getLogger(__name__)


class Dashboard1(DashboardBase):
    """Дашборд 1: столбчатая и линейная диаграммы.

    Реализует дашборд с двумя графиками:
    - Столбчатая диаграмма для сравнения значений по категориям
    - Линейный график для отображения трендов

    Поддерживаемые фильтры:
    - year: фильтрация по году
    - category: фильтрация по категории

    Атрибуты:
        config: Конфигурация дашборда
        _bar_chart: Компонент столбчатой диаграммы
        _line_chart: Компонент линейного графика
        _layout: Макет дашборда
    """

    def __init__(self, config: DashboardConfig, token: str | None = None) -> None:
        """Инициализация дашборда 1.

        Args:
            config: Конфигурация дашборда
            token: Опциональный JWT токен для API вызовов
        """
        super().__init__(config, token)
        self._bar_chart: BarChart
        self._line_chart: LineChart
        self._layout = DashboardLayout()
        self._initialize_charts()
        logger.info("Создан экземпляр Dashboard1")

    def _initialize_charts(self) -> None:
        """Инициализация компонентов графиков на основе конфигурации."""
        # Ищем конфигурации графиков в конфигурации дашборда
        charts_config = self.config.charts or []

        for chart_cfg in charts_config:
            graph_type = chart_cfg.get("type")
            chart_config = ChartConfig(
                x=chart_cfg.get("x", ""),
                color=chart_cfg.get("color"),
                metrics=chart_cfg.get("metrics", []),
                orientation=chart_cfg.get("orientation", "v"),
                barmode=chart_cfg.get("barmode", "group"),
                secondary_y=chart_cfg.get("secondary_y", []),
                layout=chart_cfg.get("layout", {}),
                yoy=chart_cfg.get("yoy"),
            )

            if graph_type == "bar":
                self._bar_chart = BarChart(chart_config)
                logger.debug("Инициализирован BarChart")
            elif graph_type == "line":
                self._line_chart = LineChart(chart_config)
                logger.debug("Инициализирован LineChart")

        # Если графики не заданы в конфигурации, создаем стандартные
        if not self._bar_chart:
            default_bar_config = ChartConfig(
                x="category",
                metrics=["revenue"],
                orientation="v",
                barmode="group",
                layout={"title": "Доход по категориям"},
            )
            self._bar_chart = BarChart(default_bar_config)
            logger.debug("Создан BarChart с конфигурацией по умолчанию")

        if not self._line_chart:
            default_line_config = ChartConfig(
                x="category",
                metrics=["revenue"],
                layout={"title": "Тренд дохода"},
            )
            self._line_chart = LineChart(default_line_config)
            logger.debug("Создан LineChart с конфигурацией по умолчанию")

    def get_data(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Получение данных для дашборда с применением фильтров.

        Выполняет запрос к API для получения агрегированных данных
        с учетом переданных фильтров.

        Args:
            filters: Словарь фильтров, где ключ - имя фильтра,
                     значение - значение фильтра
                     (например: {"year": 2024, "category": "electronics"})

        Returns:
            Список словарей с данными. Каждая словарь представляет
            одну запись/точку данных.

        Raises:
            ConnectionError: При ошибке соединения с API
            ValueError: При ошибке API
        """
        logger.info(
            "Получение данных для Dashboard1 с фильтрами: %s",
            filters,
        )

        try:
            # Формируем параметры запроса
            params = {"dashboard_id": str(self.config.title or "1")}
            if filters:
                params.update(filters)

            # Выполняем запрос к API для получения данных с фильтрами
            response_data = self._make_api_request(
                endpoint="/data/filter",
                method="POST",
                data={
                    "dashboard_id": str(self.config.title or "1"),
                    "filters": filters,
                },
            )

            # Преобразуем ответ API в формат списка словарей
            result = []
            for item in response_data:
                if "data" in item:
                    for data_point in item["data"]:
                        dims = data_point.get("dims", {})
                        metrics = data_point.get("metrics", {})
                        # Объединяем dims и metrics в одну запись
                        record = {**dims, **metrics}
                        result.append(record)

            logger.info(
                "Данные получены через API: %d записей",
                len(result),
            )
            return result

        except (ConnectionError, ValueError) as e:
            logger.error("Ошибка при получении данных через API: %s", e)
            # Fallback to empty list or re-raise as needed
            raise
        except Exception as e:
            logger.error("Неожиданная ошибка при получении данных: %s", e)
            raise

    def apply_filters(self, data: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Применение фильтров к уже полученным данным.

        Этот метод фильтрует данные на стороне приложения, когда
        фильтрация на уровне источника данных невозможна или неэффективна.

        Поддерживаемые фильтры:
        - year: фильтрация по году (точное совпадение)
        - category: фильтрация по категории (точное совпадение)

        Args:
            data: Список словарей с данными для фильтрации
            filters: Словарь фильтров, где ключ - имя поля,
                     значение - значение для фильтрации

        Returns:
            Отфильтрованный список словарей с данными

        Example:
            >>> data = [
            ...     {"year": 2023, "revenue": 100},
            ...     {"year": 2024, "revenue": 200},
            ... ]
            >>> dashboard.apply_filters(data, {"year": 2024})
            [{"year": 2024, "revenue": 200}]
        """
        if not filters:
            logger.debug("Нет фильтров для применения")
            return data

        filtered_data = data

        # Фильтрация по году
        if "year" in filters and filters["year"] is not None:
            year_value = filters["year"]
            filtered_data = [
                item for item in filtered_data
                if item.get("year") == year_value
            ]
            logger.debug("Применен фильтр по году: %s", year_value)

        # Фильтрация по категории
        if "category" in filters and filters["category"] is not None:
            category_value = filters["category"]
            filtered_data = [
                item for item in filtered_data
                if item.get("category") == category_value
            ]
            logger.debug("Применен фильтр по категории: %s", category_value)

        logger.info(
            "Фильтрация завершена: %d -> %d записей",
            len(data),
            len(filtered_data),
        )

        return filtered_data

    def render(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Рендеринг данных в формат для отображения.

        Преобразует сырые данные в формат, готовый для отображения
        в веб-интерфейсе. Строит графики и собирает макет дашборда.

        Args:
            data: Список словарей с данными для рендеринга

        Returns:
            Словарь с отрендеренными данными, готовыми для передачи
            во фронтенд. Структура зависит от типа дашборда.

        Example:
            >>> data = [{"category": "A", "revenue": 100}, {"category": "B", "revenue": 200}]
            >>> dashboard.render(data)
            {
                "type": "dashboard1",
                "layout": {...},
                "charts": {
                    "bar": {...},
                    "line": {...}
                }
            }
        """
        logger.info("Начало рендеринга Dashboard1")

        # Преобразуем данные в формат ChartData
        chart_data = ChartData(data=data)

        # Строим графики
        bar_figure = self._bar_chart.create_figure(chart_data)
        line_figure = self._line_chart.create_figure(chart_data)

        # Собираем макет дашборда
        self._layout.clear()
        self._layout.add_component(
            bar_figure,
            title="Доход по категориям",
            width=6,
        )
        self._layout.add_component(
            line_figure,
            title="Тренд дохода",
            width=6,
        )

        # Формируем результат рендеринга
        result = {
            "type": "dashboard1",
            "title": self.config.title or "Дашборд 1: Анализ доходов",
            "description": self.config.description or "Столбчатая и линейная диаграммы",
            "layout": self._layout.assemble(),
            "charts": {
                "bar": bar_figure.to_plotly_json(),
                "line": line_figure.to_plotly_json(),
            },
            "filters": {
                "available": ["year", "category"],
                "current": {},
            },
        }

        logger.info("Рендеринг Dashboard1 завершен")

        return result
