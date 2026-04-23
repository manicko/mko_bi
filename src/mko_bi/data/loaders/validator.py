from typing import Optional, Dict, Any
from mko_bi.data.loaders.loader import load_csv, validate


def validate_data(path: str, schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate CSV data against schema.

    Args:
        path: Path to CSV file
        schema: Expected schema definition

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        df = load_csv(path)
        is_valid = validate(df, schema)
        return True, None
    except Exception as e:
        return False, str(e)
