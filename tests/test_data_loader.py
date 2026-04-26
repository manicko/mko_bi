"""Тесты для загрузчика и валидатора CSV данных.

Тестирует классы CSVLoader и DataValidator для загрузки,
чтения и валидации CSV файлов.
"""

import csv
import gzip
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from mko_bi.data.loaders.loader import CSVLoader
from mko_bi.data.loaders.validator import DataValidator
from mko_bi.models.data import LoaderConfig, ValidationResult


class TestCSVLoader:
    """Тесты для класса CSVLoader."""

    @pytest.fixture
    def sample_csv_content(self):
        """Создает пример CSV содержимого."""
        return "date,category,revenue\n2023-01-01,A,100.5\n2023-01-02,B,200.0\n"

    @pytest.fixture
    def sample_csv_file(self, sample_csv_content):
        """Создает временный CSV файл."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    @pytest.fixture
    def sample_gz_file(self, sample_csv_content):
        """Создает временный сжатый CSV файл."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv.gz', delete=False) as f:
            with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                gz.write(sample_csv_content.encode('utf-8'))
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    @pytest.fixture
    def default_config(self):
        """Создает конфигурацию по умолчанию."""
        return LoaderConfig(
            required_columns=["date", "category", "revenue"],
            column_types={
                "date": "date",
                "revenue": "float",
                "category": "str",
            },
        )

    def test_init_with_default_config(self):
        """Тест инициализации с конфигурацией по умолчанию."""
        loader = CSVLoader()
        assert loader.config is not None
        assert loader.config.required_columns == []
        assert loader.config.column_types == {}

    def test_init_with_custom_config(self, default_config):
        """Тест инициализации с кастомной конфигурацией."""
        loader = CSVLoader(default_config)
        assert loader.config == default_config

    def test_load_csv_file(self, sample_csv_file, default_config):
        """Тест загрузки обычного CSV файла."""
        loader = CSVLoader(default_config)
        df = loader.load(sample_csv_file)

        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 2
        assert df.shape[1] == 3
        assert list(df.columns) == ["date", "category", "revenue"]

    def test_load_gzipped_csv_file(self, sample_gz_file, default_config):
        """Тест загрузки сжатого CSV файла."""
        loader = CSVLoader(default_config)
        df = loader.load(sample_gz_file)

        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 2
        assert df.shape[1] == 3

    def test_load_nonexistent_file(self, default_config):
        """Тест загрузки несуществующего файла."""
        loader = CSVLoader(default_config)
        with pytest.raises(FileNotFoundError):
            loader.load(Path("/nonexistent/file.csv"))

    def test_load_invalid_csv(self, default_config):
        """Тест загрузки некорректного CSV файла."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,content\n")
            temp_path = Path(f.name)

        try:
            loader = CSVLoader(default_config)
            # Файл не должен загрузиться из-за отсутствия обязательных колонок
            with pytest.raises(ValueError, match="Отсутствуют обязательные колонки"):
                loader.load(temp_path)
        finally:
            temp_path.unlink()

    def test_apply_type_transformations(self, sample_csv_file):
        """Тест преобразования типов данных."""
        config = LoaderConfig(
            column_types={
                "revenue": "float",
                "category": "str",
            },
        )
        loader = CSVLoader(config)
        df = loader.load(sample_csv_file)

        # Проверяем, что типы преобразованы
        assert str(df["revenue"].dtype) in ["Float64", "Float32"]
        assert str(df["category"].dtype) in ["Utf8", "String"]

    def test_validate_required_columns_success(self, sample_csv_file, default_config):
        """Тест успешной проверки обязательных колонок."""
        loader = CSVLoader(default_config)
        df = loader.load(sample_csv_file)

        # Не должно выбрасывать исключение
        loader._validate_required_columns(df)

    def test_validate_required_columns_failure(self, sample_csv_file):
        """Тест проверки обязательных колонок с ошибкой."""
        config = LoaderConfig(
            required_columns=["date", "category", "revenue", "nonexistent"],
        )
        loader = CSVLoader(config)
        df = pl.read_csv(sample_csv_file)

        with pytest.raises(ValueError, match="Отсутствуют обязательные колонки"):
            loader._validate_required_columns(df)

    def test_get_summary(self, sample_csv_file, default_config):
        """Тест получения сводной информации."""
        loader = CSVLoader(default_config)
        df = loader.load(sample_csv_file)

        summary = loader.get_summary(df)

        assert summary["rows"] == 2
        assert summary["columns"] == 3
        assert "date" in summary["column_names"]
        assert summary["memory_usage"] > 0

    def test_filter_data(self, sample_csv_file, default_config):
        """Тест фильтрации данных."""
        loader = CSVLoader(default_config)
        df = loader.load(sample_csv_file)

        conditions = [
            {"column": "category", "operator": "==", "value": "A"},
        ]
        filtered = loader.filter_data(df, conditions)

        assert filtered.shape[0] == 1
        assert filtered["category"][0] == "A"

    def test_aggregate_data(self, sample_csv_file, default_config):
        """Тест агрегации данных."""
        loader = CSVLoader(default_config)
        df = loader.load(sample_csv_file)

        aggregations = [
            {"column": "revenue", "function": "sum", "alias": "total_revenue"},
        ]
        result = loader.aggregate(df, ["category"], aggregations)

        assert "category" in result.columns
        assert "total_revenue" in result.columns
        assert result.shape[0] == 2  # Две категории: A и B


class TestDataValidator:
    """Тесты для класса DataValidator."""

    @pytest.fixture
    def valid_dataframe(self):
        """Создает валидный DataFrame."""
        return pl.DataFrame({
            "date": ["2023-01-01", "2023-01-02"],
            "category": ["A", "B"],
            "revenue": [100.5, 200.0],
        })

    @pytest.fixture
    def default_config(self):
        """Создает конфигурацию по умолчанию."""
        return LoaderConfig(
            required_columns=["date", "category", "revenue"],
            column_types={
                "date": "str",
                "revenue": "float",
                "category": "str",
            },
        )

    def test_init_with_default_config(self):
        """Тест инициализации с конфигурацией по умолчанию."""
        validator = DataValidator()
        assert validator.config is not None

    def test_init_with_custom_config(self, default_config):
        """Тест инициализации с кастомной конфигурацией."""
        validator = DataValidator(default_config)
        assert validator.config == default_config

    def test_validate_success(self, valid_dataframe, default_config):
        """Тест успешной валидации."""
        validator = DataValidator(default_config)
        result = validator.validate(valid_dataframe)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.errors == []
        assert result.row_count == 2
        assert result.column_count == 3

    def test_validate_missing_required_columns(self, default_config):
        """Тест валидации с отсутствующими обязательными колонками."""
        validator = DataValidator(default_config)
        df = pl.DataFrame({
            "date": ["2023-01-01"],
            "category": ["A"],
            # Отсутствует колонка 'revenue'
        })

        result = validator.validate(df)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("revenue" in error for error in result.errors)

    def test_validate_empty_dataframe(self, default_config):
        """Тест валидации пустого DataFrame."""
        validator = DataValidator(default_config)
        df = pl.DataFrame()

        result = validator.validate(df)

        assert result.is_valid is False
        assert result.row_count == 0
        assert len(result.errors) > 0

    def test_validate_with_null_values(self, default_config):
        """Тест валидации с null-значениями."""
        validator = DataValidator(default_config)
        df = pl.DataFrame({
            "date": ["2023-01-01", None],
            "category": ["A", "B"],
            "revenue": [100.5, None],
        })

        result = validator.validate(df)

        assert result.is_valid is True  # null-значения - это предупреждения, а не ошибки
        assert len(result.warnings) > 0
        assert any("null" in warning.lower() for warning in result.warnings)

    def test_validate_column_types(self, default_config):
        """Тест проверки типов колонок."""
        validator = DataValidator(default_config)
        df = pl.DataFrame({
            "date": ["2023-01-01", "2023-01-02"],
            "category": ["A", "B"],
            "revenue": ["100.5", "200.0"],  # Строки вместо чисел
        })

        result = validator.validate(df)

        # Должны быть предупреждения о несоответствии типов
        assert any("тип" in warning.lower() for warning in result.warnings)

    def test_validate_duplicates(self, default_config):
        """Тест проверки дубликатов."""
        validator = DataValidator(default_config)
        df = pl.DataFrame({
            "date": ["2023-01-01", "2023-01-01"],
            "category": ["A", "A"],
            "revenue": [100.5, 100.5],
        })

        result = validator.validate(df)

        # Должны быть предупреждения о дубликатах
        assert any("дубликат" in warning.lower() for warning in result.warnings)

    def test_validate_schema_success(self, valid_dataframe):
        """Тест успешной проверки схемы."""
        validator = DataValidator()
        expected_columns = ["date", "category", "revenue"]

        is_valid, errors = validator.validate_schema(valid_dataframe, expected_columns)

        assert is_valid is True
        assert errors == []

    def test_validate_schema_failure(self, valid_dataframe):
        """Тест неуспешной проверки схемы."""
        validator = DataValidator()
        expected_columns = ["date", "category", "revenue", "nonexistent"]

        is_valid, errors = validator.validate_schema(valid_dataframe, expected_columns)

        assert is_valid is False
        assert len(errors) > 0
        assert any("nonexistent" in error for error in errors)

    def test_get_validation_summary(self, valid_dataframe, default_config):
        """Тест получения текстового описания результата валидации."""
        validator = DataValidator(default_config)
        result = validator.validate(valid_dataframe)

        summary = validator.get_validation_summary(result)

        assert "Результат валидации" in summary
        assert "ПASSED" in summary
        assert "Строк: 2" in summary

    def test_validation_result_model(self):
        """Тест модели ValidationResult."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Тестовое предупреждение"],
            row_count=100,
            column_count=5,
            columns=["col1", "col2", "col3", "col4", "col5"],
        )

        assert result.is_valid is True
        assert result.row_count == 100
        assert result.column_count == 5
        assert len(result.warnings) == 1

    def test_loader_config_model(self):
        """Тест модели LoaderConfig."""
        config = LoaderConfig(
            required_columns=["date", "value"],
            column_types={"date": "date", "value": "float"},
            strict_schema=True,
            max_file_size=50 * 1024 * 1024,
        )

        assert config.required_columns == ["date", "value"]
        assert config.column_types == {"date": "date", "value": "float"}
        assert config.strict_schema is True
        assert config.max_file_size == 50 * 1024 * 1024


