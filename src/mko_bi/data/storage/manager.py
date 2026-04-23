import polars as pl
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

from mko_bi.config import DATABASE_URL


def get_db_engine():
    """Create database engine.

    Returns:
        SQLAlchemy engine
    """
    return create_engine(DATABASE_URL)


def init_db():
    """Initialize database tables."""
    engine = get_db_engine()
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS aggregates (
                id SERIAL PRIMARY KEY,
                dashboard_id INTEGER NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )
        conn.commit()


def save_aggregates(dashboard_id: int, df: pl.DataFrame) -> bool:
    """Save aggregated data to PostgreSQL.

    Args:
        dashboard_id: Dashboard ID
        df: Aggregated DataFrame

    Returns:
        True if saved successfully
    """
    engine = get_db_engine()

    # Convert DataFrame to dict for JSON storage
    data = df.to_dict(as_series=False)

    with engine.connect() as conn:
        # Create table if not exists
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS aggregates (
                id SERIAL PRIMARY KEY,
                dashboard_id INTEGER NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        # Upsert data (overwrite if exists)
        conn.execute(
            text(f"""
            INSERT INTO aggregates (dashboard_id, data)
            VALUES (:dashboard_id, :data)
            ON CONFLICT (dashboard_id) DO UPDATE SET
                data = EXCLUDED.data,
                created_at = CURRENT_TIMESTAMP
        """),
            {"dashboard_id": dashboard_id, "data": data},
        )

        conn.commit()

    return True


def get_aggregates(dashboard_id: int) -> Optional[pl.DataFrame]:
    """Retrieve aggregated data for a dashboard.

    Args:
        dashboard_id: Dashboard ID

    Returns:
        DataFrame with aggregated data, or None if not found
    """
    engine = get_db_engine()

    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT data FROM aggregates WHERE dashboard_id = :dashboard_id
            ORDER BY created_at DESC LIMIT 1
        """),
            {"dashboard_id": dashboard_id},
        ).fetchone()

        if result:
            data = result[0]
            # Convert dict back to DataFrame
            return pl.DataFrame(data)

    return None


def create_table_if_not_exists():
    """Ensure aggregates table exists."""
    init_db()
