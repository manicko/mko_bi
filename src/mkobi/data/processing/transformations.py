"""Data transformations and aggregations for processing pipeline.

This module provides functions to apply various
data transformations including filtering, grouping,
sorting, YoY calculation and share calculation.
"""

import logging
import re
from typing import Any, cast

import polars as pl
from pydantic import ValidationError

from mkobi.models.enums import AggregationFunctionEnum, FilterOperatorEnum
from mkobi.models.transformation_configs import TransformationConfig

logger = logging.getLogger(__name__)

# Mapping aggregation functions to Polars expressions
AGG_FUNC_MAP = {
    AggregationFunctionEnum.SUM: lambda col: pl.col(col).sum(),
    AggregationFunctionEnum.MEAN: lambda col: pl.col(col).mean(),
    AggregationFunctionEnum.COUNT: lambda col: pl.col(col).count(),
    AggregationFunctionEnum.MIN: lambda col: pl.col(col).min(),
    AggregationFunctionEnum.MAX: lambda col: pl.col(col).max(),
    AggregationFunctionEnum.MEDIAN: lambda col: pl.col(col).median(),
    AggregationFunctionEnum.STD: lambda col: pl.col(col).std(),
    AggregationFunctionEnum.VAR: lambda col: pl.col(col).var(),
    AggregationFunctionEnum.FIRST: lambda col: pl.col(col).first(),
    AggregationFunctionEnum.LAST: lambda col: pl.col(col).last(),
}