class TestIntegration:
    """Интеграционные тесты."""



    def test_load_gzipped_and_validate(self):
        """Тест загрузки сжатого файла и валидации."""
        # Создаем тестовый сжатый CSV файл
        csv_content = "date,category,revenue\n2023-01-01,A,100.5\n2023-01-02,B,200.0\n"

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv.gz', delete=False) as f:
            with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                gz.write(csv_content.encode('utf-8'))
            temp_path = Path(f.name)

        try:
            # Настройка
            config = LoaderConfig(
                required_columns=["date", "category", "revenue"],
                column_types={
                    "revenue": "float",
                    "category": "str",
                },
            )

            # Загрузка
            loader = CSVLoader(config)
            df = loader.load(temp_path)

            # Валидация
            validator = DataValidator(config)
            result = validator.validate(df)

            # Проверки
            assert result.is_valid is True
            assert result.row_count == 2

        finally:
            temp_path.unlink()

    def test_filter_and_aggregate_flow(self):
        """Тест фильтрации и агрегации данных."""
        # Создаем тестовые данные
        df = pl.DataFrame({
            "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            "category": ["A", "B", "A", "B"],
            "revenue": [100.0, 200.0, 150.0, 250.0],
        })

        config = LoaderConfig()
        loader = CSVLoader(config)

        # Фильтрация
        filtered = loader.filter_data(df, [{"column": "category", "operator": "==", "value": "A"}])
        assert filtered.shape[0] == 2

        # Агрегация
        aggregated = loader.aggregate(
            filtered,
            ["category"],
            [{"column": "revenue", "function": "sum", "alias": "total"}]
        )

        assert aggregated.shape[0] == 1
        assert aggregated["total"][0] == 250.0
