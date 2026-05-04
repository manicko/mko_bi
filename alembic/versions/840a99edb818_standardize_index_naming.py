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
    # Use try-except to handle case where constraint doesn't exist
    try:
        op.execute("ALTER TABLE users RENAME CONSTRAINT users_email_key TO idx_users_email")
    except Exception:
        pass  # Constraint might not exist or already renamed
    
    try:
        op.execute("ALTER TABLE layouts RENAME CONSTRAINT layouts_name_key TO idx_layouts_name")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE dashboards RENAME CONSTRAINT dashboards_name_key TO idx_dashboards_name")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE graphs RENAME CONSTRAINT uq_graph_dashboard_name TO idx_graphs_dashboard_name")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE filters RENAME CONSTRAINT filters_name_key TO idx_filters_name")
    except Exception:
        pass

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

    # Create missing index on dashboard_access(user_id) and rename
    op.create_index('idx_dashboard_access_user', 'dashboard_access', ['user_id'], unique=False)

    # Handle aggregated_data indexes - drop composite and create standard ones
    op.execute("DROP INDEX IF EXISTS idx_agg_dashboard_graph")
    op.create_index('idx_aggregated_data_dashboard_id', 'aggregated_data', ['dashboard_id'], unique=False)
    op.create_index('idx_aggregated_data_graph_id', 'aggregated_data', ['graph_id'], unique=False)
    op.create_index('idx_aggregated_data_dims_gin', 'aggregated_data', ['dims'], unique=False, postgresql_using='gin')


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
