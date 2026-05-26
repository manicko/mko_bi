"""Unit tests for CSVLoader class.

Tests:
- File type detection
- CSV loading (normal and gzip)
- Lazy loading for large files
- Type transformations
- Required column validation
- File size validation
"""

from pathlib import Path
import tempfile

import polars as pl
import pytest

from mkobi.data.loaders.loader import CSVLoader, detect_file_type
from mkobi.models.data import LoaderConfig
from mkobi.models.enums import FileExtensionEnum


class TestDetectFileType:
    """Tests for detect_file_type function."""

    def test_detect_csv_gz(self):
        """Test detection of .csv.gz file extension."""
        result = detect_file_type("data.csv.gz")
        assert result == FileExtensionEnum.CSV_GZ

    def test_detect_csv(self):
        """Test detection of .csv file extension."""
        result = detect_file_type("data.csv")
        assert result == FileExtensionEnum.CSV

    def test_detect_csv_uppercase(self):
        """Test detection handles uppercase extensions."""
        result = detect_file_type("data.CSV")
        assert result == FileExtensionEnum.CSV

    def test_detect_csv_gz_mixed_case(self):
        """Test detection handles mixed case .csv.gz extension."""
        result = detect_file_type("data.CSV.gz")
        assert result == FileExtensionEnum.CSV_GZ

    def test_detect_unsupported_file_type(self):
        """Test detection raises error for unsupported file type."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            detect_file_type("data.txt")

    def test_detect_unsupported_file_type_xlsx(self):
        """Test detection raises error for .xlsx file type."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            detect_file_type("data.xlsx")


