"""Панель фильтров для дашбордов.

Этот модуль предоставляет компонент FilterPanel для управления
фильтрацией данных в дашбордах.

Поддерживаемые типы фильтров:
- select: Выпадающий список с одним выбором
- multiselect: Выпадающий список с множественным выбором
- range: Диапазон значений (числовой или дат)
- date: Выбор даты
"""

import logging
from typing import Any

from mko_bi.models.data import FilterState

logger = logging.getLogger(__name__)


class FilterType:
    """Типы фильтров."""

    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"


class FilterPanel:
    """Панель фильтров для дашборда.

    Управляет состоянием фильтров и предоставляет методы
    для их применения к данным.

    Атрибуты:
        filters: Список конфигураций фильтров
        state: Текущее состояние фильтров
    """

    def __init__(self, filters: list[dict[str, Any]] | None = None) -> None:
        """Инициализация панели фильтров.

        Args:
            filters: Список конфигураций фильтров.
                     Каждая конфигурация должна содержать:
                     - field: имя поля
                     - type: тип фильтра
                     - label: отображаемое имя
                     - options: доступные значения (для select/multiselect)
        """
        self.filters = filters or []
        self.state = FilterState()
        logger.info(
            "Создана панель фильтров с %d фильтром(ами)",
            len(self.filters),
        )

    def add_filter(
        self,
        field: str,
        filter_type: str,
        label: str | None = None,
        options: list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Добавление нового фильтра.

        Args:
            field: Имя поля для фильтрации
            filter_type: Тип фильтра (select, multiselect, range, date)
            label: Отображаемое имя фильтра
            options: Доступные значения для select/multiselect
            **kwargs: Дополнительные параметры фильтра

        Raises:
            ValueError: Если тип фильтра некорректен
        """
        if filter_type not in [
            FilterType.SELECT,
            FilterType.MULTISELECT,
            FilterType.RANGE,
            FilterType.DATE,
        ]:
            raise ValueError(f"Некорректный тип фильтра: {filter_type}")

        filter_config = {
            "field": field,
            "type": filter_type,
            "label": label or field,
            **kwargs,
        }

        if options is not None:
            filter_config["options"] = options

        self.filters.append(filter_config)
        logger.debug("Добавлен фильтр: %s (тип: %s)", field, filter_type)

    def remove_filter(self, field: str) -> bool:
        """Удаление фильтра.

        Args:
            field: Имя поля фильтра

        Returns:
            True, если фильтр был удален, False - если не найден
        """
        initial_count = len(self.filters)
        self.filters = [f for f in self.filters if f["field"] != field]

        removed = len(self.filters) < initial_count
        if removed:
            logger.debug("Удален фильтр: %s", field)
            # Удаляем значение из состояния
            if field in self.state.filters:
                del self.state.filters[field]

        return removed

    def update_filter_value(self, field: str, value: Any) -> None:
        """Обновление значения фильтра.

        Args:
            field: Имя поля фильтра
            value: Новое значение

        Raises:
            KeyError: Если фильтр с таким полем не найден
        """
        if not any(f["field"] == field for f in self.filters):
            raise KeyError(f"Фильтр с полем '{field}' не найден")

        self.state.filters[field] = value
        logger.debug("Обновлено значение фильтра '%s': %s", field, value)

    def get_filter_values(self, inputs: dict[str, Any] | None = None) -> FilterState:
        """Получение текущих значений фильтров.

        Args:
            inputs: Входные значения от UI (опционально).
                    Если не переданы, используются текущие значения из состояния.

        Returns:
            Объект FilterState с текущими значениями фильтров
        """
        if inputs is not None:
            # Обновляем состояние из входных данных
            for field, value in inputs.items():
                if any(f["field"] == field for f in self.filters):
                    self.state.filters[field] = value

        logger.info(
            "Получены значения фильтров: %d активных фильтра(ов)",
            len(self.state.filters),
        )
        return self.state

    def apply_filters(
        self,
        data: list[dict[str, Any]],
        filter_state: FilterState | None = None,
    ) -> list[dict[str, Any]]:
        """Применение фильтров к данным.

        Args:
            data: Список словарей с данными для фильтрации
            filter_state: Состояние фильтров (опционально,
                          если не передано, используется текущее состояние)

        Returns:
            Отфильтрованный список данных
        """
        state = filter_state or self.state

        if not state.filters:
            logger.debug("Нет активных фильтров, данные не изменены")
            return data

        filtered_data = data
        for field, value in state.filters.items():
            if value is None or value == []:
                continue

            filter_config = next(
                (f for f in self.filters if f["field"] == field), None
            )

            if not filter_config:
                logger.warning("Конфигурация фильтра '%s' не найдена", field)
                continue

            filter_type = filter_config["type"]
            filtered_data = self._apply_single_filter(
                filtered_data, field, value, filter_type
            )

        logger.info(
            "Фильтрация завершена: %d -> %d записей",
            len(data),
            len(filtered_data),
        )
        return filtered_data

    def _apply_single_filter(
        self,
        data: list[dict[str, Any]],
        field: str,
        value: Any,
        filter_type: str,
    ) -> list[dict[str, Any]]:
        """Применение одного фильтра к данным.

        Args:
            data: Список данных
            field: Поле для фильтрации
            value: Значение фильтра
            filter_type: Тип фильтра

        Returns:
            Отфильтрованные данные
        """
        if filter_type == FilterType.SELECT:
            return [item for item in data if item.get(field) == value]

        elif filter_type == FilterType.MULTISELECT:
            if not isinstance(value, list):
                value = [value]
            return [item for item in data if item.get(field) in value]

        elif filter_type == FilterType.RANGE:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                min_val, max_val = value
                return [
                    item
                    for item in data
                    if min_val <= item.get(field, float("-inf")) <= max_val
                ]

        elif filter_type == FilterType.DATE:
            # Для дат применяем точное совпадение
            return [item for item in data if item.get(field) == value]

        return data

    def reset(self) -> None:
        """Сброс всех значений фильтров."""
        self.state = FilterState()
        logger.info("Панель фильтров сброшена")

    @property
    def active_filters(self) -> dict[str, Any]:
        """Получение активных фильтров.

        Returns:
            Словарь активных фильтров (только с непустыми значениями)
        """
        return {
            field: value
            for field, value in self.state.filters.items()
            if value not in (None, [], "")
        }

    def __repr__(self) -> str:
        """Строковое представление панели фильтров."""
        return (
            f"FilterPanel(filters={len(self.filters)}, "
            f"active={len(self.active_filters)})"
        )