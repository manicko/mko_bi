"""Unit tests for DataValidator class.

Tests:
- Schema validation
- Data quality checks
- Duplicate detection
- Required columns validation
- Column type validation
"""

import polars as pl

from mkobi.data.loaders.validator import (
    DataValidator,
    validate_dataframe,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
)
from mkobi.models.data import LoaderConfig


class TestValidateFileExtension:
    """Tests for validate_file_extension function."""

    def test_validate_csv_extension(self):
        """Test CSV extension is valid."""
        assert validate_file_extension("data.csv") is True

    def test_validate_csv_gz_extension(self):
        """Test .csv.gz extension is valid."""
        assert validate_file_extension("data.csv.gz") is True

    def test_validate_txt_extension(self):
        """Test .txt extension is invalid."""
        assert validate_file_extension("data.txt") is False

    def test_validate_xlsx_extension(self):
        """Test .xlsx extension is invalid."""
        assert validate_file_extension("data.xlsx") is False

    def test_validate_no_extension(self):
        """Test filename without extension is invalid."""
        assert validate_file_extension("datafile") is False


class TestValidateMimeType:
    """Tests for validate_mime_type function."""

    def test_validate_text_csv(self):
        """Test text/csv MIME type is valid."""
        assert validate_mime_type("text/csv") is True

    def test_validate_application_gzip(self):
        """Test application/gzip MIME type is valid."""
        assert validate_mime_type("application/gzip") is True

    def test_validate_application_x_gzip(self):
        """Test application/x-gzip MIME type is valid."""
        assert validate_mime_type("application/x-gzip") is True

    def test_validate_invalid_mime(self):
        """Test invalid MIME type returns False."""
        assert validate_mime_type("application/octet-stream") is False

    def test_validate_text_plain(self):
        """Test text/plain MIME type is invalid."""
        assert validate_mime_type("text/plain") is False


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_validate_file_size_within_limit(self):
        """Test file size within limit passes validation."""
        assert validate_file_size(1024, max_size_mb=1) is True  # 1 KB < 100 MB

    def test_validate_file_size_exceeds_limit(self):
        """Test file size exceeding limit fails validation."""
        # 101 MB in bytes
        file_size = 101 * 1024 * 1024
        assert validate_file_size(file_size, max_size_mb=100) is False

    def test_validate_file_size_exact_limit(self):
        """Test file size at exact limit passes validation."""
        file_size = 100 * 1024 * 1024
        assert validate_file_size(file_size, max_size_mb=100) is True

    def test_validate_file_size_large_limit(self):
        """Test 1GB limit works correctly."""
        file_size = 1024 * 1024 * 1024
        assert validate_file_size(file_size, max_size_mb=1024) is True


class TestValidateDataframe:
    """Tests for validate_dataframe function."""

    def test_validate_dataframe_valid(self):
        """Test valid dataframe returns no errors/warnings."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "value": [10.0, 20.0, 30.0],
        })
        errors = validate_dataframe(df, {})
        assert errors == []

    def test_validate_dataframe_with_config(self):
        """Test validation with loader config."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        })
        config = {"required_columns": ["id"]}
        errors = validate_dataframe(df, config)
        assert errors == []

    def test_validate_dataframe_empty(self):
        """Test empty dataframe returns errors."""
        df = pl.DataFrame({"id": [], "name": []}).cast({"id": pl.Int64, "name": pl.Utf8})
        errors = validate_dataframe(df, {})
        assert any("empty" in err.lower() for err in errors)


