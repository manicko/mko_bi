"""Add force_password_change column to users table.

Adds a boolean column to support admin-initiated password resets.
When set to true, users must change their password on next login.

Revision ID: a1b2c3d4e5f6
Revises: ffd23f1f7e2b
Create Date: 2026-05-31 19:10:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "ffd23f1f7e2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add force_password_change column to users table."""
    op.add_column(
        "users",
        sa.Column(
            "force_password_change",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Remove force_password_change column from users table."""
    op.drop_column("users", "force_password_change")