from typing import Dict, Any, List, Optional
import polars as pl


class GlobalFilters:
    """Global filters that apply to all dashboard queries.

    Supports year, category, and brand filters.
    """

    def __init__(self):
        self.filters: Dict[str, Any] = {}

    def set_filter(self, field: str, value: Any) -> None:
        """Set a filter value.

        Args:
            field: Field name to filter on
            value: Filter value
        """
        self.filters[field] = value

    def clear_filter(self, field: str) -> None:
        """Clear a specific filter.

        Args:
            field: Field name to clear
        """
        if field in self.filters:
            del self.filters[field]

    def clear_all(self) -> None:
        """Clear all filters."""
        self.filters.clear()

    def get_filters(self) -> Dict[str, Any]:
        """Get all current filters.

        Returns:
            Dictionary of current filters
        """
        return self.filters.copy()

    def apply_to_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """Apply filters to a DataFrame.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        result = df
        for field, value in self.filters.items():
            if field in result.columns:
                result = result.filter(pl.col(field) == value)
        return result


def apply_filters(
    df: pl.DataFrame,
    year: Optional[int] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
) -> pl.DataFrame:
    """Apply global filters to DataFrame.

    Args:
        df: Input DataFrame
        year: Year filter
        category: Category filter
        brand: Brand filter

    Returns:
        Filtered DataFrame
    """
    result = df

    if year is not None:
        result = result.filter(pl.col("year") == year)

    if category is not None:
        result = result.filter(pl.col("category") == category)

    if brand is not None:
        result = result.filter(pl.col("brand") == brand)

    return result
