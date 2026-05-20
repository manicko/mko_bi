"""Drop broken update_graphs_updated_at trigger on graphs table.

The graphs table has no updated_at column, but migration 7130ecb0388c
created a trigger that references it. This trigger will cause runtime
errors on any UPDATE to the graphs table.

Revision ID: ffd23f1f7e2b
Revises: 7130ecb0388c
Create Date: 2026-05-20 10:41:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ffd23f1f7e2b"
down_revision: str | Sequence[str] | None = "7130ecb0388c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the broken update_graphs_updated_at trigger from graphs table."""
    op.execute("DROP TRIGGER IF EXISTS update_graphs_updated_at ON graphs")


def downgrade() -> None:
    """Recreate the trigger (for completeness; will be broken without updated_at column)."""
    # Note: This downgrade recreates the trigger but it will still fail
    # because the graphs table has no updated_at column.
    # To properly restore the broken state:
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'update_graphs_updated_at'
            ) THEN
                CREATE TRIGGER update_graphs_updated_at
                BEFORE UPDATE ON graphs
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$;
    """)