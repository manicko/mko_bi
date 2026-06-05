"""Remove unused 'success' value from processing_status ENUM.

This value was a legacy alias that is replaced by 'completed'.
No data migration needed as verified: no rows have status='success'.

Revision ID: 4479eb53fd4e
Revises: 000000000002
Create Date: 2026-06-05 16:51:30.580802
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4479eb53fd4e"
down_revision: Sequence[str] | None = "000000000002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Remove unused 'success' value from processing_status ENUM.

    PostgreSQL requires CREATE TYPE ... AS ENUM with all desired values
    to remove a value from an existing ENUM type.
    """
    # Recreate the enum type without 'success' value
    op.execute(
        """
        ALTER TYPE processing_status RENAME TO processing_status_old
        """
    )
    op.execute(
        """
        CREATE TYPE processing_status AS ENUM (
            'started',
            'uploaded',
            'processing',
            'completed',
            'failed'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE processing_logs
        ALTER COLUMN status TYPE processing_status
        USING status::text::processing_status
        """
    )
    op.execute(
        """
        DROP TYPE processing_status_old
        """
    )


def downgrade() -> None:
    """Restore 'success' value to processing_status ENUM."""
    # Recreate the enum type with 'success' value
    op.execute(
        """
        ALTER TYPE processing_status RENAME TO processing_status_old
        """
    )
    op.execute(
        """
        CREATE TYPE processing_status AS ENUM (
            'started',
            'uploaded',
            'processing',
            'success',
            'failed',
            'completed'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE processing_logs
        ALTER COLUMN status TYPE processing_status
        USING status::text::processing_status
        """
    )
    op.execute(
        """
        DROP TYPE processing_status_old
        """
    )