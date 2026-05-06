"""Базовый класс для дашбордов.

Этот модуль предоставляет абстрактный базовый класс для всех дашбордов,
определяющий интерфейс и базовое поведение.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import requests
from mkobi.config import get_config
from mkobi.models.dashboard import DashboardConfig

logger = logging.getLogger(__name__)


class DashboardBase(ABC):
    """Абстрактный базовый класс для дашбордов.

    Все конкретные реализации дашбордов должны наследоваться от этого класса
    и реализовывать все абстрактные методы.

    Attributes:
        config: Конфигурация дашборда типа DashboardConfig
        token: JWT токен для API вызовов
        api_base_url: Базовый URL API
    """

    def __init__(self, config: DashboardConfig, token: str | None = None) -> None:
        """Инициализация базового дашборда.

        Args:
            config: Конфигурация дашборда
            token: Опциональный JWT токен для API вызовов
        """
        self.config = config
        self.token = token
        self.api_base_url = get_config().API_BASE_URL
        logger.info(
            "Создан экземпляр дашборда %s с конфигурацией: %s",
            self.__class__.__name__,
            config.title or "Без названия",
        )

    def get_token(self) -> str | None:
        """Возвращает JWT токен для API вызовов.

        Returns:
            JWT токен или None, если токен не установлен
        """
        return self.token

    def set_token(self, token: str) -> None:
        """Устанавливает JWT токен для API вызовов.

        Args:
            token: JWT токен
        """
        self.token = token
        logger.debug("Токен обновлен для дашборда %s", self.__class__.__name__)

    def _make_api_request(
        self, endpoint: str, method: str = "GET", params: dict[str, Any] | None = None, data: dict[str, Any] | None = None
    ) -> Any:
        """Выполняет запрос к API и возвращает результат.

        Args:
            endpoint: Эндпоинт API (без базового URL)
            method: HTTP метод (GET, POST, etc.)
            params: Параметры запроса для GET
            data: Данные запроса для POST

        Returns:
            Результат запроса (JSON)

        Raises:
            ConnectionError: При ошибке соединения
            ValueError: При ошибке API (не 200 статус)
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            logger.debug("API запрос: %s %s", method, url)
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Неподдерживаемый HTTP метод: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            logger.error("Ошибка соединения с API: %s", e)
            raise ConnectionError(f"Не удалось подключиться к API: {url}") from e
        except requests.exceptions.HTTPError as e:
            logger.error("Ошибка API %s: %s", response.status_code, response.text)
            raise ValueError(f"Ошибка API: {response.status_code} - {response.text}") from e
        except Exception as e:
            logger.error("Неожиданная ошибка при запросе к API: %s", e)
            raise

    @abstractmethod
    def get_data(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Получение данных для дашборда с применением фильтров.

        Этот метод должен быть реализован в конкретных классах дашбордов
        для получения данных из источника (база данных, API, файлы и т.д.)
        с учетом переданных фильтров.

        Args:
            filters: Словарь фильтров, где ключ - имя фильтра,
                     значение - значение фильтра

        Returns:
            Список словарей с данными. Каждый словарь представляет
            одну запись/точку данных.

        Example:
            >>> dashboard.get_data({"year": 2024, "category": "electronics"})
            [{"category": "electronics", "revenue": 100000}, ...]
        """
        ...

    @abstractmethod
    def apply_filters(self, data: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Применение фильтров к уже полученным данным.

        Этот метод фильтрует данные на стороне приложения, когда
        фильтрация на уровне источника данных невозможна или неэффективна.

        Args:
            data: Список словарей с данными для фильтрации
            filters: Словарь фильтров, где ключ - имя поля,
                     значение - значение для фильтрации

        Returns:
            Отфильтрованный список словарей с данными

        Example:
            >>> data = [{"year": 2023, "revenue": 100}, {"year": 2024, "revenue": 200}]
            >>> dashboard.apply_filters(data, {"year": 2024})
            [{"year": 2024, "revenue": 200}]
        """
        ...

    @abstractmethod
    def render(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Рендеринг данных в формат для отображения.

        Преобразует сырые данные в формат, готовый для отображения
        в веб-интерфейсе (например, в формате Plotly или табличном виде).

        Args:
            data: Список словарей с данными для рендеринга

        Returns:
            Словарь с отрендеренными данными, готовыми для передачи
            во фронтенд. Структура зависит от типа дашборда.

        Example:
            >>> data = [{"category": "A", "value": 100}, {"category": "B", "value": 200}]
            >>> dashboard.render(data)
            {"type": "bar", "data": {...}, "layout": {...}}
        """
        ...