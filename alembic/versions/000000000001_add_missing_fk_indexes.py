"""No-op migration - indexes now created in initial migration.

Revision ID: 000000000001
Revises: 000000000000
Create Date: 2026-06-02 13:15:00.000000

This migration is now a no-op since the FK indexes are created in the
initial migration (000000000000). Kept for backward compatibility -
existing databases may have already applied the indexes via this migration.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "000000000001"
down_revision: str | Sequence[str] | None = "000000000000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Indexes are now created in initial migration - this is a no-op."""
    pass


def downgrade() -> None:
    """No-op - indexes remain in place."""
    pass