class TestDataValidatorInit:
    """Tests for DataValidator initialization."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        validator = DataValidator()
        assert validator.config.required_columns == []
        assert validator.config.column_types == {}

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = LoaderConfig(
            required_columns=["id", "name"],
            column_types={"id": "int"},
        )
        validator = DataValidator(config=config)
        assert validator.config.required_columns == ["id", "name"]


class TestDataValidatorValidate:
    """Tests for DataValidator.validate method."""

    def test_validate_success(self):
        """Test successful validation."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        })
        validator = DataValidator()
        result = validator.validate(df)

        assert result.is_valid is True
        assert result.errors == []
        assert result.row_count == 3
        assert result.column_count == 2

    def test_validate_empty_dataframe(self):
        """Test validation fails for empty DataFrame."""
        df = pl.DataFrame(schema={"id": pl.Int64, "name": pl.Utf8})
        validator = DataValidator()
        result = validator.validate(df)

        assert result.is_valid is False
        assert any("empty" in err.lower() for err in result.errors)

    def test_validate_missing_required_columns(self):
        """Test validation fails for missing required columns."""
        df = pl.DataFrame({"name": ["A", "B", "C"]})
        config = LoaderConfig(required_columns=["id", "name"])
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert result.is_valid is False
        assert any("Missing required columns" in err for err in result.errors)

    def test_validate_all_required_columns_present(self):
        """Test validation passes when all required columns present."""
        df = pl.DataFrame({"id": [1, 2], "name": ["A", "B"]})
        config = LoaderConfig(required_columns=["id", "name"])
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert result.is_valid is True

    def test_validate_column_type_warning(self):
        """Test validation warns on type mismatch."""
        df = pl.DataFrame({"value": ["string_value"]})  # String instead of int
        config = LoaderConfig(column_types={"value": "int"})
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert result.is_valid is True  # Warning, not error
        assert len(result.warnings) > 0

    def test_validate_null_values_warning(self):
        """Test validation warns on null values in required columns."""
        df = pl.DataFrame({
            "id": [1, None, 3],
            "name": ["A", "B", "C"],
        })
        config = LoaderConfig(required_columns=["id", "name"])
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert len(result.warnings) > 0
        assert any("null values" in w for w in result.warnings)

    def test_validate_empty_strings_warning(self):
        """Test validation warns on empty strings in text columns."""
        df = pl.DataFrame({
            "name": ["A", "", "C"],
            "value": [1, 2, 3],
        })
        validator = DataValidator()
        result = validator.validate(df)

        assert len(result.warnings) > 0
        assert any("empty strings" in w for w in result.warnings)


