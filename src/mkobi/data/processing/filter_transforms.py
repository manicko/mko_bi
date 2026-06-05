"""Filter and computed field transformations.

This module provides functions for row filtering and computed field operations.
"""

import logging
from typing import Any

import polars as pl

from mkobi.models.enums import FilterOperatorEnum

logger = logging.getLogger(__name__)


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

        # Skip if column doesn't exist in DataFrame
        if column not in df.columns:
            logger.warning("Column %s not found in DataFrame, skipping filter", column)
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
            # Use safe parser for all expressions - no eval()
            from mkobi.data.processing.formula_parser import (
                _parse_formula,
                _parse_polars_dt_expr,
            )

            # Check if expr is a Polars datetime expression (starts with pl.col('...').dt.)
            if expr_str.strip().startswith("pl.col("):
                expr = _parse_polars_dt_expr(expr_str)
            else:
                # Parse simple arithmetic formulas
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
        # Skip if column doesn't exist
        if col not in df.columns:
            logger.warning("Column %s not found in DataFrame, skipping dtype cast", col)
            continue
        try:
            # Try case-insensitive lookup for Polars types (Int64, int64, INTEGER all work)
            dtype = getattr(pl, dtype_str.upper(), None)
            if not dtype:
                # Try capitalized form (e.g., "integer" -> "Integer")
                dtype = getattr(pl, dtype_str.capitalize(), None)
            if dtype:
                cast_exprs.append(pl.col(col).cast(dtype))
            else:
                logger.warning("Unknown data type: %s", dtype_str)
        except Exception as e:
            logger.error("Type casting error for column %s: %s", col, e)

    if cast_exprs:
        return df.with_columns(cast_exprs)
    return df