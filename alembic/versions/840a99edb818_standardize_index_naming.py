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
    op.execute("ALTER TABLE users RENAME CONSTRAINT users_email_key TO idx_users_email")
    op.execute("ALTER TABLE layouts RENAME CONSTRAINT layouts_name_key TO idx_layouts_name")
    op.execute("ALTER TABLE dashboards RENAME CONSTRAINT dashboards_name_key TO idx_dashboards_name")
    op.execute("ALTER TABLE graphs RENAME CONSTRAINT uq_graph_dashboard_name TO idx_graphs_dashboard_name")
    op.execute("ALTER TABLE filters RENAME CONSTRAINT filters_name_key TO idx_filters_name")

    # Rename regular indexes
    op.execute("ALTER INDEX ix_users_role RENAME TO idx_users_role")
    op.execute("ALTER INDEX idx_access_dashboard RENAME TO idx_dashboard_access_dashboard")
    op.execute("ALTER INDEX idx_dashboard_filter RENAME TO idx_dashboard_filters_dashboard_filter")

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
    op.execute("ALTER INDEX idx_dashboard_filters_dashboard_filter RENAME TO idx_dashboard_filter")
    op.execute("ALTER INDEX idx_dashboard_access_dashboard RENAME TO idx_access_dashboard")
    op.execute("ALTER INDEX idx_users_role RENAME TO ix_users_role")

    # Rename UNIQUE constraints back
    op.execute("ALTER TABLE filters RENAME CONSTRAINT idx_filters_name TO filters_name_key")
    op.execute("ALTER TABLE graphs RENAME CONSTRAINT idx_graphs_dashboard_name TO uq_graph_dashboard_name")
    op.execute("ALTER TABLE dashboards RENAME CONSTRAINT idx_dashboards_name TO dashboards_name_key")
    op.execute("ALTER TABLE layouts RENAME CONSTRAINT idx_layouts_name TO layouts_name_key")
    op.execute("ALTER TABLE users RENAME CONSTRAINT idx_users_email TO users_email_key")
