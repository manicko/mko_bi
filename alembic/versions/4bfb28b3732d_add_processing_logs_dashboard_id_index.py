"""add_processing_logs_dashboard_id_index

Revision ID: 4bfb28b3732d
Revises: c3cc391beded
Create Date: 2026-05-08 22:23:25.375246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bfb28b3732d'
down_revision: Union[str, Sequence[str], None] = 'c3cc391beded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename unique constraint using DO block for idempotency
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_graph_dashboard_name') THEN
                ALTER TABLE graphs RENAME CONSTRAINT uq_graph_dashboard_name TO idx_graphs_dashboard_name;
            END IF;
        END $$;
    """)

    # Create index on processing_logs.dashboard_id if not exists
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_processing_logs_dashboard_id' AND relkind = 'i') THEN
                CREATE INDEX idx_processing_logs_dashboard_id ON processing_logs(dashboard_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index if exists
    op.execute("DROP INDEX IF EXISTS idx_processing_logs_dashboard_id")

    # Rename constraint back using DO block for idempotency
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'idx_graphs_dashboard_name') THEN
                ALTER TABLE graphs RENAME CONSTRAINT idx_graphs_dashboard_name TO uq_graph_dashboard_name;
            END IF;
        END $$;
    """)