class TestDataValidatorDuplicates:
    """Tests for duplicate detection in DataValidator."""

    def test_validate_no_duplicates(self):
        """Test validation passes for data without duplicates."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        })
        validator = DataValidator()
        result = validator.validate(df)

        # Check no duplicate warnings (filter for duplicates specifically)
        duplicate_warnings = [w for w in result.warnings if "duplicate" in w.lower()]
        assert duplicate_warnings == []

    def test_validate_has_duplicates(self):
        """Test validation warns on duplicate rows."""
        df = pl.DataFrame({
            "id": [1, 1, 2],
            "name": ["A", "A", "B"],
        })
        validator = DataValidator()
        result = validator.validate(df)

        assert any("duplicate" in w.lower() for w in result.warnings)

    def test_validate_duplicates_by_required_columns(self):
        """Test validation warns on duplicates by required columns."""
        df = pl.DataFrame({
            "id": [1, 1, 2],
            "name": ["A", "B", "C"],  # Different values for same id
        })
        config = LoaderConfig(required_columns=["id"])
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert any("duplicate" in w.lower() for w in result.warnings)


class TestDataValidatorSchema:
    """Tests for DataValidator.validate_schema method."""

    def test_validate_schema_all_columns_present(self):
        """Test schema validation passes when all columns present."""
        df = pl.DataFrame({"id": [1, 2], "name": ["A", "B"], "value": [10, 20]})
        validator = DataValidator()
        is_valid, errors = validator.validate_schema(df, ["id", "name", "value"])

        assert is_valid is True
        assert errors == []

    def test_validate_schema_missing_columns(self):
        """Test schema validation fails for missing columns."""
        df = pl.DataFrame({"id": [1, 2], "name": ["A", "B"]})
        validator = DataValidator()
        is_valid, errors = validator.validate_schema(df, ["id", "name", "value"])

        assert is_valid is False
        assert any("Missing columns" in e for e in errors)

    def test_validate_schema_extra_columns_strict(self):
        """Test schema validation fails with extra columns when strict."""
        df = pl.DataFrame({"id": [1, 2], "name": ["A", "B"], "extra": ["x", "y"]})
        config = LoaderConfig(strict_schema=True)
        validator = DataValidator(config=config)
        is_valid, errors = validator.validate_schema(df, ["id", "name"])

        assert is_valid is False
        assert any("Extra columns" in e for e in errors)

    def test_validate_schema_extra_columns_not_strict(self):
        """Test schema validation passes with extra columns when not strict."""
        df = pl.DataFrame({"id": [1, 2], "name": ["A", "B"], "extra": ["x", "y"]})
        validator = DataValidator()
        is_valid, errors = validator.validate_schema(df, ["id", "name"])

        assert is_valid is True
        assert errors == []


class TestDataValidatorSummary:
    """Tests for DataValidator.get_validation_summary method."""

    def test_get_validation_summary_passed(self):
        """Test summary for passed validation."""
        df = pl.DataFrame({"id": [1, 2]})
        validator = DataValidator()
        result = validator.validate(df)
        summary = validator.get_validation_summary(result)

        assert "PASSED" in summary
        assert "Rows: 2" in summary

    def test_get_validation_summary_failed(self):
        """Test summary for failed validation."""
        df = pl.DataFrame(schema={"id": pl.Int64})
        validator = DataValidator()
        result = validator.validate(df)
        summary = validator.get_validation_summary(result)

        assert "FAILED" in summary

    def test_get_validation_summary_with_warnings(self):
        """Test summary includes warnings."""
        df = pl.DataFrame({"name": ["A", ""]})
        validator = DataValidator()
        result = validator.validate(df)
        summary = validator.get_validation_summary(result)

        if result.warnings:
            assert "Warnings" in summary

    def test_get_validation_summary_with_errors(self):
        """Test summary includes errors."""
        df = pl.DataFrame(schema={"id": pl.Int64})
        validator = DataValidator()
        result = validator.validate(df)
        summary = validator.get_validation_summary(result)

        if result.errors:
            assert "Errors" in summary


class TestDataValidatorColumnTypes:
    """Tests for column type validation in DataValidator."""

    def test_validate_int_column_accepted_types(self):
        """Test int column accepts various int types."""
        df = pl.DataFrame({"value": [1, 2, 3]}).cast({"value": pl.Int32})
        config = LoaderConfig(column_types={"value": "int"})
        validator = DataValidator(config=config)
        result = validator.validate(df)

        # Int32 should be accepted for int type
        int_warnings = [w for w in result.warnings if "expected type 'int'" in w]
        assert int_warnings == []

    def test_validate_float_column(self):
        """Test float column accepts Float64/Float32."""
        df = pl.DataFrame({"value": [1.5, 2.5]}).cast({"value": pl.Float32})
        config = LoaderConfig(column_types={"value": "float"})
        validator = DataValidator(config=config)
        result = validator.validate(df)

        float_warnings = [w for w in result.warnings if "expected type 'float'" in w]
        assert float_warnings == []

    def test_validate_datetime_column(self):
        """Test datetime column accepts Datetime type."""
        df = pl.DataFrame({
            "dt": pl.datetime_range(
                pl.datetime(2023, 1, 1, 12, 0, 0),
                pl.datetime(2023, 1, 1, 12, 0, 0),
                interval="1d",
                eager=True,
            ).cast(pl.Datetime),
        })
        config = LoaderConfig(column_types={"dt": "datetime"})
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert result.is_valid is True

    def test_validate_bool_column(self):
        """Test boolean column accepts Boolean type."""
        df = pl.DataFrame({"flag": [True, False]}).cast({"flag": pl.Boolean})
        config = LoaderConfig(column_types={"flag": "bool"})
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert result.is_valid is True

    def test_validate_unknown_expected_type(self):
        """Test unknown expected type generates warning."""
        df = pl.DataFrame({"value": [1, 2, 3]})
        config = LoaderConfig(column_types={"value": "unknown_type"})
        validator = DataValidator(config=config)
        result = validator.validate(df)

        assert any("Unknown expected type" in w for w in result.warnings)