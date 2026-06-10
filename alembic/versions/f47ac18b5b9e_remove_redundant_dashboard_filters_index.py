"""Remove redundant index on dashboard_filters table.

The PRIMARY KEY constraint on (dashboard_id, filter_id) already creates
a unique index that serves all queries. The redundant non-unique
idx_dashboard_filters_dashboard_id index wastes write performance and storage.

Revision ID: f47ac18b5b9e
Revises: b749bc53b1ee
Create Date: 2026-06-10 22:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f47ac18b5b9e"
down_revision: str | Sequence[str] | None = "b749bc53b1ee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove redundant index on dashboard_filters.

    The PRIMARY KEY creates a unique index on (dashboard_id, filter_id).
    The non-unique idx_dashboard_filters_dashboard_id is redundant and
    only adds unnecessary write overhead.
    """
    op.execute("DROP INDEX IF EXISTS idx_dashboard_filters_dashboard_id")


def downgrade() -> None:
    """Recreate the redundant index for rollback compatibility.

    This recreates the index that was removed in upgrade().
    """
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dashboard_filters_dashboard_id "
        "ON dashboard_filters (dashboard_id, filter_id)"
    )