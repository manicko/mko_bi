"""Базовый процессор данных для пайплайна обработки.

Этот модуль предоставляет базовый класс для оркестрации пайплайна
трансформации и агрегации данных.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)


class DataProcessor(ABC):
    """Базовый класс процессора данных.

    Отвечает за оркестрацию всего пайплайна обработки данных:
    - чтение данных
    - применение трансформаций
    - расчет агрегаций
    - сохранение результатов

    Attributes:
        config: Конфигурация процессора.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Инициализация процессора данных.

        Args:
            config: Опциональная конфигурация процессора.
        """
        self.config = config or {}
        logger.debug("DataProcessor инициализирован с config=%s", self.config)

    @abstractmethod
    def process(self, data: pl.DataFrame) -> pl.DataFrame:
        """Выполняет полный пайплайн обработки данных.

        Args:
            data: Исходный DataFrame.

        Returns:
            pl.DataFrame: Обработанный DataFrame.
        """
        pass

    def _validate_input(self, data: pl.DataFrame) -> None:
        """Проверяет входные данные перед обработкой.

        Args:
            data: DataFrame для проверки.

        Raises:
            ValueError: Если данные не валидны.
        """
        if data.shape[0] == 0:
            error_msg = "Входные данные пустые (нет строк)"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if data.shape[1] == 0:
            error_msg = "Входные данные пустые (нет колонок)"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(
            "Входные данные валидны: %d строк, %d колонок",
            data.shape[0],
            data.shape[1],
        )

    def _log_processing_stats(self, data: pl.DataFrame, stage: str) -> None:
        """Логирует статистику обработки на текущем этапе.

        Args:
            data: DataFrame на текущем этапе.
            stage: Название этапа обработки.
        """
        logger.info(
            "[%s] Статистика: %d строк, %d колонок",
            stage,
            data.shape[0],
            data.shape[1],
        )