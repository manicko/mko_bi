"""Tests for data service (data_service.py) - using real test database.

Tests the business logic for file upload, processing, and status tracking.
"""

import gzip
from pathlib import Path

import pytest

from mko_bi.services.data_service import (
    _validate_file,
    _process_csv_file,
)
from mko_bi.models.data import (
    ProcessingConfig,
)


def test_valid_csv_gz_file():
    """Valid .csv.gz file should pass validation."""
    content = b"test data"
    _validate_file("data.csv.gz", content)


def test_invalid_file_type_raises_error():
    """Invalid file type should raise error."""
    content = b"test data"
    with pytest.raises(ValueError, match="Недопустимый формат файла"):
        _validate_file("data.txt", content)


def test_file_too_large_raises_error():
    """File exceeding maximum size should raise error."""
    content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
    with pytest.raises(ValueError, match="превышает максимальный размер"):
        _validate_file("data.csv.gz", content)


async def test_process_csv_file_basic(tmp_path):
    """Basic CSV file processing."""
    csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
    file_path = tmp_path / "test.csv.gz"
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
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
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        f.write(csv_content)

    config = ProcessingConfig(
        filters=[{"field": "year", "operator": ">=", "value": 2024}]
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
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        f.write(csv_content)

    config = ProcessingConfig(
        groupby=["category"],
        aggregations=[{"type": "sum", "field": "value"}]
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
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        f.write(csv_content)

    result = await _process_csv_file(file_path)

    assert result["rows"] == 2
    assert result["processed_rows"] == 2
