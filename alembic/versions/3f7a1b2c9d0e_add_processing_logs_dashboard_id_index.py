"""Add index on processing_logs.dashboard_id

Revision ID: 3f7a1b2c9d0e
Revises: e86f3c8f7324
Create Date: 2026-05-03 17:30:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3f7a1b2c9d0e'
down_revision: str | Sequence[str] | None = '840a99edb818'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add index on processing_logs.dashboard_id."""
    op.create_index(
        'idx_processing_logs_dashboard_id',
        'processing_logs',
        ['dashboard_id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop index on processing_logs.dashboard_id."""
    op.drop_index(
        'idx_processing_logs_dashboard_id',
        table_name='processing_logs',
    )
