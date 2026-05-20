"""Rename idx_dashboard_filters_dashboard_filter to follow naming convention.

The index name idx_dashboard_filters_dashboard_filter does not follow the naming
convention of other indexes which use column names. Renamed to idx_dashboard_filters_dashboard_id
to follow the established pattern.

Revision ID: bc892fa3b2ae
Revises: e3b7f4a1c2d5
Create Date: 2026-05-20 17:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bc892fa3b2ae"
down_revision: str | Sequence[str] | None = "e3b7f4a1c2d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename index to follow naming convention."""
    op.execute(
        "ALTER INDEX IF EXISTS idx_dashboard_filters_dashboard_filter "
        "RENAME TO idx_dashboard_filters_dashboard_id"
    )


def downgrade() -> None:
    """Revert index rename."""
    op.execute(
        "ALTER INDEX IF EXISTS idx_dashboard_filters_dashboard_id "
        "RENAME TO idx_dashboard_filters_dashboard_filter"
    )