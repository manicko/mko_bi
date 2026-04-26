"""Реестр трансформаций для пайплайна обработки данных.

Этот модуль предоставляет реестр для управления доступными
трансформациями и их применения к данным.
"""

import logging
from typing import Any, TypeVar
from collections.abc import Callable

import polars as pl

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Any])


class TransformationRegistry:
    """Реестр трансформаций.

    Управляет регистрацией и применением различных
    трансформаций к данным. Поддерживает фильтрацию, группировку,
    сортировку и другие операции.

    Attributes:
        _transformations: Словарь зарегистрированных трансформаций.
    """

    def __init__(self) -> None:
        """Инициализация реестра трансформаций."""
        self._transformations: dict[str, Callable[..., Any]] = {}
        logger.debug("TransformationRegistry инициализирован")

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Регистрирует новую трансформацию.

        Args:
            name: Имя трансформации.
            func: Функция трансформации.

        Raises:
            ValueError: Если трансформация с таким именем уже зарегистрирована.
        """
        if name in self._transformations:
            error_msg = f"Трансформация '{name}' уже зарегистрирована"
            logger.error(error_msg)
            raise ValueError(error_msg)

        self._transformations[name] = func
        logger.debug("Трансформация '%s' успешно зарегистрирована", name)

    def get(self, name: str) -> Callable[..., Any] | None:
        """Получает зарегистрированную трансформацию по имени.

        Args:
            name: Имя трансформации.

        Returns:
            Callable: Функция трансформации или None, если не найдена.
        """
        transformation = self._transformations.get(name)
        if transformation is None:
            logger.warning("Трансформация '%s' не найдена в реестре", name)
        else:
            logger.debug("Трансформация '%s' получена из реестра", name)
        return transformation

    def apply(
        self,
        df: pl.DataFrame,
        transformation_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> pl.DataFrame:
        """Применяет зарегистрированную трансформацию к данным.

        Args:
            df: Исходный DataFrame.
            transformation_name: Имя трансформации.
            *args: Позиционные аргументы для функции трансформации.
            **kwargs: Именованные аргументы для функции трансформации.

        Returns:
            pl.DataFrame: Трансформированный DataFrame.

        Raises:
            ValueError: Если трансформация не найдена.
        """
        transformation = self.get(transformation_name)
        if transformation is None:
            error_msg = f"Трансформация '{transformation_name}' не найдена"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Применение трансформации '%s'", transformation_name)
        result = transformation(df, *args, **kwargs)
        logger.debug(
            "Трансформация '%s' применена: %d строк, %d колонок",
            transformation_name,
            result.shape[0],
            result.shape[1],
        )
        return result

    def list_transformations(self) -> list[str]:
        """Возвращает список всех зарегистрированных трансформаций.

        Returns:
            List[str]: Список имен трансформаций.
        """
        transformations = list(self._transformations.keys())
        logger.debug("Доступные трансформации: %s", transformations)
        return transformations

    def has_transformation(self, name: str) -> bool:
        """Проверяет наличие трансформации в реестре.

        Args:
            name: Имя трансформации.

        Returns:
            bool: True, если трансформация зарегистрирована.
        """
        has = name in self._transformations
        logger.debug("Проверка трансформации '%s': %s", name, has)
        return has