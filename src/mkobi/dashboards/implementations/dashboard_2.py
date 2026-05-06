"""Реализация дашборда 2.

Этот модуль содержит реализацию Dashboard2 с поддержкой:
- Круговой диаграммы (pie chart)
- Таблицы (table)
- Фильтров по бренду

Дашборд использует компоненты визуализации для отображения
агрегированных данных, загруженных через DataService.
"""

import logging
from typing import Any

from mkobi.dashboards.base import DashboardBase
from mkobi.dashboards.components.charts.pie import PieChart
from mkobi.dashboards.components.charts.table import TableChart
from mkobi.dashboards.components.layout import DashboardLayout
from mkobi.models.dashboard import DashboardConfig
from mkobi.models.data import ChartConfig, ChartData

logger = logging.getLogger(__name__)


class Dashboard2(DashboardBase):
    """Дашборд 2: круговая диаграмма и таблица.

    Реализует дашборд с двумя графиками:
    - Круговая диаграмма для отображения долей
    - Таблица для детального просмотра данных

    Поддерживаемые фильтры:
    - brand: фильтрация по бренду

    Атрибуты:
        config: Конфигурация дашборда
        _pie_chart: Компонент круговой диаграммы
        _table_chart: Компонент таблицы
        _layout: Макет дашборда
    """

    def __init__(self, config: DashboardConfig, token: str | None = None) -> None:
        """Инициализация дашборда 2.

        Args:
            config: Конфигурация дашборда
            token: Опциональный JWT токен для API вызовов
        """
        super().__init__(config, token)
        self._pie_chart: PieChart
        self._table_chart: TableChart
        self._layout = DashboardLayout()
        self._initialize_charts()
        logger.info("Создан экземпляр Dashboard2")

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

            if graph_type == "pie":
                self._pie_chart = PieChart(chart_config)
                logger.debug("Инициализирован PieChart")
            elif graph_type == "table":
                self._table_chart = TableChart(chart_config)
                logger.debug("Инициализирован TableChart")

        # Если графики не заданы в конфигурации, создаем стандартные
        if not self._pie_chart:
            default_pie_config = ChartConfig(
                x="brand",
                metrics=["revenue"],
                layout={
                    "title": "Доли по брендам",
                    "show_legend": True,
                    "show_percent": True,
                },
            )
            self._pie_chart = PieChart(default_pie_config)
            logger.debug("Создан PieChart с конфигурацией по умолчанию")

        if not self._table_chart:
            default_table_config = ChartConfig(
                x="brand",
                metrics=["revenue", "sales"],
                layout={
                    "title": "Детальная таблица",
                    "height": 400,
                },
            )
            self._table_chart = TableChart(default_table_config)
            logger.debug("Создан TableChart с конфигурацией по умолчанию")

    def get_data(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Получение данных для дашборда с применением фильтров.

        Выполняет запрос к API для получения агрегированных данных
        с учетом переданных фильтров.

        Args:
            filters: Словарь фильтров, где ключ - имя фильтра,
                     значение - значение фильтра
                     (например: {"brand": "Brand A"})

        Returns:
            Список словарей с данными. Каждая словарь представляет
            одну запись/точку данных.

        Raises:
            ConnectionError: При ошибке соединения с API
            ValueError: При ошибке API
        """
        logger.info(
            "Получение данных для Dashboard2 с фильтрами: %s",
            filters,
        )

        try:
            # Формируем параметры запроса
            params = {"dashboard_id": str(self.config.title or "2")}
            if filters:
                params.update(filters)

            # Выполняем запрос к API для получения данных с фильтрами
            response_data = self._make_api_request(
                endpoint="/data/filter",
                method="POST",
                data={
                    "dashboard_id": str(self.config.title or "2"),
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
        - brand: фильтрация по бренду (точное совпадение)

        Args:
            data: Список словарей с данными для фильтрации
            filters: Словарь фильтров, где ключ - имя поля,
                     значение - значение для фильтрации

        Returns:
            Отфильтрованный список словарей с данными

        Example:
            >>> data = [
            ...     {"brand": "Brand A", "revenue": 100},
            ...     {"brand": "Brand B", "revenue": 200},
            ... ]
            >>> dashboard.apply_filters(data, {"brand": "Brand A"})
            [{"brand": "Brand A", "revenue": 100}]
        """
        if not filters:
            logger.debug("Нет фильтров для применения")
            return data

        filtered_data = data

        # Фильтрация по бренду
        if "brand" in filters and filters["brand"] is not None:
            brand_value = filters["brand"]
            filtered_data = [
                item for item in filtered_data
                if item.get("brand") == brand_value
            ]
            logger.debug("Применен фильтр по бренду: %s", brand_value)

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
            >>> data = [{"brand": "A", "revenue": 100}, {"brand": "B", "revenue": 200}]
            >>> dashboard.render(data)
            {
                "type": "dashboard2",
                "layout": {...},
                "charts": {
                    "pie": {...},
                    "table": {...}
                }
            }
        """
        logger.info("Начало рендеринга Dashboard2")

        # Преобразуем данные в формат ChartData
        chart_data = ChartData(data=data)

        # Строим графики
        pie_figure = self._pie_chart.create_figure(chart_data)
        table_figure = self._table_chart.create_figure(chart_data)

        # Собираем макет дашборда
        self._layout.clear()
        self._layout.add_component(
            pie_figure,
            title="Распределение по брендам",
            width=6,
        )
        self._layout.add_component(
            table_figure,
            title="Детальная таблица",
            width=6,
        )

        # Формируем результат рендеринга
        result = {
            "type": "dashboard2",
            "title": self.config.title or "Дашборд 2: Анализ брендов",
            "description": self.config.description or "Круговая диаграмма и таблица",
            "layout": self._layout.assemble(),
            "charts": {
                "pie": pie_figure.to_plotly_json(),
                "table": table_figure.to_plotly_json(),
            },
            "filters": {
                "available": ["brand"],
                "current": {},
            },
        }

        logger.info("Рендеринг Dashboard2 завершен")

        return result
