"""add unique constraint on aggregated_data (dashboard_id, graph_id, dims)

Revision ID: 91f5436a3098
Revises: f50a4054569c
Create Date: 2026-05-07 20:35:07.146278

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91f5436a3098'
down_revision: Sequence[str] | str | None = 'f50a4054569c'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create unique index for UPSERT support
    # Note: dims is JSONB, so we need to cast to text for uniqueness
    # Use raw SQL since PostgreSQL requires parentheses around expressions in indexes
    op.execute(
        "CREATE UNIQUE INDEX uq_aggregated_data_dashboard_graph_dims "
        "ON aggregated_data (dashboard_id, graph_id, (dims::text))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_aggregated_data_dashboard_graph_dims",
        table_name="aggregated_data",
    )
