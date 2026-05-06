"""Tests for data processing pipeline."""

import pytest
import polars as pl
from uuid import uuid4

from mkobi.data.processing.registry import DataPipeline
from mkobi.data.processing.transformations import (
    apply_transformations,
    aggregate_data,
)
from mkobi.models.enums import UploadMode, ProcessingStatus


class TestDataPipeline:
    """Tests for DataPipeline."""

    @pytest.fixture
    def storage_manager(self):
        class MockStorageManager:
            def __init__(self):
                self.saved_data = []

            async def save_aggregates(self, dashboard_id, aggregates, clear_old=True):
                self.saved_data.append({"dashboard_id": dashboard_id, "aggregates": aggregates})
                return len(aggregates)

        return MockStorageManager()

    @pytest.fixture
    def pipeline(self, storage_manager):
        return DataPipeline(storage_manager)

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "year": [2022, 2022, 2023, 2023],
            "category": ["A", "B", "A", "B"],
            "revenue": [100, 200, 150, 250],
            "cost": [50, 80, 60, 100],
        })

    @pytest.mark.asyncio
    async def test_pipeline_run(self, pipeline, sample_df, storage_manager):
        assert pipeline is not None
        assert hasattr(pipeline, 'run')


class TestApplyTransformations:
    """Tests for apply_transformations."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "year": [2022, 2022, 2023, 2023, 2023],
            "category": ["A", "B", "A", "B", "C"],
            "revenue": [100, 200, 150, 250, 300],
            "cost": [50, 80, 60, 100, 120],
        })

    def test_apply_filters(self, sample_df):
        config = {
            "filters": [{"column": "year", "operator": "eq", "value": 2023}]
        }
        result = apply_transformations(sample_df, config)
        assert result.shape[0] == 3
        assert result["year"].unique().to_list() == [2023]

    def test_apply_computed_fields(self, sample_df):
        config = {
            "computed_fields": [{"name": "profit", "expr": "revenue - cost"}]
        }
        result = apply_transformations(sample_df, config)
        assert "profit" in result.columns

    def test_apply_rename(self, sample_df):
        config = {"rename": {"revenue": "sales"}}
        result = apply_transformations(sample_df, config)
        assert "sales" in result.columns

    def test_no_transformations(self, sample_df):
        result = apply_transformations(sample_df)
        assert result.shape == sample_df.shape


class TestAggregateData:
    """Tests for aggregate_data."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "year": [2022, 2022, 2023, 2023],
            "category": ["A", "B", "A", "B"],
            "revenue": [100, 200, 150, 250],
            "cost": [50, 80, 60, 100],
        })

    def test_aggregate_data(self, sample_df):
        graph_configs = [
            {
                "dimensions": ["year"],
                "metrics": [{"column": "revenue", "function": "sum", "alias": "total_revenue"}],
            }
        ]
        result = aggregate_data(sample_df, graph_configs)
        assert isinstance(result, list)
        assert len(result) == 2
        assert "year" in result[0]
        assert "total_revenue" in result[0]
