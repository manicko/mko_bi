"""Data validator.

This module provides a class for validating data structure and types,
as well as checking required fields in loaded data.
"""

import logging
from typing import Any

import polars as pl

from mkobi.models.data import LoaderConfig, ValidationResult
from mkobi.models.enums import FileExtensionEnum, MimeTypeEnum

logger = logging.getLogger(__name__)


class DataValidator:
    """Validator for data structure and types.

    Responsible for checking data structure, column types,
    presence of required fields and data quality.

    Attributes:
        config: Validator configuration.
    """

    def __init__(self, config: LoaderConfig | None = None) -> None:
        """Initialize validator.

        Args:
            config: Optional validator configuration.
        """
        self.config = config or LoaderConfig()
        logger.debug("DataValidator initialized with config=%s", self.config)

    def validate(self, df: pl.DataFrame) -> ValidationResult:
        """Perform full DataFrame validation.

        Checks data structure, column types, presence
        of required fields and data quality.

        Args:
            df: DataFrame to validate.

        Returns:
            ValidationResult: Validation result.
        """
        logger.info("Starting data validation: %d rows, %d columns", df.shape[0], df.shape[1])

        errors: list[str] = []
        warnings: list[str] = []

        # Check for empty DataFrame
        if df.shape[0] == 0:
            error_msg = "DataFrame is empty (no rows)"
            logger.error(error_msg)
            errors.append(error_msg)
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                row_count=0,
                column_count=df.shape[1],
            )

        # Check required columns
        missing_columns = self._validate_required_columns(df)
        errors.extend(missing_columns)

        # Check column types
        type_errors, type_warnings = self._validate_column_types(df)
        errors.extend(type_errors)
        warnings.extend(type_warnings)

        # Check data quality
        quality_warnings = self._validate_data_quality(df)
        warnings.extend(quality_warnings)

        # Check duplicates
        duplicate_warnings = self._validate_duplicates(df)
        warnings.extend(duplicate_warnings)

        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            row_count=df.shape[0],
            column_count=df.shape[1],
            columns=df.columns,
        )

        if is_valid:
            logger.info("Validation passed successfully")
        else:
            logger.error("Validation failed with errors: %s", errors)

        if warnings:
            logger.warning("Validation: %d warnings", len(warnings))

        return result

    def _validate_required_columns(self, df: pl.DataFrame) -> list[str]:
        """Check presence of required columns.

        Args:
            df: DataFrame to check.

        Returns:
            list[str]: List of errors (empty if all columns present).
        """
        errors: list[str] = []

        if not self.config.required_columns:
            return errors

        missing_columns = [
            col for col in self.config.required_columns if col not in df.columns
        ]

        if missing_columns:
            error_msg = (
                f"Missing required columns: {', '.join(missing_columns)}"
            )
            logger.error(error_msg)
            errors.append(error_msg)
        else:
            logger.debug("All required columns present")

        return errors

    def _validate_column_types(
        self, df: pl.DataFrame
    ) -> tuple[list[str], list[str]]:
        """Check column types.

        Args:
            df: DataFrame to check.

        Returns:
            tuple: (errors, warnings)
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not self.config.column_types:
            return errors, warnings

        for column_name, expected_type in self.config.column_types.items():
            if column_name not in df.columns:
                continue

            actual_type = str(df[column_name].dtype)

            # Check type correspondence
            type_mapping = {
                "int": ["Int64", "Int32", "Int16", "Int8", "UInt64", "UInt32", "UInt16", "UInt8"],
                "float": ["Float64", "Float32"],
                "str": ["Utf8", "String"],
                "date": ["Date", "Datetime"],
                "datetime": ["Datetime"],
                "bool": ["Boolean"],
            }

            if expected_type in type_mapping:
                valid_types = type_mapping[expected_type]
                if actual_type not in valid_types:
                    warning_msg = (
                        f"Column '{column_name}': expected type '{expected_type}', "
                        f"actual type '{actual_type}'"
                    )
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)
            else:
                warning_msg = (
                    f"Unknown expected type '{expected_type}' "
                    f"for column '{column_name}'"
                )
                logger.warning(warning_msg)
                warnings.append(warning_msg)

        return errors, warnings

    def _validate_data_quality(self, df: pl.DataFrame) -> list[str]:
        """Check data quality.

        Args:
            df: DataFrame to check.

        Returns:
            list[str]: List of data quality warnings.
        """
        warnings = []

        # Check null values in required columns
        if self.config.required_columns:
            for column in self.config.required_columns:
                if column in df.columns:
                    null_count = df[column].null_count()
                    if null_count > 0:
                        warning_msg = (
                            f"Column '{column}': found {null_count} null values"
                        )
                        logger.warning(warning_msg)
                        warnings.append(warning_msg)

        # Check empty strings in text columns
        for column in df.columns:
            if df[column].dtype == pl.Utf8:
                empty_count = df.filter(pl.col(column) == "").shape[0]
                if empty_count > 0:
                    warning_msg = (
                        f"Column '{column}': found {empty_count} empty strings"
                    )
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)

        return warnings

    def _validate_duplicates(self, df: pl.DataFrame) -> list[str]:
        """Check for duplicates.

        Args:
            df: DataFrame to check.

        Returns:
            list[str]: List of duplicate warnings.
        """
        warnings = []

        # Check duplicates across all columns
        duplicate_count = df.shape[0] - df.unique().shape[0]

        if duplicate_count > 0:
            warning_msg = (
                f"Found {duplicate_count} duplicate rows "
                f"({duplicate_count / df.shape[0] * 100:.1f}% of total)"
            )
            logger.warning(warning_msg)
            warnings.append(warning_msg)

        # Check duplicates by key columns if specified
        if self.config.required_columns:
            try:
                duplicate_count_key = (
                    df.shape[0] - df.select(self.config.required_columns).unique().shape[0]
                )
                if duplicate_count_key > 0:
                    warning_msg = (
                        f"Found {duplicate_count_key} duplicates "
                        f"by required columns: {', '.join(self.config.required_columns)}"
                    )
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)
            except Exception as e:
                logger.debug("Failed to check duplicates by key columns: %s", e)

        return warnings

    def validate_schema(
        self,
        df: pl.DataFrame,
        expected_columns: list[str],
    ) -> tuple[bool, list[str]]:
        """Check if data schema matches expected.

        Args:
            df: DataFrame to check.
            expected_columns: Expected columns.

        Returns:
            tuple: (is_valid, list of errors)
        """
        errors = []

        # Check presence of all expected columns
        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            error_msg = f"Missing columns: {', '.join(missing)}"
            errors.append(error_msg)

        # Check extra columns (if important)
        if self.config.strict_schema:
            extra = [col for col in df.columns if col not in expected_columns]
            if extra:
                error_msg = f"Extra columns: {', '.join(extra)}"
                errors.append(error_msg)

        return len(errors) == 0, errors

    def get_validation_summary(self, result: ValidationResult) -> str:
        """Generate text description of validation result.

        Args:
            result: Validation result.

        Returns:
            str: Text description.
        """
        lines = [
            f"Validation result: {'PASSED' if result.is_valid else 'FAILED'}",
            f"Rows: {result.row_count}, Columns: {result.column_count}",
        ]

        if result.errors:
            lines.append(f"Errors ({len(result.errors)}):")
            for error in result.errors:
                lines.append(f"  - {error}")

        if result.warnings:
            lines.append(f"Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)


def validate_file_extension(filename: str) -> bool:
    return any(filename.endswith(ext.value) for ext in FileExtensionEnum)


def validate_mime_type(mime_type: str) -> bool:
    return mime_type in {mime.value for mime in MimeTypeEnum}


def validate_file_size(file_size: int, max_size_mb: int) -> bool:
    max_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_bytes


def validate_dataframe(df: pl.DataFrame, config: dict[str, Any]) -> list[str]:
    loader_config = LoaderConfig(**config) if config else LoaderConfig()
    validator = DataValidator(config=loader_config)
    result = validator.validate(df)
    return list(result.errors) + list(result.warnings)
