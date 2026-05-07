"""Add updated_at to users table.

Revision ID: 20260507141843
Revises: e86f3c8f7324
Create Date: 2026-05-07 14:18:43
"""

import sqlalchemy as sa
from alembic import op

revision = "20260507141843"
down_revision = "e86f3c8f7324"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add updated_at column to users table."""
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """Remove updated_at column from users table."""
    op.drop_column("users", "updated_at")
