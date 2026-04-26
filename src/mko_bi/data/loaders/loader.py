"""CSV загрузчик данных.

Этот модуль предоставляет класс для загрузки и чтения CSV файлов,
включая поддержку сжатых .csv.gz файлов.
"""

import gzip
import logging
from pathlib import Path
from typing import Any

import polars as pl

from mko_bi.models.data import LoaderConfig

logger = logging.getLogger(__name__)


class CSVLoader:
    """Загрузчик CSV файлов.

    Отвечает за чтение CSV файлов (включая сжатые .csv.gz),
    проверку структуры данных и преобразование типов.

    Attributes:
        config: Конфигурация загрузчика.
    """

    def __init__(self, config: LoaderConfig | None = None) -> None:
        """Инициализация загрузчика.

        Args:
            config: Опциональная конфигурация загрузчика.
        """
        self.config = config or LoaderConfig()
        logger.debug("CSVLoader инициализирован с config=%s", self.config)

    def load(self, file_path: Path) -> pl.DataFrame:
        """Загружает CSV файл и возвращает DataFrame.

        Читает CSV файл (поддерживает .csv.gz), применяет
        преобразования типов данных согласно конфигурации.

        Args:
            file_path: Путь к CSV файлу.

        Returns:
            pl.DataFrame: Загруженные данные.

        Raises:
            FileNotFoundError: Если файл не существует.
            ValueError: Если файл не может быть прочитан.
        """
        logger.info("Загрузка файла: %s", file_path)

        if not file_path.exists():
            logger.error("Файл не найден: %s", file_path)
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        try:
            df = self._read_csv(file_path)
            logger.info(
                "Файл прочитан: %d строк, %d колонок",
                df.shape[0],
                df.shape[1],
            )

            # Применяем преобразования типов
            if self.config.column_types:
                df = self._apply_type_transformations(df)

            # Проверяем обязательные колонки
            if self.config.required_columns:
                self._validate_required_columns(df)

            return df

        except Exception as e:
            logger.error("Ошибка при загрузке файла %s: %s", file_path, e)
            raise ValueError(f"Не удалось загрузить файл {file_path}: {e}") from e

    def _read_csv(self, file_path: Path) -> pl.DataFrame:
        """Читает CSV файл (поддерживает gzip сжатие).

        Args:
            file_path: Путь к CSV файлу.

        Returns:
            pl.DataFrame: Прочитанные данные.
        """
        try:
            if file_path.suffix == ".gz" or file_path.name.endswith(".csv.gz"):
                logger.debug("Чтение gzipped CSV файла: %s", file_path)
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    return pl.read_csv(f)
            else:
                logger.debug("Чтение обычного CSV файла: %s", file_path)
                return pl.read_csv(file_path)
        except Exception as e:
            logger.error("Ошибка чтения CSV файла %s: %s", file_path, e)
            raise

    def _apply_type_transformations(self, df: pl.DataFrame) -> pl.DataFrame:
        """Применяет преобразования типов колонок.

        Args:
            df: Исходный DataFrame.

        Returns:
            pl.DataFrame: DataFrame с преобразованными типами.
        """
        logger.debug("Применение преобразований типов")

        for column_name, target_type in self.config.column_types.items():
            if column_name in df.columns:
                try:
                    if target_type == "int":
                        df = df.with_columns(pl.col(column_name).cast(pl.Int64))
                    elif target_type == "float":
                        df = df.with_columns(pl.col(column_name).cast(pl.Float64))
                    elif target_type == "str":
                        df = df.with_columns(pl.col(column_name).cast(pl.Utf8))
                    elif target_type == "date":
                        df = df.with_columns(pl.col(column_name).cast(pl.Date))
                    elif target_type == "datetime":
                        df = df.with_columns(pl.col(column_name).cast(pl.Datetime))
                    elif target_type == "bool":
                        df = df.with_columns(pl.col(column_name).cast(pl.Boolean))
                    else:
                        logger.warning(
                            "Неизвестный тип данных '%s' для колонки '%s'",
                            target_type,
                            column_name,
                        )
                        continue

                    logger.debug(
                        "Колонка '%s' преобразована в тип '%s'",
                        column_name,
                        target_type,
                    )
                except Exception as e:
                    logger.warning(
                        "Не удалось преобразовать колонку '%s' в тип '%s': %s",
                        column_name,
                        target_type,
                        e,
                    )
            else:
                logger.warning(
                    "Колонка '%s' не найдена в данных, пропуск преобразования",
                    column_name,
                )

        return df

    def _validate_required_columns(self, df: pl.DataFrame) -> None:
        """Проверяет наличие обязательных колонок.

        Args:
            df: DataFrame для проверки.

        Raises:
            ValueError: Если обязательные колонки отсутствуют.
        """
        missing_columns = [
            col for col in self.config.required_columns if col not in df.columns
        ]

        if missing_columns:
            error_msg = (
                f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Все обязательные колонки присутствуют")

    def get_summary(self, df: pl.DataFrame) -> dict[str, Any]:
        """Возвращает сводную информацию о DataFrame.

        Args:
            df: DataFrame для анализа.

        Returns:
            dict: Сводная информация о данных.
        """
        return {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": df.columns,
            "column_types": {col: str(df[col].dtype) for col in df.columns},
            "memory_usage": df.estimated_size(),
        }

    def filter_data(
        self,
        df: pl.DataFrame,
        conditions: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """Применяет фильтры к данным.

        Args:
            df: Исходный DataFrame.
            conditions: Список условий фильтрации.
                Каждое условие - словарь с ключами:
                - column: имя колонки
                - operator: оператор (==, !=, >, <, >=, <=)
                - value: значение для сравнения

        Returns:
            pl.DataFrame: Отфильтрованные данные.
        """
        logger.debug("Применение фильтров: %s", conditions)

        result = df
        for condition in conditions:
            column = condition["column"]
            operator = condition["operator"]
            value = condition["value"]

            if operator == "==":
                result = result.filter(pl.col(column) == value)
            elif operator == "!=":
                result = result.filter(pl.col(column) != value)
            elif operator == ">":
                result = result.filter(pl.col(column) > value)
            elif operator == "<":
                result = result.filter(pl.col(column) < value)
            elif operator == ">=":
                result = result.filter(pl.col(column) >= value)
            elif operator == "<=":
                result = result.filter(pl.col(column) <= value)
            else:
                logger.warning("Неизвестный оператор фильтрации: %s", operator)
                continue

            logger.debug("Применен фильтр: %s %s %s", column, operator, value)

        return result

    def aggregate(
        self,
        df: pl.DataFrame,
        groupby: list[str],
        aggregations: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """Выполняет группировку и агрегацию данных.

        Args:
            df: Исходный DataFrame.
            groupby: Список колонок для группировки.
            aggregations: Список агрегаций.
                Каждая агрегация - словарь с ключами:
                - column: имя колонки
                - function: функция агрегации (sum, mean, count, min, max)
                - alias: опциональное имя результирующей колонки

        Returns:
            pl.DataFrame: Агрегированные данные.
        """
        logger.debug(
            "Агрегация: группировка по %s, агрегации %s",
            groupby,
            aggregations,
        )

        agg_exprs = []
        for agg in aggregations:
            column = agg["column"]
            function = agg["function"]
            alias = agg.get("alias", f"{column}_{function}")

            if function == "sum":
                expr = pl.col(column).sum().alias(alias)
            elif function == "mean":
                expr = pl.col(column).mean().alias(alias)
            elif function == "count":
                expr = pl.col(column).count().alias(alias)
            elif function == "min":
                expr = pl.col(column).min().alias(alias)
            elif function == "max":
                expr = pl.col(column).max().alias(alias)
            else:
                logger.warning("Неизвестная функция агрегации: %s", function)
                continue

            agg_exprs.append(expr)

        result = df.group_by(groupby).agg(agg_exprs)
        logger.info(
            "Агрегация выполнена: %d групп, %d колонок",
            result.shape[0],
            result.shape[1],
        )

        return result
