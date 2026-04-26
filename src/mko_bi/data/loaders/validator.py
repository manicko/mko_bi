"""Валидатор данных.

Этот модуль предоставляет класс для валидации структуры и типов данных,
а также проверки обязательных полей в загруженных данных.
"""

import logging

import polars as pl

from mko_bi.models.data import LoaderConfig, ValidationResult

logger = logging.getLogger(__name__)


class DataValidator:
    """Валидатор структуры и типов данных.

    Отвечает за проверку структуры данных, типов колонок,
    наличия обязательных полей и качества данных.

    Attributes:
        config: Конфигурация валидатора.
    """

    def __init__(self, config: LoaderConfig | None = None) -> None:
        """Инициализация валидатора.

        Args:
            config: Опциональная конфигурация валидатора.
        """
        self.config = config or LoaderConfig()
        logger.debug("DataValidator инициализирован с config=%s", self.config)

    def validate(self, df: pl.DataFrame) -> ValidationResult:
        """Выполняет полную валидацию DataFrame.

        Проверяет структуру данных, типы колонок, наличие
        обязательных полей и качество данных.

        Args:
            df: DataFrame для валидации.

        Returns:
            ValidationResult: Результат валидации.
        """
        logger.info("Начало валидации данных: %d строк, %d колонок", df.shape[0], df.shape[1])

        errors: list[str] = []
        warnings: list[str] = []

        # Проверка на пустой DataFrame
        if df.shape[0] == 0:
            error_msg = "DataFrame пустой (нет строк)"
            logger.error(error_msg)
            errors.append(error_msg)
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                row_count=0,
                column_count=df.shape[1],
            )

        # Проверка обязательных колонок
        missing_columns = self._validate_required_columns(df)
        errors.extend(missing_columns)

        # Проверка типов колонок
        type_errors, type_warnings = self._validate_column_types(df)
        errors.extend(type_errors)
        warnings.extend(type_warnings)

        # Проверка качества данных
        quality_warnings = self._validate_data_quality(df)
        warnings.extend(quality_warnings)

        # Проверка дубликатов
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
            logger.info("Валидация пройдена успешно")
        else:
            logger.error("Валидация завершилась с ошибками: %s", errors)

        if warnings:
            logger.warning("Валидация: %d предупреждений", len(warnings))

        return result

    def _validate_required_columns(self, df: pl.DataFrame) -> list[str]:
        """Проверяет наличие обязательных колонок.

        Args:
            df: DataFrame для проверки.

        Returns:
            list[str]: Список ошибок (пустой, если все колонки есть).
        """
        errors: list[str] = []

        if not self.config.required_columns:
            return errors

        missing_columns = [
            col for col in self.config.required_columns if col not in df.columns
        ]

        if missing_columns:
            error_msg = (
                f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}"
            )
            logger.error(error_msg)
            errors.append(error_msg)
        else:
            logger.debug("Все обязательные колонки присутствуют")

        return errors

    def _validate_column_types(
        self, df: pl.DataFrame
    ) -> tuple[list[str], list[str]]:
        """Проверяет типы колонок.

        Args:
            df: DataFrame для проверки.

        Returns:
            tuple: (ошибки, предупреждения)
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not self.config.column_types:
            return errors, warnings

        for column_name, expected_type in self.config.column_types.items():
            if column_name not in df.columns:
                continue

            actual_type = str(df[column_name].dtype)

            # Проверяем соответствие типов
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
                        f"Колонка '{column_name}': ожидался тип '{expected_type}', "
                        f"фактический тип '{actual_type}'"
                    )
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)
            else:
                warning_msg = (
                    f"Неизвестный ожидаемый тип '{expected_type}' "
                    f"для колонки '{column_name}'"
                )
                logger.warning(warning_msg)
                warnings.append(warning_msg)

        return errors, warnings

    def _validate_data_quality(self, df: pl.DataFrame) -> list[str]:
        """Проверяет качество данных.

        Args:
            df: DataFrame для проверки.

        Returns:
            list[str]: Список предупреждений о качестве данных.
        """
        warnings = []

        # Проверка null-значений в обязательных колонках
        if self.config.required_columns:
            for column in self.config.required_columns:
                if column in df.columns:
                    null_count = df[column].null_count()
                    if null_count > 0:
                        warning_msg = (
                            f"Колонка '{column}': найдено {null_count} null-значений"
                        )
                        logger.warning(warning_msg)
                        warnings.append(warning_msg)

        # Проверка пустых строк в текстовых колонках
        for column in df.columns:
            if df[column].dtype == pl.Utf8:
                empty_count = df.filter(pl.col(column) == "").shape[0]
                if empty_count > 0:
                    warning_msg = (
                        f"Колонка '{column}': найдено {empty_count} пустых строк"
                    )
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)

        return warnings

    def _validate_duplicates(self, df: pl.DataFrame) -> list[str]:
        """Проверяет наличие дубликатов.

        Args:
            df: DataFrame для проверки.

        Returns:
            list[str]: Список предупреждений о дубликатах.
        """
        warnings = []

        # Проверяем дубликаты по всем колонкам
        duplicate_count = df.shape[0] - df.unique().shape[0]

        if duplicate_count > 0:
            warning_msg = (
                f"Найдено {duplicate_count} дубликатов строк "
                f"({duplicate_count / df.shape[0] * 100:.1f}% от общего числа)"
            )
            logger.warning(warning_msg)
            warnings.append(warning_msg)

        # Проверяем дубликаты по ключевым колонкам, если они заданы
        if self.config.required_columns:
            try:
                duplicate_count_key = (
                    df.shape[0] - df.select(self.config.required_columns).unique().shape[0]
                )
                if duplicate_count_key > 0:
                    warning_msg = (
                        f"Найдено {duplicate_count_key} дубликатов "
                        f"по обязательным колонкам: {', '.join(self.config.required_columns)}"
                    )
                    logger.warning(warning_msg)
                    warnings.append(warning_msg)
            except Exception as e:
                logger.debug("Не удалось проверить дубликаты по ключевым колонкам: %s", e)

        return warnings

    def validate_schema(
        self,
        df: pl.DataFrame,
        expected_columns: list[str],
    ) -> tuple[bool, list[str]]:
        """Проверяет соответствие схемы данных ожидаемой.

        Args:
            df: DataFrame для проверки.
            expected_columns: Ожидаемые колонки.

        Returns:
            tuple: (валидно ли, список ошибок)
        """
        errors = []

        # Проверяем наличие всех ожидаемых колонок
        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            error_msg = f"Отсутствуют колонки: {', '.join(missing)}"
            errors.append(error_msg)

        # Проверяем лишние колонки (если это важно)
        if self.config.strict_schema:
            extra = [col for col in df.columns if col not in expected_columns]
            if extra:
                error_msg = f"Лишние колонки: {', '.join(extra)}"
                errors.append(error_msg)

        return len(errors) == 0, errors

    def get_validation_summary(self, result: ValidationResult) -> str:
        """Формирует текстовое описание результата валидации.

        Args:
            result: Результат валидации.

        Returns:
            str: Текстовое описание.
        """
        lines = [
            f"Результат валидации: {'ПASSED' if result.is_valid else 'FAILED'}",
            f"Строк: {result.row_count}, Колонок: {result.column_count}",
        ]

        if result.errors:
            lines.append(f"Ошибки ({len(result.errors)}):")
            for error in result.errors:
                lines.append(f"  - {error}")

        if result.warnings:
            lines.append(f"Предупреждения ({len(result.warnings)}):")
            for warning in result.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)
