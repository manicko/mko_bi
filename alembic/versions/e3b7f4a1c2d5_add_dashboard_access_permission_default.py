"""Add DEFAULT 'view' to dashboard_access.permission column.

The ORM model declares server_default=text("'view'") for DashboardAccess.permission,
but the initial migration created the column without a DEFAULT clause. This migration
adds the DB-level DEFAULT to match the ORM expectation and prevent NOT NULL violations
on raw SQL INSERTs without a permission value.

Revision ID: e3b7f4a1c2d5
Revises: a2153f0f6094
Create Date: 2026-05-20 11:45:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3b7f4a1c2d5"
down_revision: str | Sequence[str] | None = "a2153f0f6094"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add DEFAULT 'view' to dashboard_access.permission column."""
    op.execute(
        "ALTER TABLE dashboard_access "
        "ALTER COLUMN permission SET DEFAULT 'view'::dashboard_permission_level"
    )


def downgrade() -> None:
    """Remove DEFAULT from dashboard_access.permission column."""
    op.execute(
        "ALTER TABLE dashboard_access "
        "ALTER COLUMN permission DROP DEFAULT"
    )