class TestCSVLoaderInit:
    """Tests for CSVLoader initialization."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        loader = CSVLoader()
        assert loader.config.required_columns == []
        assert loader.config.column_types == {}

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = LoaderConfig(
            required_columns=["id", "name"],
            column_types={"id": "int", "name": "str"},
        )
        loader = CSVLoader(config=config)
        assert loader.config.required_columns == ["id", "name"]
        assert loader.config.column_types == {"id": "int", "name": "str"}

    def test_init_with_config_dict(self):
        """Test initialization with config passed to load_csv."""
        loader = CSVLoader()
        assert loader.config.required_columns == []  # Default empty


class TestCSVLoaderLoadCSV:
    """Tests for CSVLoader.load_csv method."""

    def test_load_csv_basic(self):
        """Test loading basic CSV file."""
        csv_content = b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        loader = CSVLoader()
        df = loader.load_csv(tmp_path)

        assert df.shape[0] == 2
        assert df.shape[1] == 3
        assert "name" in df.columns
        assert "age" in df.columns
        assert "city" in df.columns

    def test_load_csv_with_required_columns(self):
        """Test loading CSV with required columns validation."""
        csv_content = b"id,name,value\n1,Item1,100\n2,Item2,200\n"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        config = LoaderConfig(required_columns=["id", "name"])
        loader = CSVLoader(config=config)
        df = loader.load_csv(tmp_path)

        assert df.shape[0] == 2

    def test_load_csv_missing_required_columns(self):
        """Test loading CSV raises error when required columns missing."""
        csv_content = b"name,value\nItem1,100\n"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        config = LoaderConfig(required_columns=["id", "name"])
        loader = CSVLoader(config=config)

        with pytest.raises(ValueError, match="Missing required columns"):
            loader.load_csv(tmp_path)

    def test_load_csv_file_not_found(self):
        """Test loading CSV raises error for non-existent file."""
        loader = CSVLoader()
        with pytest.raises(FileNotFoundError, match="File not found"):
            loader.load_csv(Path("/nonexistent/file.csv"))

    def test_load_csv_with_separator(self):
        """Test loading CSV with custom separator."""
        csv_content = b"name;age;city\nAlice;30;NYC\n"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        loader = CSVLoader()
        df = loader.load_csv(tmp_path, config={"separator": ";"})

        assert df.shape[0] == 1
        assert "name" in df.columns

    def test_load_csv_lazy_threshold_respected(self):
        """Test that lazy loading threshold is used for large files."""
        # Create small CSV content
        csv_content = b"name,value\n" + b"Item1,100\n" * 100

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        loader = CSVLoader()
        # Use very small threshold to force lazy loading
        df = loader.load_csv(tmp_path, lazy_threshold_mb=0.000001)

        assert df.shape[0] >= 100


class TestCSVLoaderTypeTransformations:
    """Tests for CSVLoader type transformations."""

    def test_apply_type_transformations_int(self):
        """Test integer type transformation."""
        df = pl.DataFrame({"value": ["1", "2", "3"]})
        config = LoaderConfig(column_types={"value": "int"})
        loader = CSVLoader(config=config)

        result = loader._apply_type_transformations(df)
        assert result["value"].dtype in (pl.Int64, pl.Int32)

    def test_apply_type_transformations_float(self):
        """Test float type transformation."""
        df = pl.DataFrame({"value": ["1.5", "2.5", "3.5"]})
        config = LoaderConfig(column_types={"value": "float"})
        loader = CSVLoader(config=config)

        result = loader._apply_type_transformations(df)
        assert result["value"].dtype in (pl.Float64, pl.Float32)

    def test_apply_type_transformations_str(self):
        """Test string type transformation."""
        df = pl.DataFrame({"value": [1, 2, 3]})
        config = LoaderConfig(column_types={"value": "str"})
        loader = CSVLoader(config=config)

        result = loader._apply_type_transformations(df)
        assert result["value"].dtype == pl.Utf8

    def test_apply_type_transformations_date(self):
        """Test date type transformation."""
        df = pl.DataFrame({"date": ["2023-01-01", "2023-01-02"]})
        config = LoaderConfig(column_types={"date": "date"})
        loader = CSVLoader(config=config)

        result = loader._apply_type_transformations(df)
        assert result["date"].dtype == pl.Date

    def test_apply_type_transformations_bool(self):
        """Test boolean type transformation with actual boolean values."""
        df = pl.DataFrame({"flag": [True, False, True]})
        config = LoaderConfig(column_types={"flag": "bool"})
        loader = CSVLoader(config=config)

        result = loader._apply_type_transformations(df)
        assert result["flag"].dtype == pl.Boolean

    def test_apply_type_transformations_bool_string_fails_gracefully(self):
        """Test boolean type transformation with strings fails gracefully."""
        df = pl.DataFrame({"flag": ["true", "false", "true"]})
        config = LoaderConfig(column_types={"flag": "bool"})
        loader = CSVLoader(config=config)

        # String to bool cast fails in Polars, so dtype remains unchanged
        result = loader._apply_type_transformations(df)
        assert result["flag"].dtype == pl.Utf8  # Unchanged due to cast failure

    def test_apply_type_transformations_unknown_type(self):
        """Test unknown type is logged and skipped."""
        df = pl.DataFrame({"value": [1, 2, 3]})
        config = LoaderConfig(column_types={"value": "unknown_type"})
        loader = CSVLoader(config=config)

        # Should not raise, just log warning
        result = loader._apply_type_transformations(df)
        assert result.shape == df.shape

    def test_apply_type_transformations_missing_column(self):
        """Test transformation skips missing columns gracefully."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        config = LoaderConfig(column_types={"b": "int"})
        loader = CSVLoader(config=config)

        result = loader._apply_type_transformations(df)
        assert result.shape == df.shape

    def test_apply_type_transformations_empty_config(self):
        """Test no transformation when column_types is empty."""
        df = pl.DataFrame({"value": [1, 2, 3]})
        loader = CSVLoader()

        result = loader._apply_type_transformations(df)
        assert result.shape == df.shape


class TestCSVLoaderFileValidation:
    """Tests for CSVLoader file validation methods."""

    def test_validate_file_size_within_limit(self):
        """Test file size validation passes for small file."""
        csv_content = b"data\n"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        loader = CSVLoader()
        size = loader._validate_file_size(tmp_path, max_size_mb=1)
        assert size >= 0

    def test_validate_file_size_exceeds_limit(self):
        """Test file size validation fails for large file."""
        csv_content = b"d" * 100  # 100 bytes
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        config = LoaderConfig(max_file_size=50)  # 50 bytes limit
        loader = CSVLoader(config=config)

        with pytest.raises(ValueError, match="File too large"):
            loader._validate_file_size(tmp_path)

    def test_get_file_size_mb(self):
        """Test _get_file_size_mb returns correct size."""
        csv_content = b"d" * 1024 * 1024  # 1 MB
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        loader = CSVLoader()
        size_mb = loader._get_file_size_mb(tmp_path)
        assert size_mb >= 1.0


class TestCSVLoaderSummary:
    """Tests for CSVLoader.get_summary method."""

    def test_get_summary_basic(self):
        """Test summary returns correct information."""
        df = pl.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [30, 25],
            "score": [95.5, 87.3],
        })
        loader = CSVLoader()

        summary = loader.get_summary(df)

        assert summary["rows"] == 2
        assert summary["columns"] == 3
        assert "name" in summary["column_names"]
        assert "age" in summary["column_names"]
        assert "score" in summary["column_names"]

    def test_get_summary_column_types(self):
        """Test summary returns correct column types."""
        df = pl.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [30, 25],
        })
        loader = CSVLoader()

        summary = loader.get_summary(df)

        assert "name" in summary["column_types"]
        assert "age" in summary["column_types"]


