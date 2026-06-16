"""Remove redundant index on dashboard_filters table.

The PRIMARY KEY constraint on (dashboard_id, filter_id) already creates
a unique index (dashboard_filters_pkey) that serves all queries. The
non-unique idx_dashboard_filters_dashboard_id index was created externally
(e.g., manually or via a non-versioned migration) and is redundant — it
covers the same column set as the PK and only adds unnecessary write overhead.

This migration uses DROP INDEX IF EXISTS to safely handle databases where
the index may or may not exist.

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

    Recreates idx_dashboard_filters_dashboard_id which was originally
    created externally (not via Alembic). The index is redundant with
    the PRIMARY KEY on (dashboard_id, filter_id) and is only recreated
    to support downgrade paths on databases where it previously existed.

    Note: This index is safe to leave in place if downgrade is executed
    on a database that never had it — it will simply be an unused index.
    """
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dashboard_filters_dashboard_id "
        "ON dashboard_filters (dashboard_id, filter_id)"
    )