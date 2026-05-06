"""Tests for data service (data_service.py) - using real test database.

Tests the business logic for file upload, processing, status tracking.
"""

import gzip
from typing import Any

import pytest

from mkobi.services.data_service import (
    _process_csv_file,
    _validate_file,
    apply_filters_to_dims,
    build_filter_conditions,
    format_for_plotly,
)
from mkobi.models.data import (
    ProcessingConfig,
)
from mkobi.models.transformation_configs import (
    AggregationConfig,
    FilterConfig,
)
from mkobi.models.enums import (
    AggregationFunctionEnum,
    FilterOperatorEnum,
)


def test_valid_csv_gz_file():
    """Valid .csv.gz file should pass validation."""
    content = b"test data"
    _validate_file("data.csv.gz", content, "application/gzip")


def test_invalid_file_type_raises_error():
    """Invalid file type should raise error."""
    content = b"test data"
    # Используем валидный MIME-type, но неправильное расширение
    with pytest.raises(ValueError, match="Недопустимый формат файла"):
        _validate_file("data.txt", content, "text/csv")


def test_file_too_large_raises_error():
    """File exceeding maximum size should raise error."""
    content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
    with pytest.raises(ValueError, match="превышает максимальный размер"):
        _validate_file("data.csv.gz", content, "application/gzip")


def test_invalid_mime_type_raises_error():
    """Invalid MIME type should raise error."""
    content = b"test data"
    with pytest.raises(ValueError, match="Недопустимый MIME-type"):
        _validate_file("data.csv.gz", content, "application/pdf")


def test_valid_mime_type_text_csv():
    """Valid text/csv MIME type should pass."""
    content = b"col1,col2\n1,2\n3,4"
    _validate_file("data.csv", content, "text/csv")


async def test_process_csv_file_basic(tmp_path):
    """Basic CSV file processing."""
    csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
    file_path = tmp_path / "test.csv.gz"
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        f.write(csv_content)

    result = await _process_csv_file(file_path)

    assert "columns" in result
    assert "rows" in result
    assert result["rows"] == 3
    assert "category" in result["columns"]
    assert "value" in result["columns"]


async def test_process_csv_file_with_filters(tmp_path):
    """CSV file processing with filters."""
    csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
    file_path = tmp_path / "test.csv.gz"
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        f.write(csv_content)

    config = ProcessingConfig(
        filters=[FilterConfig(column="year", operator=FilterOperatorEnum.GTE, value=2024)]
    )

    result = await _process_csv_file(file_path, config)

    assert result["processed_rows"] == 1


async def test_process_csv_file_with_groupby(tmp_path):
    """CSV file processing with grouping."""
    csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
    file_path = tmp_path / "test.csv.gz"
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        f.write(csv_content)

    config = ProcessingConfig(
        groupby=["category"],
        aggregations=[AggregationConfig(column="value", function=AggregationFunctionEnum.SUM)]
    )

    result = await _process_csv_file(file_path, config)

    assert result["processed_rows"] > 0


async def test_process_csv_file_empty_config(tmp_path):
    """CSV file processing without config."""
    csv_content = """category,value
A,100
B,200
"""
    file_path = tmp_path / "test.csv.gz"
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        f.write(csv_content)

    result = await _process_csv_file(file_path)

    assert result["rows"] == 2
    assert result["processed_rows"] == 2


def test_format_for_plotly_bar():
    """Test formatting data for bar chart."""
    graph_config = {"type": "bar"}
    data = [
        {"dims": {"category": "A"}, "metrics": {"value": 100}},
        {"dims": {"category": "B"}, "metrics": {"value": 200}},
    ]

    result = format_for_plotly(graph_config, data)

    assert result["type"] == "bar"
    assert result["x"] == ["A", "B"]
    assert result["y"] == [100, 200]


def test_format_for_plotly_line():
    """Test formatting data for line chart."""
    graph_config = {"type": "line"}
    data = [
        {"dims": {"month": "Jan"}, "metrics": {"sales": 100}},
        {"dims": {"month": "Feb"}, "metrics": {"sales": 200}},
    ]

    result = format_for_plotly(graph_config, data)

    assert result["type"] == "scatter"
    assert result["mode"] == "lines+markers"
    assert result["x"] == ["Jan", "Feb"]
    assert result["y"] == [100, 200]