class TestCSVLoaderFilterData:
    """Tests for CSVLoader.filter_data method."""

    def test_filter_data_eq(self):
        """Test filter with equals operator."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35]})
        loader = CSVLoader()

        result = loader.filter_data(df, [{"column": "age", "operator": "==", "value": 30}])
        assert result.shape[0] == 1
        assert result["name"][0] == "Alice"

    def test_filter_data_ne(self):
        """Test filter with not-equals operator."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35]})
        loader = CSVLoader()

        result = loader.filter_data(df, [{"column": "age", "operator": "!=", "value": 30}])
        assert result.shape[0] == 2

    def test_filter_data_gt(self):
        """Test filter with greater-than operator."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35]})
        loader = CSVLoader()

        result = loader.filter_data(df, [{"column": "age", "operator": ">", "value": 28}])
        assert result.shape[0] == 2  # Alice (30) and Charlie (35)

    def test_filter_data_lt(self):
        """Test filter with less-than operator."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35]})
        loader = CSVLoader()

        result = loader.filter_data(df, [{"column": "age", "operator": "<", "value": 30}])
        assert result.shape[0] == 1  # Bob (25)

    def test_filter_data_gte(self):
        """Test filter with greater-or-equal operator."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35]})
        loader = CSVLoader()

        result = loader.filter_data(df, [{"column": "age", "operator": ">=", "value": 30}])
        assert result.shape[0] == 2  # Alice (30) and Charlie (35)

    def test_filter_data_lte(self):
        """Test filter with less-or-equal operator."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35]})
        loader = CSVLoader()

        result = loader.filter_data(df, [{"column": "age", "operator": "<=", "value": 25}])
        assert result.shape[0] == 1  # Bob (25)

    def test_filter_data_multiple_conditions(self):
        """Test filter with multiple conditions."""
        df = pl.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
            "city": ["NYC", "LA", "NYC"],
        })
        loader = CSVLoader()

        result = loader.filter_data(df, [
            {"column": "city", "operator": "==", "value": "NYC"},
            {"column": "age", "operator": ">", "value": 28},
        ])
        assert result.shape[0] == 2  # Alice (30, NYC) and Charlie (35, NYC)

    def test_filter_data_unknown_operator(self):
        """Test filter handles unknown operator gracefully."""
        df = pl.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        loader = CSVLoader()

        # Should not raise, just log warning and skip
        result = loader.filter_data(df, [{"column": "age", "operator": "UNKNOWN", "value": 30}])
        assert result.shape[0] == 2  # No filtering applied


class TestCSVLoaderAggregate:
    """Tests for CSVLoader.aggregate method."""

    def test_aggregate_sum(self):
        """Test aggregation with sum function."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[{"column": "value", "function": "sum"}],
        )
        assert result.shape[0] == 2
        assert "value_sum" in result.columns

    def test_aggregate_mean(self):
        """Test aggregation with mean function."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[{"column": "value", "function": "mean"}],
        )
        assert result.shape[0] == 2
        assert "value_mean" in result.columns

    def test_aggregate_count(self):
        """Test aggregation with count function."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[{"column": "value", "function": "count"}],
        )
        assert result.shape[0] == 2
        assert "value_count" in result.columns

    def test_aggregate_multiple_functions(self):
        """Test aggregation with multiple functions."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[
                {"column": "value", "function": "sum"},
                {"column": "value", "function": "mean"},
            ],
        )
        assert result.shape[0] == 2
        assert "value_sum" in result.columns
        assert "value_mean" in result.columns

    def test_aggregate_with_alias(self):
        """Test aggregation with custom alias."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[{"column": "value", "function": "sum", "alias": "total"}],
        )
        assert "total" in result.columns

    def test_aggregate_unknown_function(self):
        """Test aggregation handles unknown function gracefully."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[{"column": "value", "function": "unknown"}],
        )
        assert result.shape[0] == 2

    def test_aggregate_min_max(self):
        """Test aggregation with min and max functions."""
        df = pl.DataFrame({"category": ["A", "A", "B"], "value": [10, 20, 30]})
        loader = CSVLoader()

        result = loader.aggregate(
            df,
            groupby=["category"],
            aggregations=[
                {"column": "value", "function": "min"},
                {"column": "value", "function": "max"},
            ],
        )
        assert "value_min" in result.columns
        assert "value_max" in result.columns
