"""Add composite index on dashboard_id, graph_id for aggregated_data.

This index supports the primary data retrieval pattern for dashboard graphs.
The individual indexes on dashboard_id and graph_id exist, but queries
filtering on both columns require a composite index for optimal performance.

Revision ID: a2153f0f6094
Revises: ffd23f1f7e2b
Create Date: 2026-05-20 10:46:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2153f0f6094"
down_revision: str | Sequence[str] | None = "ffd23f1f7e2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composite index for aggregated_data queries by dashboard and graph."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph "
        "ON aggregated_data (dashboard_id, graph_id)"
    )


def downgrade() -> None:
    """Remove composite index from aggregated_data table."""
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dashboard_graph")