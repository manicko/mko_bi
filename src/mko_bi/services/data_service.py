from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from mko_bi.config import DATABASE_URL
from mko_bi.data.loaders.loader import load_csv
from mko_bi.data.processing.base import DataPipeline
from mko_bi.data.storage.manager import save_aggregates


def get_data(dashboard_id: int, filters: Optional[Dict[str, Any]] = None) -> list:
    """Get aggregated data for a dashboard with optional filters.

    Args:
        dashboard_id: Dashboard ID
        filters: Optional filters to apply

    Returns:
        List of data records
    """
    from mko_bi.db.models.dashboard import Dashboard
    from mko_bi.db.repositories.dashboard_repo import DashboardRepository

    # Get dashboard config
    dashboard = DashboardRepository.get(dashboard_id)
    if not dashboard:
        return []

    # Load and process data
    df = load_csv(dashboard.data_source)

    # Apply filters if provided
    if filters:
        for field, value in filters.items():
            df = df.filter(pl.col(field) == value)

    # Process through pipeline
    pipeline = DataPipeline()
    result_df = pipeline.run(df, dashboard.config)

    # Convert to list of dicts
    return result_df.to_dict(as_series=False)


def trigger_processing(file_path: str, dashboard_id: int) -> bool:
    """Trigger data processing for uploaded file.

    Args:
        file_path: Path to uploaded CSV file
        dashboard_id: Dashboard ID to process for

    Returns:
        True if processing successful
    """
    # Load data
    df = load_csv(file_path)

    # Process
    pipeline = DataPipeline()
    result_df = pipeline.run(df, {})

    # Save
    return save_aggregates(dashboard_id, result_df)
