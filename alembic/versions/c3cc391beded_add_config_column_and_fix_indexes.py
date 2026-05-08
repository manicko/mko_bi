"""add_config_column_and_fix_indexes.

Revision ID: c3cc391beded
Revises: 20260508145000
Create Date: 2026-05-08 21:34:53.927730

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3cc391beded'
down_revision: str | Sequence[str] | None = '20260508145000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add config column to dashboards table if not exists (idempotent)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='dashboards' AND column_name='config'
            ) THEN
                ALTER TABLE dashboards ADD COLUMN config JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """)

    # Fix indexes to match SPEC.md requirements
    
    # 1. Rename idx_access_dashboard to idx_dashboard_access_dashboard
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_access_dashboard' AND relkind = 'i') THEN
                IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_access_dashboard' AND relkind = 'i') THEN
                    ALTER INDEX idx_access_dashboard RENAME TO idx_dashboard_access_dashboard;
                END IF;
            END IF;
        END $$;
    """)

    # 2. Rename idx_dashboard_filter to idx_dashboard_filters_dashboard_filter
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_filter' AND relkind = 'i') THEN
                IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_filters_dashboard_filter' AND relkind = 'i') THEN
                    ALTER INDEX idx_dashboard_filter RENAME TO idx_dashboard_filters_dashboard_filter;
                END IF;
            END IF;
        END $$;
    """)

    # 3. Create idx_dashboard_access_user if not exists
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_access_user' AND relkind = 'i') THEN
                CREATE INDEX idx_dashboard_access_user ON dashboard_access(user_id);
            END IF;
        END $$;
    """)

    # 4. Create idx_graphs_dashboard if not exists
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_graphs_dashboard' AND relkind = 'i') THEN
                CREATE INDEX idx_graphs_dashboard ON graphs(dashboard_id);
            END IF;
        END $$;
    """)

    # 5. Ensure aggregated_data indexes exist with correct names (idempotent)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_aggregated_data_graph_id' AND relkind = 'i') THEN
                CREATE INDEX idx_aggregated_data_graph_id ON aggregated_data(graph_id);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_aggregated_data_dashboard_id' AND relkind = 'i') THEN
                CREATE INDEX idx_aggregated_data_dashboard_id ON aggregated_data(dashboard_id);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_aggregated_data_dashboard_graph' AND relkind = 'i') THEN
                CREATE INDEX idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_aggregated_data_dims_gin' AND relkind = 'i') THEN
                CREATE INDEX idx_aggregated_data_dims_gin ON aggregated_data USING GIN (dims);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes we created/renamed
    op.execute("DROP INDEX IF EXISTS idx_dashboard_filters_dashboard_filter")
    op.execute("DROP INDEX IF EXISTS idx_dashboard_access_dashboard")
    op.execute("DROP INDEX IF EXISTS idx_dashboard_access_user")
    op.execute("DROP INDEX IF EXISTS idx_graphs_dashboard")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dashboard_graph")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dashboard_id")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_graph_id")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dims_gin")

    # Recreate old index names (best effort)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_filter' AND relkind = 'i') THEN
                CREATE INDEX idx_dashboard_filter ON dashboard_filters(dashboard_id, filter_id);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_access_dashboard' AND relkind = 'i') THEN
                CREATE INDEX idx_access_dashboard ON dashboard_access(dashboard_id);
            END IF;
        END $$;
    """)

    # Drop config column
    op.drop_column('dashboards', 'config')
