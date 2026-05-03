"""Add composite index on aggregated_data

Revision ID: 2aa835fe1fac
Revises: 57f43a5c499d
Create Date: 2026-05-03 12:04:57.517193

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2aa835fe1fac'
down_revision: str | Sequence[str] | None = '57f43a5c499d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'idx_agg_dashboard_graph',
        'aggregated_data',
        ['dashboard_id', 'graph_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_agg_dashboard_graph', table_name='aggregated_data')
