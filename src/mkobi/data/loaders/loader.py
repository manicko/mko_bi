"""CSV загрузчик данных.

Этот модуль предоставляет класс для загрузки и чтения CSV файлов,
включая поддержку сжатых .csv.gz файлов.
"""

import gzip
import logging
from pathlib import Path
from typing import Any

import polars as pl

from mkobi.config import get_config
from mkobi.models.data import LoaderConfig

logger = logging.getLogger(__name__)


async def load_csv(filepath: Path, config: dict | None = None) -> pl.DataFrame:
    """Асинхронная загрузка CSV файла.

    Обертка над синхронным CSVLoader для использования в асинхронном коде.
    Поддерживает .csv и .csv.gz файлы, UTF-8 кодировку.

    Args:
        filepath: Путь к CSV файлу.
        config: Опциональная конфигурация для чтения (separator, has_header, etc.).

    Returns:
        pl.DataFrame: Загруженные данные.

    Raises:
        FileNotFoundError: Если файл не существует.
        ValueError: Если файл не может быть прочитан.
    """
    loader = CSVLoader()
    if config:
        loader.config = LoaderConfig(**config)
    return await asyncio.to_thread(loader.load_csv, filepath, config)


def detect_file_type(filename: str) -> str:
    """Detect file type based on filename extension.

    Args:
        filename: Name of the file.

    Returns:
        str: "csv" for .csv files, "csv_gz" for .csv.gz files, "unknown" otherwise.
    """
    if filename.endswith(".csv.gz"):
        return "csv_gz"
    elif filename.endswith(".csv"):
        return "csv"
    else:
        return "unknown"


class CSVLoader:
    """Загрузчик CSV файлов.

    Отвечает за чтение CSV файлов (включая сжатые .csv.gz),
    проверку структуры данных и преобразование типов.
    Поддерживает lazy loading для больших файлов.

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

    def load_csv(
        self,
        file_path: Path,
        config: dict[str, Any] | None = None,
        lazy_threshold_mb: float | None = None,
    ) -> pl.DataFrame:
        """Загружает CSV файл с поддержкой lazy loading для больших файлов.

        Читает CSV файл (поддерживает .csv и .csv.gz).
        Для файлов больше lazy_threshold_mb использует lazy evaluation.
        Выполняет валидацию размера файла.

        Args:
            file_path: Путь к CSV файлу.
            config: Опциональная конфигурация для чтения CSV (separator, has_header, encoding, etc.).
            lazy_threshold_mb: Порог в МБ для lazy loading.
                Если None, берется из конфигурации приложения.

        Returns:
            pl.DataFrame: Загруженные данные.

        Raises:
            FileNotFoundError: Если файл не существует.
            ValueError: Если файл слишком большой или не может быть прочитан.
        """
        logger.info("Загрузка CSV файла: %s", file_path)

        if not file_path.exists():
            logger.error("Файл не найден: %s", file_path)
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        # Валидация размера файла
        self._validate_file_size(file_path)

        # Определение порога для lazy loading
        if lazy_threshold_mb is None:
            app_config = get_config()
            lazy_threshold_mb = app_config.lazy_threshold_mb

        file_size_mb = self._get_file_size_mb(file_path)

        # Чтение файла
        try:
            if file_size_mb > lazy_threshold_mb:
                logger.info(
                    "Используется lazy evaluation для файла %.2f MB (порог: %.2f MB)",
                    file_size_mb,
                    lazy_threshold_mb,
                )
                df = self._read_csv_lazy(file_path, config)
            else:
                logger.info(
                    "Используется обычное чтение для файла %.2f MB (порог: %.2f MB)",
                    file_size_mb,
                    lazy_threshold_mb,
                )
                df = self._read_csv(file_path, config)

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
        return self.load_csv(file_path)

    def _read_csv_lazy(self, file_path: Path, config: dict[str, Any] | None = None) -> pl.DataFrame:
        """Читает CSV файл с использованием lazy evaluation.

        Args:
            file_path: Путь к CSV файлу.
            config: Опциональная конфигурация для чтения CSV.

        Returns:
            pl.DataFrame: Прочитанные данные.
        """
        try:
            read_kwargs = {}
            if config:
                if "separator" in config:
                    read_kwargs["separator"] = config["separator"]
                if "has_header" in config:
                    read_kwargs["has_header"] = config["has_header"]
                if "encoding" in config:
                    read_kwargs["encoding"] = config["encoding"]

            if file_path.suffix == ".gz" or file_path.name.endswith(".csv.gz"):
                logger.debug("Чтение gzipped CSV файла (lazy): %s", file_path)
                return pl.scan_csv(file_path, **read_kwargs).collect()
            else:
                logger.debug("Чтение обычного CSV файла (lazy): %s", file_path)
                return pl.scan_csv(file_path, **read_kwargs).collect()
        except Exception as e:
            logger.error("Ошибка чтения CSV файла (lazy) %s: %s", file_path, e)
            raise

    def _get_file_size_mb(self, file_path: Path) -> float:
        """Получает размер файла в мегабайтах.

        Args:
            file_path: Путь к файлу.

        Returns:
            float: Размер файла в МБ.

        Raises:
            FileNotFoundError: Если файл не найден.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.stat().st_size / (1024 * 1024)

    def _validate_file_size(self, file_path: Path, max_size_mb: float | None = None) -> float:
        """Проверяет размер файла.

        Args:
            file_path: Путь к файлу.
            max_size_mb: Максимальный размер в МБ.
                Если None, берется из конфигурации загрузчика.

        Returns:
            float: Размер файла в МБ.

        Raises:
            ValueError: Если файл слишком большой.
            FileNotFoundError: Если файл не найден.
        """
        file_size_mb = self._get_file_size_mb(file_path)

        if max_size_mb is None:
            max_size_mb = self.config.max_file_size / (1024 * 1024)

        if file_size_mb > max_size_mb:
            logger.error(
                "Файл превышает максимальный размер: %s (%.2f > %.2f MB)",
                file_path,
                file_size_mb,
                max_size_mb,
            )
            raise ValueError(
                f"File too large: {file_path.stat().st_size} bytes "
                f"(max: {int(max_size_mb * 1024 * 1024)} bytes)"
            )

        logger.info("Размер файла %s: %.2f MB", file_path, file_size_mb)
        return file_size_mb

    def _read_csv(self, file_path: Path, config: dict[str, Any] | None = None) -> pl.DataFrame:
        """Читает CSV файл (поддерживает gzip сжатие).

        Args:
            file_path: Путь к CSV файлу.
            config: Опциональная конфигурация для чтения CSV.

        Returns:
            pl.DataFrame: Прочитанные данные.
        """
        try:
            read_kwargs = {}
            if config:
                if "separator" in config:
                    read_kwargs["separator"] = config["separator"]
                if "has_header" in config:
                    read_kwargs["has_header"] = config["has_header"]

            if file_path.suffix == ".gz" or file_path.name.endswith(".csv.gz"):
                logger.debug("Чтение gzipped CSV файла: %s", file_path)
                encoding = config.get("encoding", "utf-8") if config else "utf-8"
                with gzip.open(file_path, "rt", encoding=encoding) as f:
                    return pl.read_csv(f, **read_kwargs)
            else:
                logger.debug("Чтение обычного CSV файла: %s", file_path)
                if config and "encoding" in config:
                    read_kwargs["encoding"] = config["encoding"]
                return pl.read_csv(file_path, **read_kwargs)
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