def test_format_for_plotly_pie():
    """Test formatting data for pie chart."""
    graph_config = {"type": "pie"}
    data = [
        {"dims": {"category": "A"}, "metrics": {"value": 30}},
        {"dims": {"category": "B"}, "metrics": {"value": 70}},
    ]

    result = format_for_plotly(graph_config, data)

    assert result["type"] == "pie"
    assert result["labels"] == ["A", "B"]
    assert result["values"] == [30, 70]


def test_format_for_plotly_table():
    """Test formatting data for table."""
    graph_config = {"type": "table"}
    data = [
        {"dims": {"category": "A", "year": 2023}, "metrics": {"value": 100}},
        {"dims": {"category": "B", "year": 2023}, "metrics": {"value": 200}},
    ]

    result = format_for_plotly(graph_config, data)

    assert "columns" in result
    assert "data" in result
    assert len(result["data"]) == 2


def test_format_for_plotly_unsupported_type():
    """Test formatting with unsupported graph type."""
    graph_config = {"type": "unsupported"}
    data: list[dict[str, Any]] = []

    with pytest.raises(ValueError, match="Unsupported graph type"):
        format_for_plotly(graph_config, data)


def test_apply_filters_to_dims_single_value():
    """Test filtering with single value."""
    data = [
        {"dims": {"year": 2023, "category": "A"}, "metrics": {"value": 100}},
        {"dims": {"year": 2024, "category": "A"}, "metrics": {"value": 150}},
        {"dims": {"year": 2023, "category": "B"}, "metrics": {"value": 200}},
    ]
    filters = {"year": 2023}

    result = apply_filters_to_dims(data, filters)

    assert len(result) == 2
    assert all(item["dims"]["year"] == 2023 for item in result)


def test_apply_filters_to_dims_multiple_values():
    """Test filtering with multiple values for same key."""
    data = [
        {"dims": {"category": "A"}, "metrics": {"value": 100}},
        {"dims": {"category": "B"}, "metrics": {"value": 200}},
        {"dims": {"category": "C"}, "metrics": {"value": 300}},
    ]
    filters = {"category": ["A", "B"]}

    result = apply_filters_to_dims(data, filters)

    assert len(result) == 2
    assert all(item["dims"]["category"] in ["A", "B"] for item in result)


def test_apply_filters_to_dims_multiple_filters():
    """Test filtering with multiple filter keys."""
    data = [
        {"dims": {"year": 2023, "category": "A"}, "metrics": {"value": 100}},
        {"dims": {"year": 2023, "category": "B"}, "metrics": {"value": 200}},
        {"dims": {"year": 2024, "category": "A"}, "metrics": {"value": 150}},
    ]
    filters = {"year": 2023, "category": "A"}

    result = apply_filters_to_dims(data, filters)

    assert len(result) == 1
    assert result[0]["dims"]["year"] == 2023
    assert result[0]["dims"]["category"] == "A"


def test_apply_filters_to_dims_no_filters():
    """Test filtering with empty filters."""
    data = [
        {"dims": {"category": "A"}, "metrics": {"value": 100}},
        {"dims": {"category": "B"}, "metrics": {"value": 200}},
    ]

    result = apply_filters_to_dims(data, {})

    assert len(result) == 2


def test_apply_filters_to_dims_no_match():
    """Test filtering with no matching data."""
    data = [
        {"dims": {"category": "A"}, "metrics": {"value": 100}},
    ]
    filters = {"category": "Z"}

    result = apply_filters_to_dims(data, filters)

    assert len(result) == 0


def test_build_filter_conditions_empty():
    """Test building filter conditions with empty filters."""
    conditions = build_filter_conditions({})

    assert conditions == []


def test_build_filter_conditions_single():
    """Test building filter conditions with single filter."""
    filters = {"year": "2023"}

    conditions = build_filter_conditions(filters)

    assert len(conditions) == 1


def test_build_filter_conditions_multiple():
    """Test building filter conditions with multiple filters."""
    filters = {"year": "2023", "category": "A"}

    conditions = build_filter_conditions(filters)

    assert len(conditions) == 2


def test_build_filter_conditions_list_value():
    """Test building filter conditions with list value (OR logic)."""
    filters = {"category": ["A", "B"]}

    conditions = build_filter_conditions(filters)

    assert len(conditions) == 1
