"""Standardize index naming

Revision ID: 840a99edb818
Revises: 2aa835fe1fac
Create Date: 2026-05-03 12:16:20.489609

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '840a99edb818'
down_revision: str | Sequence[str] | None = '2aa835fe1fac'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename UNIQUE constraints (these also rename the underlying indexes)
    # Use DO block for idempotency
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_email_key') THEN
                ALTER TABLE users RENAME CONSTRAINT users_email_key TO idx_users_email;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'layouts_name_key') THEN
                ALTER TABLE layouts RENAME CONSTRAINT layouts_name_key TO idx_layouts_name;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'dashboards_name_key') THEN
                ALTER TABLE dashboards RENAME CONSTRAINT dashboards_name_key TO idx_dashboards_name;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_graph_dashboard_name') THEN
                ALTER TABLE graphs RENAME CONSTRAINT uq_graph_dashboard_name TO idx_graphs_dashboard_name;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'filters_name_key') THEN
                ALTER TABLE filters RENAME CONSTRAINT filters_name_key TO idx_filters_name;
            END IF;
        END $$;
    """)

    # Rename regular indexes (check if old name exists first)
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'ix_users_role' AND relkind = 'i') THEN
                EXECUTE 'ALTER INDEX ix_users_role RENAME TO idx_users_role';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_access_dashboard' AND relkind = 'i') THEN
                EXECUTE 'ALTER INDEX idx_access_dashboard RENAME TO idx_dashboard_access_dashboard';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_filter' AND relkind = 'i') THEN
                EXECUTE 'ALTER INDEX idx_dashboard_filter RENAME TO idx_dashboard_filters_dashboard_filter';
            END IF;
        END $$;
    """)

    # Create missing index on dashboard_access(user_id) if not exists
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_dashboard_access_user' AND relkind = 'i') THEN
                CREATE INDEX idx_dashboard_access_user ON dashboard_access(user_id);
            END IF;
        END $$;
    """)

    # Handle aggregated_data indexes - drop composite and create standard ones
    op.execute("DROP INDEX IF EXISTS idx_agg_dashboard_graph")
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_aggregated_data_dashboard_id' AND relkind = 'i') THEN
                CREATE INDEX idx_aggregated_data_dashboard_id ON aggregated_data(dashboard_id);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_aggregated_data_graph_id' AND relkind = 'i') THEN
                CREATE INDEX idx_aggregated_data_graph_id ON aggregated_data(graph_id);
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
    # Revert aggregated_data indexes
    op.drop_index('idx_aggregated_data_dims_gin', table_name='aggregated_data')
    op.drop_index('idx_aggregated_data_graph_id', table_name='aggregated_data')
    op.drop_index('idx_aggregated_data_dashboard_id', table_name='aggregated_data')
    op.create_index('idx_agg_dashboard_graph', 'aggregated_data', ['dashboard_id', 'graph_id'], unique=False)

    # Drop created index on dashboard_access
    op.drop_index('idx_dashboard_access_user', table_name='dashboard_access')

    # Rename regular indexes back
    try:
        op.execute("ALTER INDEX idx_dashboard_filters_dashboard_filter RENAME TO idx_dashboard_filter")
    except Exception:
        pass
    
    try:
        op.execute("ALTER INDEX idx_dashboard_access_dashboard RENAME TO idx_access_dashboard")
    except Exception:
        pass
    
    try:
        op.execute("ALTER INDEX idx_users_role RENAME TO ix_users_role")
    except Exception:
        pass

    # Rename UNIQUE constraints back
    try:
        op.execute("ALTER TABLE filters RENAME CONSTRAINT idx_filters_name TO filters_name_key")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE graphs RENAME CONSTRAINT idx_graphs_dashboard_name TO uq_graph_dashboard_name")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE dashboards RENAME CONSTRAINT idx_dashboards_name TO dashboards_name_key")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE layouts RENAME CONSTRAINT idx_layouts_name TO layouts_name_key")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE users RENAME CONSTRAINT idx_users_email TO users_email_key")
    except Exception:
        pass
