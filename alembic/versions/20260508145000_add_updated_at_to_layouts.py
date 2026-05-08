"""Add updated_at column to layouts table.

Revision ID: 20260508145000
Revises: a2b3c4d5e6f7
Create Date: 2026-05-08 14:50:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision: str = '20260508145000'
down_revision: str | None = 'a2b3c4d5e6f7'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add updated_at column to layouts table."""
    # Add updated_at column with default value
    op.add_column(
        "layouts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    
    # The trigger update_layouts_updated_at should now work
    # since the updated_at column exists


def downgrade() -> None:
    """Remove updated_at column from layouts table."""
    # Drop the trigger first (if exists)
    op.execute(
        "DROP TRIGGER IF EXISTS update_layouts_updated_at ON layouts"
    )
    
    # Drop the column
    op.drop_column("layouts", "updated_at")
