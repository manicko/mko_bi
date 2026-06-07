"""Aggregation service for per-chart Polars GROUP BY operations.

Provides data aggregation logic for dashboard graphs using Polars DataFrames.
Performs GROUP BY with graph dimensions and dashboard filter dimensions.
"""

import logging
from typing import Any

import polars as pl

from mkobi.models.graph import GraphRead
from mkobi.models.filters import FilterRead

logger = logging.getLogger(__name__)


class AggregationService:
    """Service for aggregating data for dashboard graphs.

    Performs per-chart GROUP BY aggregation using Polars.
    Each unique combination of dimensions becomes one row with aggregated metrics.
    """

    def __init__(self) -> None:
        """Initialize aggregation service."""
        logger.info("AggregationService initialized")

    async def aggregate_for_dashboard(
        self,
        df: pl.DataFrame,
        graphs: list[GraphRead],
        dashboard_filters: list[FilterRead],
        metric_agg: str = "sum",
    ) -> list[dict[str, Any]]:
        """Aggregate data for each graph in dashboard.

        Args:
            df: Polars DataFrame with source data.
            graphs: List of GraphRead models for the dashboard.
            dashboard_filters: List of FilterRead models for the dashboard.
            metric_agg: Aggregation type for metrics (default: "sum").

        Returns:
            List of dicts with {dashboard_id, graph_id, dims: {all str}, metrics: {}}.
        """
        dashboard_filter_dim_names = [f.name for f in dashboard_filters]
        results: list[dict[str, Any]] = []

        for graph in graphs:
            # Collect columns for GROUP BY from graph dimensions and dashboard filters
            groupby_cols = [
                d for d in (graph.dimensions + dashboard_filter_dim_names)
                if d in df.columns
            ]

            # Collect metric columns that exist in DataFrame
            metric_cols = [m for m in graph.metrics if m in df.columns]

            # Skip graph if no valid columns
            if not groupby_cols or not metric_cols:
                logger.warning(
                    "Skipping graph %s - no valid groupby or metric columns", graph.id
                )
                continue

            # Build aggregation expressions for metrics using metric_agg parameter
            _agg_fn_map: dict[str, Any] = {
                "sum": lambda c: c.sum(),
                "mean": lambda c: c.mean(),
                "min": lambda c: c.min(),
                "max": lambda c: c.max(),
                "count": lambda c: c.count(),
            }
            agg_fn = _agg_fn_map.get(metric_agg, lambda c: c.sum())
            agg_exprs = [agg_fn(pl.col(m)).alias(f"{m}_{metric_agg}") for m in metric_cols]

            # Perform GROUP BY aggregation
            result = df.group_by(groupby_cols).agg(agg_exprs)

            # Convert each row to record dict with string dimensions
            for row in result.to_dicts():
                dims = {col: str(row[col]) for col in groupby_cols}
                metrics = {k: v for k, v in row.items() if k not in groupby_cols}
                record = {
                    "dashboard_id": graph.dashboard_id,
                    "graph_id": graph.id,
                    "dims": dims,
                    "metrics": metrics,
                }
                results.append(record)

        return results

    async def extract_filter_values(
        self,
        aggregated_records: list[dict[str, Any]],
        dashboard_filter_names: list[str],
    ) -> dict[str, list[str]]:
        """Extract distinct values for each filter dimension from aggregated records.

        Args:
            aggregated_records: List of aggregated data records.
            dashboard_filter_names: List of filter dimension names.

        Returns:
            Dict with {filter_name: [sorted unique string values]}.
        """
        # Initialize sets for each filter name
        value_sets: dict[str, set[str]] = {
            name: set() for name in dashboard_filter_names
        }

        # Collect values from each record's dims
        for record in aggregated_records:
            dims = record.get("dims", {})
            for filter_name in dashboard_filter_names:
                if filter_name in dims:
                    value_sets[filter_name].add(str(dims[filter_name]))

        # Return sorted lists
        return {
            name: sorted(list(values))
            for name, values in value_sets.items()
        }