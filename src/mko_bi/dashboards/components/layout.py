"""Макет дашборда.

Этот модуль предоставляет компонент DashboardLayout для
организации компонентов дашборда в сетку.

Особенности:
- Адаптивная сетка (Row/Col)
- Фильтры сверху, графики ниже
- Поддержка динамического добавления компонентов
"""

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html
from mko_bi.models.data import FilterState

logger = logging.getLogger(__name__)


class DashboardLayout:
    """Макет дашборда.

    Управляет компоновкой компонентов дашборда в адаптивную сетку.
    Фильтры размещаются в верхней части, графики - в основной области.

    Атрибуты:
        components: Список компонентов дашборда
        filter_panel: Панель фильтров
    """

    def __init__(self) -> None:
        """Инициализация макета дашборда."""
        self.components: list[dict[str, Any]] = []
        self.filter_panel = None
        logger.info("Создан макет дашборда")

    def add_filter_panel(self, filter_panel: Any) -> None:
        """Добавление панели фильтров.

        Args:
            filter_panel: Компонент панели фильтров
        """
        self.filter_panel = filter_panel
        logger.debug("Добавлена панель фильтров")

    def add_component(
        self,
        component: Any,
        title: str | None = None,
        width: int = 12,
        height: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Добавление компонента в макет.

        Args:
            component: Компонент дашборда (график и т.д.)
            title: Заголовок компонента
            width: Ширина компонента в сетке (1-12)
            height: Высота компонента (опционально)
            **kwargs: Дополнительные параметры
        """
        if not 1 <= width <= 12:
            raise ValueError("Ширина должна быть в диапазоне 1-12")

        component_config = {
            "component": component,
            "title": title,
            "width": width,
            "height": height,
            **kwargs,
        }
        self.components.append(component_config)
        logger.debug(
            "Добавлен компонент: %s (ширина: %d)",
            title or component.__class__.__name__,
            width,
        )

    def assemble(self, filter_state: FilterState | None = None) -> list[dbc.Row]:
        """Сборка макета дашборда.

        Создает адаптивную сетку с фильтрами сверху и графиками ниже.

        Args:
            filter_state: Текущее состояние фильтров (опционально)

        Returns:
            Список объектов dbc.Row для отображения в Dash
        """
        rows = []

        # Строка с фильтрами (если есть)
        if self.filter_panel:
            filter_row = self._create_filter_row(filter_state)
            rows.append(filter_row)

        # Строки с компонентами
        if self.components:
            component_rows = self._create_component_rows()
            rows.extend(component_rows)

        logger.info(
            "Макет собран: %d строк (фильтры: %d, компоненты: %d)",
            len(rows),
            1 if self.filter_panel else 0,
            len(self.components),
        )
        return rows

    def _create_filter_row(self, filter_state: FilterState | None) -> dbc.Row:
        """Создание строки с фильтрами.

        Args:
            filter_state: Состояние фильтров

        Returns:
            Объект dbc.Row с фильтрами
        """
        filter_content = []

        if hasattr(self.filter_panel, "filters"):
            for filter_config in self.filter_panel.filters:
                field = filter_config["field"]
                filter_type = filter_config["type"]
                label = filter_config.get("label", field)

                # Создаем элемент управления в зависимости от типа
                control = self._create_filter_control(
                    field, filter_type, filter_config, filter_state
                )

                filter_content.append(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([
                                html.H3(label, className="mb-3"),
                                control,
                            ]),
                            className="mb-3",
                        ),
                        width=12,
                        md=6,
                        lg=4,
                    )
                )

        return dbc.Row(
            dbc.Col(
                dbc.Card(
                dbc.CardBody([
                    html.H3("Фильтры", className="mb-3"),
                    dbc.Row(filter_content, className="g-3"),
                ]),
                    className="shadow-sm",
                ),
                width=12,
            ),
            className="mb-4",
        )

    def _create_filter_control(
        self,
        field: str,
        filter_type: str,
        filter_config: dict[str, Any],
        filter_state: FilterState | None,
    ) -> Any:
        """Создание элемента управления для фильтра.

        Args:
            field: Имя поля
            filter_type: Тип фильтра
            filter_config: Конфигурация фильтра
            filter_state: Состояние фильтров

        Returns:
            Элемент управления Dash/Bootstrap
        """
        # Получаем текущее значение
        current_value = None
        if filter_state and field in filter_state.filters:
            current_value = filter_state.filters[field]

        common_props = {
            "id": {"type": "filter", "field": field},
            "value": current_value,
        }

        if filter_type == "select":
            options = filter_config.get("options", [])
            return dbc.Select(
                options=[{"label": str(o), "value": o} for o in options],
                **common_props,
            )

        elif filter_type == "multiselect":
            options = filter_config.get("options", [])
            # In newer versions of dash-bootstrap-components, Select doesn't support multiple
            # Use a regular Select for now (single selection)
            return dbc.Select(
                options=[{"label": str(o), "value": o} for o in options],
                **common_props,
            )

        elif filter_type == "range":
            return dbc.Input(
                type="text",
                placeholder="min, max",
                **common_props,
            )

        elif filter_type == "date":
            return dbc.Input(
                type="date",
                **common_props,
            )

        else:
            return dbc.Input(
                type="text",
                **common_props,
            )

    def _create_component_rows(self) -> list[dbc.Row]:
        """Создание строк с компонентами.

        Группирует компоненты по строкам в зависимости от их ширины
        для оптимального использования пространства.

        Returns:
            Список объектов dbc.Row
        """
        rows = []
        current_row_components = []
        current_width = 0

        for component_config in self.components:
            width = component_config["width"]

            # Если компонент не помещается в текущую строку, создаем новую
            if current_width + width > 12 and current_row_components:
                rows.append(self._create_row(current_row_components))
                current_row_components = []
                current_width = 0

            current_row_components.append(component_config)
            current_width += width

        # Добавляем оставшиеся компоненты
        if current_row_components:
            rows.append(self._create_row(current_row_components))

        return rows

    def _create_row(self, component_configs: list[dict[str, Any]]) -> dbc.Row:
        """Создание строки с компонентами.

        Args:
            component_configs: Список конфигураций компонентов

        Returns:
            Объект dbc.Row
        """
        cols = []
        for config in component_configs:
            component = config["component"]
            title = config.get("title")
            width = config["width"]
            height = config.get("height")

            # Создаем карточку для компонента
            card_content = []

            if title:
                card_content.append(html.H3(title))

            card_content.append(component)

            card = dbc.Card(
                dbc.CardBody(card_content),
                className="shadow-sm h-100",
            )

            # Применяем высоту, если задана
            if height:
                card.style = {"height": f"{height}px"}

            cols.append(
                dbc.Col(
                    card,
                    width=width,
                    className="mb-4",
                )
            )

        return dbc.Row(
            cols,
            className="g-4",
        )

    def clear(self) -> None:
        """Очистка макета (удаление всех компонентов)."""
        self.components = []
        self.filter_panel = None
        logger.info("Макет очищен")

    @property
    def component_count(self) -> int:
        """Количество компонентов в макете.

        Returns:
            Количество компонентов
        """
        return len(self.components)

    def __repr__(self) -> str:
        """Строковое представление макета."""
        return (
            f"DashboardLayout(components={len(self.components)}, "
            f"has_filters={self.filter_panel is not None})"
        )