"""Schema adjustments migration

This migration adjusts the schema after the true initial migration.
It should be applied after 5ee63ece-ea0_true_initial_migration.

Revision ID: e86f3c8f7324
Revises: 7130ecb0388c
Create Date: 2026-05-01 21:27:22.548960

"""
from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = 'e86f3c8f7324'
down_revision: str | Sequence[str] | None = '7130ecb0388c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op: true_initial_migration already creates everything correctly."""
    pass


def downgrade() -> None:
    """No-op: downgrade handled by true_initial_migration."""
    pass
