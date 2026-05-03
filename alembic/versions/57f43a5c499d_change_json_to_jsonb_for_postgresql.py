"""Change JSON to JSONB for PostgreSQL

This migration is now a no-op because the true initial migration
(5ee63ece-ea0) already creates all columns with JSONB type.

Revision ID: 57f43a5c499d
Revises: e86f3c8f7324
Create Date: 2026-05-03 09:59:40.883866

"""
from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = '57f43a5c499d'
down_revision: str | Sequence[str] | None = 'e86f3c8f7324'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op: true_initial_migration already uses JSONB."""
    pass


def downgrade() -> None:
    """No-op: handled by previous migrations."""
    pass
