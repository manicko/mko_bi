"""Change JSON to JSONB for PostgreSQL

Revision ID: 57f43a5c499d
Revises: e86f3c8f7324
Create Date: 2026-05-03 09:59:40.883866

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '57f43a5c499d'
down_revision: str | Sequence[str] | None = 'e86f3c8f7324'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alter dashboards.config from JSON to JSONB
    op.alter_column('dashboards', 'config',
                    existing_type=sa.JSON(),
                    type_=JSONB(),
                    existing_nullable=False,
                    postgresql_using='config::jsonb')

    # Alter graphs columns from JSON to JSONB
    op.alter_column('graphs', 'config',
                    existing_type=sa.JSON(),
                    type_=JSONB(),
                    existing_nullable=False,
                    postgresql_using='config::jsonb')
    op.alter_column('graphs', 'dimensions',
                    existing_type=sa.JSON(),
                    type_=JSONB(),
                    existing_nullable=False,
                    postgresql_using='dimensions::jsonb')
    op.alter_column('graphs', 'metrics',
                    existing_type=sa.JSON(),
                    type_=JSONB(),
                    existing_nullable=False,
                    postgresql_using='metrics::jsonb')

    # Alter filters.config from JSON to JSONB
    op.alter_column('filters', 'config',
                    existing_type=sa.JSON(),
                    type_=JSONB(),
                    existing_nullable=False,
                    postgresql_using='config::jsonb')

    # Alter processing_configs.settings from JSON to JSONB
    op.alter_column('processing_configs', 'settings',
                    existing_type=sa.JSON(),
                    type_=JSONB(),
                    existing_nullable=False,
                    postgresql_using='settings::jsonb')


def downgrade() -> None:
    """Downgrade schema."""
    # Revert processing_configs.settings from JSONB to JSON
    op.alter_column('processing_configs', 'settings',
                    existing_type=JSONB(),
                    type_=sa.JSON(),
                    existing_nullable=False)

    # Revert filters.config from JSONB to JSON
    op.alter_column('filters', 'config',
                    existing_type=JSONB(),
                    type_=sa.JSON(),
                    existing_nullable=False)

    # Revert graphs columns from JSONB to JSON
    op.alter_column('graphs', 'metrics',
                    existing_type=JSONB(),
                    type_=sa.JSON(),
                    existing_nullable=False)
    op.alter_column('graphs', 'dimensions',
                    existing_type=JSONB(),
                    type_=sa.JSON(),
                    existing_nullable=False)
    op.alter_column('graphs', 'config',
                    existing_type=JSONB(),
                    type_=sa.JSON(),
                    existing_nullable=False)

    # Revert dashboards.config from JSONB to JSON
    op.alter_column('dashboards', 'config',
                    existing_type=JSONB(),
                    type_=sa.JSON(),
                    existing_nullable=False)
