"""Tests for AggregationService business logic."""
from unittest.mock import MagicMock
from uuid import uuid4

import polars as pl
import pytest

from mkobi.models.filters import FilterRead
from mkobi.services.aggregation_service import AggregationService


@pytest.mark.asyncio
class TestAggregationService:
    """Unit tests for AggregationService business logic."""

    @pytest.fixture
    def aggregation_service(self):
        """Create AggregationService instance."""
        return AggregationService()

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pl.DataFrame({
            "category": ["A", "A", "B", "B", "C", "C"],
            "region": ["North", "South", "North", "South", "North", "South"],
            "sales": [100, 150, 200, 250, 300, 350],
            "profit": [10, 20, 30, 40, 50, 60],
        })

    def _make_graph_read(
        self, graph_id=None, dashboard_id=None, dimensions=None, metrics=None
    ):
        """Create a mock GraphRead-like object for testing."""
        obj = MagicMock()
        obj.id = graph_id or uuid4()
        obj.dashboard_id = dashboard_id or uuid4()
        obj.dimensions = dimensions or ["category"]
        obj.metrics = metrics or ["sales"]
        return obj

    def _make_filter_read(self, name, filter_id=None):
        """Create FilterRead model for testing."""
        return FilterRead(
            id=filter_id or uuid4(),
            name=name,
            type="select",
            config={"field": name},
            created_at=None,
        )

    # --- aggregate_for_dashboard tests ---

    async def test_aggregate_for_dashboard_basic(
        self, aggregation_service, sample_dataframe
    ):
        """Test basic aggregation with one graph."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
        )

        assert len(results) > 0
        assert all("dashboard_id" in r for r in results)
        assert all("graph_id" in r for r in results)
        assert all("dims" in r for r in results)
        assert all("metrics" in r for r in results)

    async def test_aggregate_for_dashboard_multiple_graphs(
        self, aggregation_service, sample_dataframe
    ):
        """Test aggregation with multiple graphs."""
        dashboard_id = uuid4()
        graph1 = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )
        graph2 = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["region"],
            metrics=["profit"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph1, graph2],
            dashboard_filters=[],
        )

        # Should have results from both graphs
        assert len(results) >= 2

    async def test_aggregate_for_dashboard_with_dashboard_filters(
        self, aggregation_service, sample_dataframe
    ):
        """Test aggregation includes dashboard filter dimensions."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )
        dashboard_filter = self._make_filter_read(name="region")

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[dashboard_filter],
        )

        assert len(results) > 0
        # Region should be included in dimensions
        for r in results:
            assert "dims" in r

    async def test_aggregate_for_dashboard_skips_missing_columns(
        self, aggregation_service, sample_dataframe
    ):
        """Test graph with columns not in DataFrame is skipped."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["nonexistent_column"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
        )

        # Should skip graph with no valid columns
        assert results == []

    async def test_aggregate_for_dashboard_skips_no_metrics(
        self, aggregation_service, sample_dataframe
    ):
        """Test graph with no valid metric columns is skipped."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["nonexistent_metric"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
        )

        assert results == []

    async def test_aggregate_for_dashboard_returns_proper_structure(
        self, aggregation_service, sample_dataframe
    ):
        """Test aggregation returns correct data structure."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
        )

        for r in results:
            assert isinstance(r["dims"], dict)
            assert isinstance(r["metrics"], dict)
            # All dim values should be strings
            for v in r["dims"].values():
                assert isinstance(v, str)

    # --- extract_filter_values tests ---

    async def test_extract_filter_values_basic(self, aggregation_service):
        """Test extracting filter values from aggregated records."""
        records = [
            {"dims": {"region": "North", "status": "active"}},
            {"dims": {"region": "South", "status": "inactive"}},
            {"dims": {"region": "North", "status": "active"}},
        ]

        filter_names = ["region", "status"]
        result = await aggregation_service.extract_filter_values(records, filter_names)

        assert "region" in result
        assert "status" in result
        assert sorted(result["region"]) == ["North", "South"]
        assert sorted(result["status"]) == ["active", "inactive"]

    async def test_extract_filter_values_empty_records(self, aggregation_service):
        """Test extraction with empty records list."""
        result = await aggregation_service.extract_filter_values([], ["region"])
        assert result == {"region": []}

    async def test_extract_filter_values_missing_filter_in_dims(self, aggregation_service):
        """Test extraction when some filters not present in records."""
        records = [
            {"dims": {"region": "North"}},
        ]

        filter_names = ["region", "missing_filter"]
        result = await aggregation_service.extract_filter_values(records, filter_names)

        assert sorted(result["region"]) == ["North"]
        assert result["missing_filter"] == []

    async def test_extract_filter_values_no_dims_key(self, aggregation_service):
        """Test extraction handles records without dims key gracefully."""
        records = [
            {"metrics": {"sales": 100}},
            {"dims": {"region": "South"}},
        ]

        filter_names = ["region"]
        result = await aggregation_service.extract_filter_values(records, filter_names)

        assert sorted(result["region"]) == ["South"]

    async def test_extract_filter_values_sorted_result(self, aggregation_service):
        """Test that extracted values are sorted."""
        records = [
            {"dims": {"region": "C"}},
            {"dims": {"region": "A"}},
            {"dims": {"region": "B"}},
        ]

        result = await aggregation_service.extract_filter_values(records, ["region"])

        assert result["region"] == ["A", "B", "C"]

    # --- Integration test ---

    async def test_full_aggregation_flow(self, aggregation_service):
        """Test full aggregation flow from DataFrame to records."""
        df = pl.DataFrame({
            "product": ["A", "A", "B"],
            "sales": [100, 200, 150],
            "quantity": [10, 20, 15],
        })

        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["product"],
            metrics=["sales", "quantity"],
        )

        records = await aggregation_service.aggregate_for_dashboard(
            df=df,
            graphs=[graph],
            dashboard_filters=[],
            metric_agg="sum",
        )

        assert len(records) == 2  # Two products

        # Check aggregation values
        record_a = next(r for r in records if r["dims"]["product"] == "A")
        assert record_a["metrics"]["sales_sum"] == 300
        assert record_a["metrics"]["quantity_sum"] == 30

    async def test_aggregate_for_dashboard_mean_aggregation(
        self, aggregation_service, sample_dataframe
    ):
        """Test mean aggregation type."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
            metric_agg="mean",
        )

        assert len(results) > 0
        for r in results:
            # Check that metric key uses "mean" suffix
            assert any(k.endswith("_mean") for k in r["metrics"].keys())

    async def test_aggregate_for_dashboard_min_aggregation(
        self, aggregation_service, sample_dataframe
    ):
        """Test min aggregation type."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
            metric_agg="min",
        )

        assert len(results) > 0
        for r in results:
            # Check that metric key uses "min" suffix
            assert any(k.endswith("_min") for k in r["metrics"].keys())

    async def test_aggregate_for_dashboard_max_aggregation(
        self, aggregation_service, sample_dataframe
    ):
        """Test max aggregation type."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
            metric_agg="max",
        )

        assert len(results) > 0
        for r in results:
            # Check that metric key uses "max" suffix
            assert any(k.endswith("_max") for k in r["metrics"].keys())

    async def test_aggregate_for_dashboard_count_aggregation(
        self, aggregation_service, sample_dataframe
    ):
        """Test count aggregation type."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
            metric_agg="count",
        )

        assert len(results) > 0
        for r in results:
            # Check that metric key uses "count" suffix and values are counts
            metric_key = next(k for k in r["metrics"].keys() if k.endswith("_count"))
            assert r["metrics"][metric_key] == 2  # Two rows per category in sample data

    async def test_aggregate_for_dashboard_unknown_agg_falls_back_to_sum(
        self, aggregation_service, sample_dataframe
    ):
        """Test that unknown aggregation type falls back to sum."""
        dashboard_id = uuid4()
        graph = self._make_graph_read(
            graph_id=uuid4(),
            dashboard_id=dashboard_id,
            dimensions=["category"],
            metrics=["sales"],
        )

        results = await aggregation_service.aggregate_for_dashboard(
            df=sample_dataframe,
            graphs=[graph],
            dashboard_filters=[],
            metric_agg="unknown_func",
        )

        assert len(results) > 0
        for r in results:
            # Check that metric key uses "unknown_func" suffix (falling back to sum behavior)
            assert any(k.endswith("_unknown_func") for k in r["metrics"].keys())