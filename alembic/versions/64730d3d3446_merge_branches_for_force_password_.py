"""merge branches for force_password_change migration

Revision ID: 64730d3d3446
Revises: bc892fa3b2ae, a1b2c3d4e5f6
Create Date: 2026-05-31 19:15:42.706300

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "64730d3d3446"
down_revision: str | Sequence[str] | None = ("bc892fa3b2ae", "a1b2c3d4e5f6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
