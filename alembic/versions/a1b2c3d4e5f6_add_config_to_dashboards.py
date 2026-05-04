"""Add config column to dashboards table.

Revision ID: a1b2c3d4e5f6
Revises: 3f7a1b2c9d0e
Create Date: 2026-05-04 07:30:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = '3f7a1b2c9d0e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add config JSONB column to dashboards table if it doesn't exist."""
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='dashboards' AND column_name='config'
            ) THEN
                ALTER TABLE dashboards ADD COLUMN config JSONB NOT NULL DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Drop config column from dashboards table."""
    op.drop_column('dashboards', 'config')
