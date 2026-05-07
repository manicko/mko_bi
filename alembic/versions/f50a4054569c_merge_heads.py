"""Merge heads

Revision ID: f50a4054569c
Revises: 20260507141843, a1e404502aac
Create Date: 2026-05-07 14:20:56.899717

"""
from collections.abc import Sequence



# revision identifiers, used by Alembic.
revision: str = 'f50a4054569c'
down_revision: str | Sequence[str] | None = ('20260507141843', 'a1e404502aac')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
