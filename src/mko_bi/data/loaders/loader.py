import polars as pl
from typing import Optional


def load_csv(path: str) -> pl.DataFrame:
    """Load a CSV file using Polars with gzip support.

    Args:
        path: Path to the CSV file (supports .gz compression)

    Returns:
        Polars DataFrame with loaded data

    Raises:
        Exception: If file cannot be loaded
    """
    try:
        df = pl.read_csv(path, compression="gzip")
        return df
    except Exception as e:
        raise Exception(f"Failed to load CSV file: {str(e)}")


def validate(df: pl.DataFrame, schema: dict) -> bool:
    """Validate DataFrame against expected schema.

    Args:
        df: DataFrame to validate
        schema: Expected schema with column names and types

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    # Check columns exist
    expected_columns = set(schema.keys())
    actual_columns = set(df.columns)

    missing_columns = expected_columns - actual_columns
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    # Check column types (basic validation)
    for col, expected_type in schema.items():
        actual_type = df[col].dtype
        # Type checking logic would go here
        # For now, just ensure column exists
        pass

    return True
