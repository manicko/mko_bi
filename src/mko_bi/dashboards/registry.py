"""Реестр и фабрика для управления дашбордами.

Этот модуль предоставляет функциональность регистрации,
создания и кэширования экземпляров дашбордов.
"""

import json
import logging
from hashlib import md5

from mko_bi.dashboards.base import DashboardBase
from mko_bi.models.dashboard import DashboardConfig

logger = logging.getLogger(__name__)


class DashboardRegistry:
    """Реестр и фабрика для управления дашбордами.

    Отвечает за:
    - Регистрацию классов дашбордов
    - Создание экземпляров (фабрика)
    - Кэширование экземпляров с учетом конфигурации

    Атрибуты:
        _registry: Словарь зарегистрированных классов дашбордов
        _instances: Словарь кэшированных экземпляров
    """

    def __init__(self) -> None:
        """Инициализация реестра дашбордов."""
        self._registry: dict[str, type[DashboardBase]] = {}
        self._instances: dict[tuple[str, str], DashboardBase] = {}
        logger.info("Инициализирован DashboardRegistry")

    def register(self, name: str, dashboard_cls: type[DashboardBase]) -> None:
        """Регистрация класса дашборда.

        Регистрирует класс дашборда под указанным именем.
        Если имя уже занято, вызывается исключение ValueError.

        Args:
            name: Имя дашборда для регистрации
            dashboard_cls: Класс дашборда, наследник DashboardBase

        Raises:
            ValueError: Если дашборд с таким именем уже зарегистрирован
            TypeError: Если dashboard_cls не является наследником DashboardBase

        Example:
            >>> registry.register("sales", SalesDashboard)
        """
        if name in self._registry:
            logger.error("Попытка повторной регистрации дашборда: %s", name)
            raise ValueError(
                f"Дашборд с именем '{name}' уже зарегистрирован. "
                f"Используйте другое имя или удалите существующий дашборд."
            )

        if not issubclass(dashboard_cls, DashboardBase):
            logger.error(
                "Попытка зарегистрировать некорректный класс: %s",
                dashboard_cls.__name__,
            )
            raise TypeError(
                f"Класс {dashboard_cls.__name__} должен наследоваться от DashboardBase"
            )

        self._registry[name] = dashboard_cls
        logger.info("Зарегистрирован дашборд: %s -> %s", name, dashboard_cls.__name__)

    def _generate_config_hash(self, config: DashboardConfig) -> str:
        """Генерация хеша конфигурации для кэширования.

        Создает уникальный хеш на основе конфигурации дашборда,
        который используется как ключ для кэширования экземпляров.

        Args:
            config: Конфигурация дашборда

        Returns:
            Строковое представление MD5 хеша конфигурации
        """
        config_dict = config.model_dump(mode="json")
        config_json = json.dumps(config_dict, sort_keys=True)
        config_hash = md5(config_json.encode()).hexdigest()
        logger.debug("Сгенерирован хеш конфигурации: %s", config_hash)
        return config_hash

    def get(self, name: str, config: DashboardConfig) -> DashboardBase:
        """Получение экземпляра дашборда.

        Возвращает экземпляр дашборда по имени. Если экземпляр
        с такой конфигурацией уже существует в кэше, возвращает
        его. В противном случае создает новый экземпляр,
        сохраняет в кэш и возвращает.

        Args:
            name: Имя зарегистрированного дашборда
            config: Конфигурация дашборда

        Returns:
            Экземпляр дашборда

        Raises:
            KeyError: Если дашборд с указанным именем не найден

        Example:
            >>> dashboard = registry.get("sales", config)
        """
        if name not in self._registry:
            logger.error("Попытка получить несуществующий дашборд: %s", name)
            available = ", ".join(self._registry.keys())
            raise KeyError(
                f"Дашборд '{name}' не найден в реестре. "
                f"Доступные дашборды: {available}"
            )

        config_hash = self._generate_config_hash(config)
        cache_key = (name, config_hash)

        if cache_key in self._instances:
            logger.info(
                "Возвращен кэшированный экземпляр дашборда: %s (hash: %s)",
                name,
                config_hash[:8],
            )
            return self._instances[cache_key]

        dashboard_cls = self._registry[name]
        instance = dashboard_cls(config)
        self._instances[cache_key] = instance
        logger.info(
            "Создан и закэширован новый экземпляр дашборда: %s (hash: %s)",
            name,
            config_hash[:8],
        )
        return instance

    def exists(self, name: str) -> bool:
        """Проверка существования дашборда в реестре.

        Args:
            name: Имя дашборда для проверки

        Returns:
            True, если дашборд зарегистрирован, иначе False

        Example:
            >>> if registry.exists("sales"):
            ...     print("Дашборд доступен")
        """
        exists = name in self._registry
        logger.debug("Проверка существования дашборда '%s': %s", name, exists)
        return exists

    def clear_cache(self) -> None:
        """Очистка кэша экземпляров дашбордов.

        Удаляет все кэшированные экземпляры дашбордов.
        Словарь регистрации классов остается неизменным.

        Example:
            >>> registry.clear_cache()
        """
        count = len(self._instances)
        self._instances.clear()
        logger.info("Очищен кэш экземпляров дашбордов (удалено: %d)", count)

    @property
    def registered_dashboards(self) -> list[str]:
        """Получение списка зарегистрированных дашбордов.

        Returns:
            Список имен зарегистрированных дашбордов
        """
        return list(self._registry.keys())

    def __repr__(self) -> str:
        """Строковое представление реестра.

        Returns:
            Строка с информацией о реестре
        """
        return (
            f"DashboardRegistry(" 
            f"registered={len(self._registry)}, "
            f"cached={len(self._instances)}"
            f")"
        )


# Модульный экземпляр реестра (синглтон на уровне модуля)
registry = DashboardRegistry()
"""Глобальный экземпляр реестра дашбордов.

Этот экземпляр должен использоваться для регистрации и получения
экземпляров дашбордов во всем приложении.
"""


def register(name: str):
    """Декоратор для регистрации классов дашбордов.

    Удобный декоратор, позволяющий зарегистрировать класс дашборда
    сразу после его определения.

    Args:
        name: Имя дашборда для регистрации

    Returns:
        Декоратор, регистрирующий класс

    Example:
        >>> @registry.register("sales")
        ... class SalesDashboard(DashboardBase):
        ...     def get_data(self, filters):
        ...         return []
        ...     def apply_filters(self, data, filters):
        ...         return data
        ...     def render(self, data):
        ...         return {}
    """

    def decorator(dashboard_cls: type[DashboardBase]) -> type[DashboardBase]:
        registry.register(name, dashboard_cls)
        return dashboard_cls

    return decorator