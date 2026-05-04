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
from mko_bi.models.enums import FilterType

logger = logging.getLogger(__name__)


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
        filter_type: FilterType | str,
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
        filter_type_str = filter_type.value if isinstance(filter_type, FilterType) else filter_type
        valid_types = [ft.value for ft in FilterType]
        if filter_type_str not in valid_types:
            raise ValueError(f"Некорректный тип фильтра: {filter_type}")

        filter_config: dict[str, Any] = {
            "field": field,
            "type": filter_type_str,
            "label": label or field,
            **kwargs,
        }

        if options is not None:
            filter_config["options"] = options

        self.filters.append(filter_config)
        logger.debug("Добавлен фильтр: %s (тип: %s)", field, filter_type_str)

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
        logger.debug("Применение фильтра '%s' (тип: %s)", field, filter_type)

        if filter_type == FilterType.SELECT.value:
            return self._apply_select_filter(data, field, value)
        elif filter_type == FilterType.MULTISELECT.value:
            return self._apply_multiselect_filter(data, field, value)
        elif filter_type == FilterType.RANGE.value:
            return self._apply_range_filter(data, field, value)
        elif filter_type == FilterType.DATE.value:
            return self._apply_date_filter(data, field, value)

        return data

    def _apply_select_filter(
        self,
        data: list[dict[str, Any]],
        field: str,
        value: Any,
    ) -> list[dict[str, Any]]:
        """Применение фильтра типа select.

        Args:
            data: Список данных
            field: Поле для фильтрации
            value: Значение для выбора

        Returns:
            Отфильтрованные данные
        """
        logger.debug("Фильтр select: %s = %s", field, value)
        return [item for item in data if item.get(field) == value]

    def _apply_multiselect_filter(
        self,
        data: list[dict[str, Any]],
        field: str,
        value: Any,
    ) -> list[dict[str, Any]]:
        """Применение фильтра типа multiselect.

        Args:
            data: Список данных
            field: Поле для фильтрации
            value: Список значений для выбора

        Returns:
            Отфильтрованные данные
        """
        if not isinstance(value, list):
            value = [value]
        logger.debug("Фильтр multiselect: %s in %s", field, value)
        return [item for item in data if item.get(field) in value]

    def _apply_range_filter(
        self,
        data: list[dict[str, Any]],
        field: str,
        value: Any,
    ) -> list[dict[str, Any]]:
        """Применение фильтра типа range.

        Args:
            data: Список данных
            field: Поле для фильтрации
            value: Кортеж (min_val, max_val)

        Returns:
            Отфильтрованные данные
        """
        if isinstance(value, (list, tuple)) and len(value) == 2:
            min_val, max_val = value
            logger.debug("Фильтр range: %s [%s, %s]", field, min_val, max_val)
            return [
                item
                for item in data
                if min_val <= item.get(field, float("-inf")) <= max_val
            ]
        return data

    def _apply_date_filter(
        self,
        data: list[dict[str, Any]],
        field: str,
        value: Any,
    ) -> list[dict[str, Any]]:
        """Применение фильтра типа date.

        Args:
            data: Список данных
            field: Поле для фильтрации
            value: Дата для фильтрации

        Returns:
            Отфильтрованные данные
        """
        logger.debug("Фильтр date: %s = %s", field, value)
        return [item for item in data if item.get(field) == value]

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
