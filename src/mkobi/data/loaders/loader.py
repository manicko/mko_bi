"""CSV data loader.

This module provides a class for loading and reading CSV files,
including support for compressed .csv.gz files.
"""

import asyncio
import gzip
import logging
from pathlib import Path
from typing import Any

import polars as pl

from mkobi.config import get_config
from mkobi.models.data import LoaderConfig
from mkobi.models.enums import FileExtensionEnum

logger = logging.getLogger(__name__)


async def load_csv(filepath: Path, config: dict[str, Any] | None = None) -> pl.DataFrame:
    """Load CSV file asynchronously.

    Wrapper around synchronous CSVLoader for use in async code.
    Supports .csv and .csv.gz files with UTF-8 encoding.

    Args:
        filepath: Path to CSV file.
        config: Optional configuration for reading (separator, has_header, etc.).

    Returns:
        pl.DataFrame: Loaded data.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file cannot be read.
    """
    loader = CSVLoader()
    if config:
        loader.config = LoaderConfig(**config)
    return await asyncio.to_thread(loader.load_csv, filepath, config)


def detect_file_type(filename: str) -> FileExtensionEnum:
    """Detect file type from filename extension.

    Args:
        filename: Name of the file.

    Returns:
        File extension type as FileExtensionEnum.

    Raises:
        ValueError: If file type is not supported.
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".csv.gz"):
        logger.debug("Detected file type: %s for file: %s", FileExtensionEnum.CSV_GZ, filename)
        return FileExtensionEnum.CSV_GZ
    elif filename_lower.endswith(".csv"):
        logger.debug("Detected file type: %s for file: %s", FileExtensionEnum.CSV, filename)
        return FileExtensionEnum.CSV
    else:
        error_msg = f"Unsupported file type: {filename}"
        logger.error(error_msg)
        raise ValueError(error_msg)


class CSVLoader:
    """CSV file loader.

    Responsible for reading CSV files (including compressed .csv.gz),
    validating data structure and transforming types.
    Supports lazy loading for large files.

    Attributes:
        config: Loader configuration.
    """

    def __init__(self, config: LoaderConfig | None = None) -> None:
        """Initialize loader.

        Args:
            config: Optional loader configuration.
        """
        self.config = config or LoaderConfig()
        logger.debug("CSVLoader initialized with config=%s", self.config)

    def load_csv(
        self,
        file_path: Path,
        config: dict[str, Any] | None = None,
        lazy_threshold_mb: float | None = None,
    ) -> pl.DataFrame:
        """Load CSV file with lazy loading support for large files.

        Reads CSV file (supports .csv and .csv.gz).
        Uses lazy evaluation for files larger than lazy_threshold_mb.
        Performs file size validation.

        Args:
            file_path: Path to CSV file.
            config: Optional configuration for reading CSV (separator, has_header, encoding, etc.).
            lazy_threshold_mb: Threshold in MB for lazy loading.
                If None, uses application configuration.

        Returns:
            pl.DataFrame: Loaded data.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file is too large or cannot be read.
        """
        logger.info("Loading CSV file: %s", file_path)

        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate file size
        self._validate_file_size(file_path)

        # Determine threshold for lazy loading
        if lazy_threshold_mb is None:
            app_config = get_config()
            lazy_threshold_mb = app_config.lazy_threshold_mb

        file_size_mb = self._get_file_size_mb(file_path)

        # Read file
        try:
            if file_size_mb > lazy_threshold_mb:
                logger.info(
                    "Using lazy evaluation for file %.2f MB (threshold: %.2f MB)",
                    file_size_mb,
                    lazy_threshold_mb,
                )
                df = self._read_csv_lazy(file_path, config)
            else:
                logger.info(
                    "Using normal reading for file %.2f MB (threshold: %.2f MB)",
                    file_size_mb,
                    lazy_threshold_mb,
                )
                df = self._read_csv(file_path, config)

            logger.info(
                "File read: %d rows, %d columns",
                df.shape[0],
                df.shape[1],
            )

            # Apply type transformations
            if self.config.column_types:
                df = self._apply_type_transformations(df)

            # Check required columns
            if self.config.required_columns:
                self._validate_required_columns(df)

            return df

        except Exception as e:
            logger.error("Error loading file %s: %s", file_path, e)
            raise ValueError(f"Failed to load file {file_path}: {e}") from e

    def load(self, file_path: Path) -> pl.DataFrame:
        """Load CSV file and return DataFrame.

        Reads CSV file (supports .csv.gz), applies
        data type transformations according to configuration.

        Args:
            file_path: Path to CSV file.

        Returns:
            pl.DataFrame: Loaded data.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file cannot be read.
        """
        return self.load_csv(file_path)

    def _read_csv_lazy(self, file_path: Path, config: dict[str, Any] | None = None) -> pl.DataFrame:
        """Read CSV file using lazy evaluation.

        Args:
            file_path: Path to CSV file.
            config: Optional configuration for reading CSV.

        Returns:
            pl.DataFrame: Read data.
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
                logger.debug("Reading gzipped CSV file (lazy): %s", file_path)
                return pl.scan_csv(file_path, **read_kwargs).collect()
            else:
                logger.debug("Reading normal CSV file (lazy): %s", file_path)
                return pl.scan_csv(file_path, **read_kwargs).collect()
        except Exception as e:
            logger.error("Error reading CSV file (lazy) %s: %s", file_path, e)
            raise

    def _get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in megabytes.

        Args:
            file_path: Path to file.

        Returns:
            float: File size in MB.

        Raises:
            FileNotFoundError: If file not found.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.stat().st_size / (1024 * 1024)

    def _validate_file_size(self, file_path: Path, max_size_mb: float | None = None) -> float:
        """Validate file size.

        Args:
            file_path: Path to file.
            max_size_mb: Maximum size in MB.
                If None, uses loader configuration.

        Returns:
            float: File size in MB.

        Raises:
            ValueError: If file is too large.
            FileNotFoundError: If file not found.
        """
        file_size_mb = self._get_file_size_mb(file_path)

        if max_size_mb is None:
            max_size_mb = self.config.max_file_size / (1024 * 1024)

        if file_size_mb > max_size_mb:
            logger.error(
                "File exceeds maximum size: %s (%.2f > %.2f MB)",
                file_path,
                file_size_mb,
                max_size_mb,
            )
            raise ValueError(
                f"File too large: {file_path.stat().st_size} bytes "
                f"(max: {int(max_size_mb * 1024 * 1024)} bytes)"
            )

        logger.info("File size %s: %.2f MB", file_path, file_size_mb)
        return file_size_mb

    def _read_csv(self, file_path: Path, config: dict[str, Any] | None = None) -> pl.DataFrame:
        """Read CSV file (supports gzip compression).

        Args:
            file_path: Path to CSV file.
            config: Optional configuration for reading CSV.

        Returns:
            pl.DataFrame: Read data.
        """
        try:
            read_kwargs = {}
            if config:
                if "separator" in config:
                    read_kwargs["separator"] = config["separator"]
                if "has_header" in config:
                    read_kwargs["has_header"] = config["has_header"]

            if file_path.suffix == ".gz" or file_path.name.endswith(".csv.gz"):
                logger.debug("Reading gzipped CSV file: %s", file_path)
                encoding = config.get("encoding", "utf-8") if config else "utf-8"
                with gzip.open(file_path, "rt", encoding=encoding) as f:
                    return pl.read_csv(f, **read_kwargs)
            else:
                logger.debug("Reading normal CSV file: %s", file_path)
                if config and "encoding" in config:
                    read_kwargs["encoding"] = config["encoding"]
                return pl.read_csv(file_path, **read_kwargs)
        except Exception as e:
            logger.error("Error reading CSV file %s: %s", file_path, e)
            raise

    def _apply_type_transformations(self, df: pl.DataFrame) -> pl.DataFrame:
        """Apply column type transformations.

        Args:
            df: Source DataFrame.

        Returns:
            pl.DataFrame: DataFrame with transformed types.
        """
        logger.debug("Applying type transformations")

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
                            "Unknown data type '%s' for column '%s'",
                            target_type,
                            column_name,
                        )
                        continue

                    logger.debug(
                        "Column '%s' transformed to type '%s'",
                        column_name,
                        target_type,
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to transform column '%s' to type '%s': %s",
                        column_name,
                        target_type,
                        e,
                    )
            else:
                logger.warning(
                    "Column '%s' not found in data, skipping transformation",
                    column_name,
                )

        return df

    def _validate_required_columns(self, df: pl.DataFrame) -> None:
        """Validate presence of required columns.

        Args:
            df: DataFrame to check.

        Raises:
            ValueError: If required columns are missing.
        """
        missing_columns = [
            col for col in self.config.required_columns if col not in df.columns
        ]

        if missing_columns:
            error_msg = (
                f"Missing required columns: {', '.join(missing_columns)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("All required columns present")

    def get_summary(self, df: pl.DataFrame) -> dict[str, Any]:
        """Return summary information about DataFrame.

        Args:
            df: DataFrame to analyze.

        Returns:
            dict: Summary information about data.
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
        """Apply filters to data.

        Args:
            df: Source DataFrame.
            conditions: List of filter conditions.
                Each condition is a dict with keys:
                - column: column name
                - operator: operator (==, !=, >, <, >=, <=)
                - value: value for comparison

        Returns:
            pl.DataFrame: Filtered data.
        """
        logger.debug("Applying filters: %s", conditions)

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
                logger.warning("Unknown filter operator: %s", operator)
                continue

            logger.debug("Applied filter: %s %s %s", column, operator, value)

        return result

    def aggregate(
        self,
        df: pl.DataFrame,
        groupby: list[str],
        aggregations: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """Perform grouping and data aggregation.

        Args:
            df: Source DataFrame.
            groupby: List of columns to group by.
            aggregations: List of aggregations.
                Each aggregation is a dict with keys:
                - column: column name
                - function: aggregation function (sum, mean, count, min, max)
                - alias: optional result column name

        Returns:
            pl.DataFrame: Aggregated data.
        """
        logger.debug(
            "Aggregation: group by %s, aggregations %s",
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
                logger.warning("Unknown aggregation function: %s", function)
                continue

            agg_exprs.append(expr)

        result = df.group_by(groupby).agg(agg_exprs)
        logger.info(
            "Aggregation completed: %d groups, %d columns",
            result.shape[0],
            result.shape[1],
        )

        return result
