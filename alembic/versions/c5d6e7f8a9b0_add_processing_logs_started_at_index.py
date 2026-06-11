"""Add index on processing_logs (status, started_at) for stale log cleanup queries.

Revision ID: c5d6e7f8a9b0
Revises: f47ac18b5b9e
Create Date: 2026-06-11 20:30:39.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d6e7f8a9b0"
down_revision: str | Sequence[str] | None = "f47ac18b5b9e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composite index on processing_logs (status, started_at) for stale log cleanup."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_processing_logs_status_started_at "
        "ON processing_logs (status, started_at)"
    )


def downgrade() -> None:
    """Remove composite index added for stale log cleanup optimization."""
    op.execute("DROP INDEX IF EXISTS idx_processing_logs_status_started_at")