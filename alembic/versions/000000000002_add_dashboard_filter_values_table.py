"""Add dashboard_filter_values table for filter UI options.

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-06-02 23:40:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000002"
down_revision: str | Sequence[str] | None = "000000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create dashboard_filter_values table with proper schema and indexes."""
    # Create dashboard_filter_values table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS dashboard_filter_values (
            id BIGSERIAL PRIMARY KEY,
            dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
            filter_name VARCHAR(255) NOT NULL,
            filter_value VARCHAR(1024) NOT NULL
        )
        """
    )

    # Create unique index to prevent duplicate filter values per dashboard
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_dashboard_filter_values ON dashboard_filter_values (dashboard_id, filter_name, filter_value)"
    )

    # Create lookup index for efficient filtering
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dashboard_filter_values_lookup ON dashboard_filter_values (dashboard_id, filter_name)"
    )


def downgrade() -> None:
    """Drop dashboard_filter_values table."""
    op.execute("DROP TABLE IF EXISTS dashboard_filter_values CASCADE")