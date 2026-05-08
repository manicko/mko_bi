"""add_registration_requests_table

Revision ID: a1e404502aac
Revises: ce58bba5d461
Create Date: 2026-05-05 16:30:39.639351

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1e404502aac'
down_revision: str | Sequence[str] | None = 'ce58bba5d461'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type if not exists (idempotent)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'registration_status') THEN
                CREATE TYPE registration_status AS ENUM ('pending', 'approved', 'rejected');
            END IF;
        END $$;
    """)
    
    # Create registration_requests table using raw SQL to avoid SQLAlchemy enum creation issues
    op.execute("""
        CREATE TABLE IF NOT EXISTS registration_requests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL UNIQUE,
            status registration_status NOT NULL DEFAULT 'pending',
            requested_by_ip INET,
            reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
            reviewed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    
    # Drop old indexes (these were renamed in later migrations, but we handle idempotently)
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dashboard_graph")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dashboard_id")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dims_gin")
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_graph_id")
    op.execute("DROP INDEX IF EXISTS idx_dashboard_access_dashboard")
    op.execute("DROP INDEX IF EXISTS idx_dashboard_access_user")
    
    # Create new indexes
    op.create_index('idx_access_dashboard', 'dashboard_access', ['dashboard_id'], unique=False)
    op.create_index('idx_dashboard_filter', 'dashboard_filters', ['dashboard_id', 'filter_id'], unique=False)
    
    # Alter columns to varchar(255) and rename constraints
    op.alter_column('dashboards', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.execute("DROP INDEX IF EXISTS idx_dashboards_name")
    op.create_unique_constraint(None, 'dashboards', ['name'])
    
    # Drop config column from dashboards
    op.drop_column('dashboards', 'config')
    
    op.alter_column('filters', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.execute("DROP INDEX IF EXISTS idx_filters_name")
    op.create_unique_constraint(None, 'filters', ['name'])
    
    op.alter_column('graphs', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.execute("DROP INDEX IF EXISTS idx_graphs_dashboard")
    op.execute("DROP INDEX IF EXISTS idx_graphs_dashboard_name")
    op.create_unique_constraint('uq_graph_dashboard_name', 'graphs', ['dashboard_id', 'name'])
    
    op.alter_column('layouts', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.execute("DROP INDEX IF EXISTS idx_layouts_name")
    op.create_unique_constraint(None, 'layouts', ['name'])
    
    op.alter_column('processing_logs', 'message',
               existing_type=sa.TEXT(),
               type_=sa.String(length=1000),
               existing_nullable=True)
    
    op.alter_column('users', 'email',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('users', 'password_hash',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.execute("DROP INDEX IF EXISTS idx_users_email")
    op.execute("DROP INDEX IF EXISTS idx_users_role")
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_unique_constraint(None, 'users', ['email'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraints using correct constraint names
    op.execute("DROP INDEX IF EXISTS idx_users_email")
    op.execute("DROP INDEX IF EXISTS ix_users_role")
    op.create_index(op.f('idx_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('idx_users_email'), 'users', ['email'], unique=True)
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Use CREATE INDEX IF NOT EXISTS since the index might have been created by later migrations
    op.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_dashboard_id ON processing_logs(dashboard_id)")
    
    op.alter_column('processing_logs', 'message',
               existing_type=sa.String(length=1000),
               type_=sa.TEXT(),
               existing_nullable=True)
    
    op.execute("DROP INDEX IF EXISTS idx_layouts_name")
    op.create_index(op.f('idx_layouts_name'), 'layouts', ['name'], unique=True)
    op.alter_column('layouts', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    op.execute("DROP INDEX IF EXISTS idx_graphs_dashboard_name")
    op.execute("DROP INDEX IF EXISTS idx_graphs_dashboard")
    op.create_index(op.f('idx_graphs_dashboard_name'), 'graphs', ['dashboard_id', 'name'], unique=True)
    op.create_index(op.f('idx_graphs_dashboard'), 'graphs', ['dashboard_id'], unique=False)
    op.alter_column('graphs', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    op.execute("DROP INDEX IF EXISTS idx_filters_name")
    op.create_index(op.f('idx_filters_name'), 'filters', ['name'], unique=True)
    op.alter_column('filters', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    op.add_column('dashboards', sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=False))
    op.execute("DROP INDEX IF EXISTS idx_dashboards_name")
    op.create_index(op.f('idx_dashboards_name'), 'dashboards', ['name'], unique=True)
    op.alter_column('dashboards', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Drop indexes that were created in upgrade (use IF EXISTS since they might have been renamed)
    op.execute("DROP INDEX IF EXISTS idx_dashboard_filter")
    op.execute("DROP INDEX IF EXISTS idx_access_dashboard")
    
    # Recreate indexes with old names (use CREATE IF NOT EXISTS to handle renamed indexes)
    op.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_access_user ON dashboard_access(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_access_dashboard ON dashboard_access(dashboard_id)")
    
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_graph_id ON aggregated_data(graph_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dims_gin ON aggregated_data USING GIN(dims)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_id ON aggregated_data(dashboard_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id)")
    
    # Drop registration_requests table
    op.drop_table('registration_requests')
    
    # Drop the enum type if it exists
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'registration_status') THEN
                DROP TYPE registration_status;
            END IF;
        END $$;
    """)
