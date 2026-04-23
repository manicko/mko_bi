import polars as pl
from typing import Dict, Any, List


def apply_transformations(df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
    """Apply transformations defined in configuration.

    Args:
        df: Input DataFrame
        config: Transformation configuration

    Returns:
        Transformed DataFrame
    """
    pipeline = DataPipeline()
    return pipeline.transform(df, config)


def apply_aggregations(df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
    """Apply aggregations defined in configuration.

    Args:
        df: Input DataFrame
        config: Aggregation configuration

    Returns:
        Aggregated DataFrame
    """
    pipeline = DataPipeline()
    return pipeline.aggregate(df, config)


# Registry for custom transformations
from mko_bi.data.processing.registry import register, PROCESSORS


def get_transformation(name: str):
    """Get a registered transformation by name.

    Args:
        name: Transformation name

    Returns:
        Transformation class/function
    """
    return PROCESSORS.get(name)