def apply_transformations(
    df: pl.DataFrame,
    config: dict[str, Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    groupby: list[str] | None = None,
    sort_by: str | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> pl.DataFrame:
    """Apply transformations to DataFrame per config.
    
    Executes filtering, grouping, sorting,
    computed field addition, column renaming
    and type casting.

    Args:
        df: Source DataFrame.
        config: Configuration dict (filters, computed_fields, rename, dtype).
        filters: List of filter conditions.
        groupby: List of columns for base grouping (no aggregations).
        sort_by: Column name to sort by.
        descending: Sort in descending order.
        limit: Limit number of rows.

    Returns:
        pl.DataFrame: Transformed DataFrame.
    """
    config = config or {}
    # Validate config structure
    try:
        TransformationConfig(**config)
    except ValidationError as e:
        logger.error("Invalid transformation config: %s", e)
        raise ValueError(f"Invalid transformation config: {e}") from None
    result = df

    # 1. Row filtering (where conditions)
    filter_list: list[Any] | None = filters if filters is not None else config.get("filters") if config else None
    if filter_list:
        logger.debug("Applying filters: %s", filter_list)
        result = _apply_filters(result, filter_list)

    # 2. Base grouping (no aggregations)
    if groupby:
        logger.debug("Grouping by: %s", groupby)
        result = result.group_by(groupby).agg(pl.all().first())

    # 3. Sorting
    if sort_by:
        logger.debug("Sorting by: %s (desc=%s)", sort_by, descending)
        result = result.sort(sort_by, descending=descending)

    # 4. Row limit
    if limit:
        logger.debug("Limiting rows: %s", limit)
        result = result.head(limit)

    # 5. Computed fields
    computed_fields = config.get("computed_fields") if config else None
    if computed_fields:
        logger.debug("Adding computed fields: %s", computed_fields)
        result = _add_computed_fields(result, cast(list[dict[str, Any]], computed_fields))

    # 6. Column renaming
    rename_map = config.get("rename")
    if rename_map:
        logger.debug("Renaming columns: %s", rename_map)
        result = result.rename(rename_map)

    # 7. Column type casting
    dtype_map = config.get("dtype") if config else None
    if dtype_map:
        logger.debug("Casting column types: %s", dtype_map)
        result = _apply_dtypes(result, cast(dict[str, str], dtype_map))

    logger.info("Transformations applied: %d rows", result.shape[0])
    return result


def _apply_filters(
    df: pl.DataFrame,
    filters: list[Any],
) -> pl.DataFrame:
    """Apply filters to DataFrame.

    Args:
        df: Source DataFrame.
        filters: List of filter conditions (FilterConfig objects or dicts with keys: column, operator, value).

    Returns:
        pl.DataFrame: Filtered DataFrame.
    """
    result = df
    for condition in filters:
        # Handle both Pydantic models and dictionaries
        if isinstance(condition, dict):
            column = condition.get("column")
            operator = condition.get("operator")
            value = condition.get("value")
        else:
            column = getattr(condition, 'column', None)
            operator = getattr(condition, 'operator', None)
            value = getattr(condition, 'value', None)

        if not column or not operator:
            continue

        # Handle operator from FilterOperatorEnum or string
        op_value = operator.value if hasattr(operator, 'value') else operator

        if op_value == FilterOperatorEnum.EQ.value:
            result = result.filter(pl.col(column) == value)
        elif op_value == FilterOperatorEnum.NE.value:
            result = result.filter(pl.col(column) != value)
        elif op_value == FilterOperatorEnum.GT.value:
            result = result.filter(pl.col(column) > value)
        elif op_value == FilterOperatorEnum.LT.value:
            result = result.filter(pl.col(column) < value)
        elif op_value == FilterOperatorEnum.GTE.value:
            result = result.filter(pl.col(column) >= value)
        elif op_value == FilterOperatorEnum.LTE.value:
            result = result.filter(pl.col(column) <= value)
        elif op_value == "in" and isinstance(value, list):
            result = result.filter(pl.col(column).is_in(value))
        else:
            logger.warning("Unknown filter operator: %s", op_value)
            continue

        logger.debug("Applied filter: %s %s %s", column, op_value, value)

    return result


def _add_computed_fields(
    df: pl.DataFrame,
    fields: list[dict[str, Any]],
) -> pl.DataFrame:
    """Add computed fields to DataFrame.

    Args:
        df: Source DataFrame.
        fields: List of dicts with keys 'name' and 'expr'.

    Returns:
        pl.DataFrame: DataFrame with added computed fields.
    """
    result = df
    for field in fields:
        name = field.get("name")
        expr_str = field.get("expr")
        if not name or not expr_str:
            continue
        try:
            expr = _parse_formula(expr_str)
            result = result.with_columns(expr.alias(name))
            logger.debug("Added computed field '%s'", name)
        except Exception as e:
            logger.error("Error in computed field '%s': %s", name, e)
            raise
    return result


def _apply_dtypes(
    df: pl.DataFrame,
    dtype_map: dict[str, str],
) -> pl.DataFrame:
    """Apply column type casting.

    Args:
        df: Source DataFrame.
        dtype_map: Dict {col_name: polars_type_string}.

    Returns:
        pl.DataFrame: DataFrame with casted types.
    """
    cast_exprs = []
    for col, dtype_str in dtype_map.items():
        try:
            dtype = getattr(pl, dtype_str.upper(), None)
            if dtype:
                cast_exprs.append(pl.col(col).cast(dtype))
            else:
                logger.warning("Unknown data type: %s", dtype_str)
        except Exception as e:
            logger.error("Type casting error for column %s: %s", col, e)

    if cast_exprs:
        return df.with_columns(cast_exprs)
    return df


def calculate_aggregations(
    df: pl.DataFrame,
    groupby: list[str] | None = None,
    aggregations: list[dict[str, Any]] | None = None,
    yoy_config: dict[str, Any] | None = None,
    share_config: dict[str, Any] | None = None,
    custom_metrics: list[dict[str, Any]] | None = None,
) -> pl.DataFrame:
    """Calculate data aggregations with YoY and share support.

    Args:
        df: Source DataFrame.
        groupby: List of columns to group by.
        aggregations: List of aggregation configs (AggregationConfig objects).
        yoy_config: Configuration for YoY calculation.
        share_config: Configuration for share calculation.
        custom_metrics: List of custom metrics.

    Returns:
        pl.DataFrame: Aggregated DataFrame.
    """
    logger.info("Starting aggregation calculation")
    result = df

    # Grouping and base aggregations
    if groupby and aggregations:
        logger.debug("Grouping by: %s", groupby)
        result = _apply_groupby_aggregations(result, groupby, aggregations)

    # YoY calculation
    if yoy_config:
        logger.debug("YoY calculation: %s", yoy_config)
        result = _calculate_yoy(result, **yoy_config)

    # Share calculation
    if share_config:
        logger.debug("Share calculation: %s", share_config)
        result = _calculate_share(result, **share_config)

    # Custom metrics
    if custom_metrics:
        logger.debug("Custom metrics: %s", custom_metrics)
        result = _add_computed_fields(result, custom_metrics)

    logger.info("Aggregations calculated: %d rows", result.shape[0])
    return result


def aggregate_data(
    df: pl.DataFrame,
    graph_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate data per graph configurations.

    Args:
        df: Source DataFrame.
        graph_configs: List of graph configuration dicts.

    Returns:
        list[dict]: List of dicts for JSONB storage.
    """
    results = []
    for config in graph_configs:
        groupby = config.get("dimensions", [])
        aggs = config.get("metrics", [])

        if not groupby or not aggs:
            continue

        aggregated = calculate_aggregations(
            df=df,
            groupby=groupby,
            aggregations=aggs,
        )
        results.extend(aggregated.to_dicts())
    return results


def _apply_groupby_aggregations(
    df: pl.DataFrame,
    groupby: list[str],
    aggregations: list[Any],
) -> pl.DataFrame:
    """Apply grouping and aggregations.

    Args:
        df: Source DataFrame.
        groupby: List of columns to group by.
        aggregations: List of aggregation configs (AggregationConfig objects or dicts).

    Returns:
        pl.DataFrame: Aggregated DataFrame.
    """
    agg_exprs = []
    for agg in aggregations:
        # Handle both Pydantic models and dictionaries
        if isinstance(agg, dict):
            column = agg.get("column")
            func_str = agg.get("function")
            alias = agg.get("alias", f"{column}_{func_str}")
        else:
            column = getattr(agg, 'column', None)
            func_str = getattr(agg, 'function', None)
            alias = getattr(agg, 'alias', None) or f"{column}_{func_str}"

        try:
            func_enum = AggregationFunctionEnum(func_str) if isinstance(func_str, str) else func_str
        except ValueError:
            logger.warning("Unknown aggregation function: %s", func_str)
            continue

        if func_enum not in AGG_FUNC_MAP:
            logger.warning("Unsupported aggregation function: %s", func_enum)
            continue

        expr = AGG_FUNC_MAP[func_enum](column).alias(alias)
        agg_exprs.append(expr)

    return df.group_by(groupby).agg(agg_exprs)


def _calculate_yoy(
    df: pl.DataFrame,
    year_column: str,
    value_column: str,
    group_cols: list[str] | None = None,
    month_column: str | None = None,
    alias: str = "yoy",
    percent_alias: str | None = None,
) -> pl.DataFrame:
    """Calculate Year-over-Year growth.

    Args:
        df: Source DataFrame.
        year_column: Column name containing year.
        value_column: Column name containing value.
        group_cols: List of grouping columns (dimensions).
        month_column: Column name containing month.
        alias: Name of resulting YoY column.

    Returns:
        pl.DataFrame: DataFrame with YoY column.
    """
    sort_cols = [year_column]
    if month_column:
        sort_cols.append(month_column)
    if group_cols:
        sort_cols.extend(group_cols)

    result = df.sort(sort_cols)

    if month_column:
        shift_group_cols = [month_column]
        if group_cols:
            shift_group_cols.extend(group_cols)

        result = result.with_columns([
            pl.col(value_column).shift(1).over(shift_group_cols).alias("__prev_value"),
            pl.col(year_column).shift(1).over(shift_group_cols).alias("__prev_year"),
        ])

        year_diff = pl.col(year_column) - pl.col("__prev_year")
        prev_value_expr = pl.when(year_diff == 1).then(pl.col("__prev_value")).otherwise(None)
    else:
        shift_lag = 1
        if group_cols:
            prev_value_expr = pl.col(value_column).shift(shift_lag).over(group_cols)
        else:
            prev_value_expr = pl.col(value_column).shift(shift_lag)

    result = result.with_columns([
        pl.when(prev_value_expr.is_null() | (prev_value_expr == 0))
        .then(None)
        .otherwise((pl.col(value_column) - prev_value_expr) / prev_value_expr * 100)
        .alias(alias)
    ])

    result = result.with_columns([pl.col(alias).fill_nan(None)])
    temp_cols = ["__prev_value", "__prev_year"]
    for col in temp_cols:
        if col in result.columns:
            result = result.drop(col)

    return result


def _calculate_share(
    df: pl.DataFrame,
    value_column: str,
    alias: str = "share",
    group_cols: list[str] | None = None,
) -> pl.DataFrame:
    """Calculate share of each value from total sum.

    Args:
        df: Source DataFrame.
        value_column: Column name containing value.
        alias: Name of resulting share column.
        group_cols: List of columns to group by.

    Returns:
        pl.DataFrame: DataFrame with share column.
    """
    if group_cols:
        total_df = df.group_by(group_cols).agg(pl.col(value_column).sum().alias("total"))
        result = df.join(total_df, on=group_cols)
        result = result.with_columns(
            pl.when(pl.col("total") == 0)
            .then(0.0)
            .otherwise(pl.col(value_column) / pl.col("total") * 100)
            .alias(alias)
        )
        result = result.drop("total")
    else:
        total = df[value_column].sum()
        if total == 0:
            result = df.with_columns(pl.lit(0.0).alias(alias))
        else:
            result = df.with_columns((pl.col(value_column) / total * 100).alias(alias))

    return result


def _parse_formula(formula: str) -> pl.Expr:
    """Parse simple formula into Polars expression.

    Args:
        formula: Formula string (e.g., "revenue / cost * 100").

    Returns:
        pl.Expr: Polars expression.
    """
    tokens = re.split(r'([+\-*/])', formula)
    tokens = [t.strip() for t in tokens if t.strip()]

    if len(tokens) == 1:
        return pl.col(tokens[0])

    expr = pl.col(tokens[0])
    i = 1
    while i < len(tokens):
        op = tokens[i]
        next_token = tokens[i + 1]

        if op == "+":
            expr = expr + pl.col(next_token)
        elif op == "-":
            expr = expr - pl.col(next_token)
        elif op == "*":
            expr = expr * pl.col(next_token)
        elif op == "/":
            expr = expr / pl.col(next_token)
        else:
            raise ValueError(f"Unknown operator in formula: {op}")
        i += 2

    return expr
