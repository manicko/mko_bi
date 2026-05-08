"""Fix unique constraint on aggregated_data for JSONB UPSERT support

Revision ID: a2b3c4d5e6f7
Revises: 91f5436a3098
Create Date: 2026-05-08 10:40:00

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: str | Sequence[str] | None = '91f5436a3098'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old constraint if it exists (created incorrectly on JSONB)
    op.execute(
        "ALTER TABLE aggregated_data DROP CONSTRAINT "
        "IF EXISTS uq_aggregated_data_dashboard_graph_dims"
    )

    # Drop old index if it exists
    op.execute(
        "DROP INDEX IF EXISTS uq_aggregated_data_dashboard_graph_dims"
    )

    # Create correct unique index with dims::text cast for JSONB
    # Use raw SQL since PostgreSQL requires parentheses around expressions in indexes
    op.execute(
        "CREATE UNIQUE INDEX uq_aggregated_data_dashboard_graph_dims "
        "ON aggregated_data (dashboard_id, graph_id, (dims::text))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Use IF EXISTS to handle cases where index might not exist
    op.execute("DROP INDEX IF EXISTS uq_aggregated_data_dashboard_graph_dims")
