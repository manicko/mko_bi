"""Add missing values to processing_status enum.

This migration adds 'uploaded', 'processing', and 'completed' values
to the processing_status enum that were missing from the initial migration.

Revision ID: f3d4e5f6a7b8
Revises: e86f3c8f7324
Create Date: 2026-05-04 12:00:00.000000

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'f3d4e5f6a7b8'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'  # Changed from e86f3c8f7324 to main chain
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing values to processing_status enum."""
    # PostgreSQL 12+ supports ALTER TYPE ... ADD VALUE in transactions
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'uploaded'")
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'processing'")
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'completed'")


def downgrade() -> None:
    """Remove added enum values - requires recreating the type."""
    # PostgreSQL doesn't support removing enum values directly
    # In production, you would need to recreate the type
    # For development/testing, we can pass
    pass
