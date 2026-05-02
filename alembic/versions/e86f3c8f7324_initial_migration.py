"""Initial migration

Revision ID: e86f3c8f7324
Revises: 
Create Date: 2026-05-01 21:27:22.548960

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e86f3c8f7324'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop CHECK constraints before altering to enum types
    op.execute("ALTER TABLE dashboard_access DROP CONSTRAINT IF EXISTS dashboard_access_permission_check")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check")
    
    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'editor', 'viewer')")
    op.execute("CREATE TYPE dashboard_permission_level AS ENUM ('view', 'edit', 'admin')")
    
    # Create dashboard_filters table
    op.create_table(
        'dashboard_filters',
        sa.Column('dashboard_id', sa.UUID(), nullable=False),
        sa.Column('filter_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filter_id'], ['filters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dashboard_id', 'filter_id')
    )
    op.create_index('idx_dashboard_filter', 'dashboard_filters', ['dashboard_id', 'filter_id'], unique=False)
    
    # Alter aggregated_data table
    op.alter_column('aggregated_data', 'id',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True)
    op.drop_index(op.f('idx_agg_dashboard_id'), table_name='aggregated_data')
    op.drop_index(op.f('idx_agg_dims_gin'), table_name='aggregated_data', postgresql_using='gin')
    op.drop_index(op.f('idx_agg_graph_id'), table_name='aggregated_data')
    
    # Alter dashboard_access - permission column
    op.execute("ALTER TABLE dashboard_access ALTER COLUMN permission TYPE dashboard_permission_level USING permission::dashboard_permission_level")
    op.drop_index(op.f('idx_access_user'), table_name='dashboard_access')
    
    # Alter dashboards table
    op.alter_column('dashboards', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('dashboards', 'config',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.alter_column('dashboards', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.alter_column('dashboards', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_constraint(op.f('dashboards_created_by_fkey'), 'dashboards', type_='foreignkey')
    op.drop_constraint(op.f('dashboards_layout_id_fkey'), 'dashboards', type_='foreignkey')
    op.create_foreign_key(None, 'dashboards', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'dashboards', 'layouts', ['layout_id'], ['id'], ondelete='SET NULL')
    
    # Alter filters table
    op.alter_column('filters', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('filters', 'type',
               existing_type=sa.TEXT(),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('filters', 'config',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.alter_column('filters', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    
    # Alter graphs table
    op.alter_column('graphs', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('graphs', 'type',
               existing_type=sa.TEXT(),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('graphs', 'config',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.alter_column('graphs', 'dimensions',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.alter_column('graphs', 'metrics',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.alter_column('graphs', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_constraint(op.f('graphs_dashboard_id_name_key'), 'graphs', type_='unique')
    op.create_unique_constraint('uq_graph_dashboard_name', 'graphs', ['dashboard_id', 'name'])
    
    # Alter layouts table
    op.alter_column('layouts', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('layouts', 'definition',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.alter_column('layouts', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    
    # Alter processing_configs table
    op.alter_column('processing_configs', 'settings',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.alter_column('processing_configs', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    
    # Alter processing_logs table
    op.alter_column('processing_logs', 'status',
               existing_type=sa.TEXT(),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('processing_logs', 'message',
               existing_type=sa.TEXT(),
               type_=sa.String(length=1000),
               existing_nullable=True)
    op.alter_column('processing_logs', 'started_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.alter_column('processing_logs', 'finished_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.drop_constraint(op.f('processing_logs_dashboard_id_fkey'), 'processing_logs', type_='foreignkey')
    op.create_foreign_key(None, 'processing_logs', 'dashboards', ['dashboard_id'], ['id'], ondelete='SET NULL')
    
    # Alter users table - role column
    op.alter_column('users', 'email',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.alter_column('users', 'password_hash',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::user_role")
    op.alter_column('users', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('true'))
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.create_index('ix_users_role', 'users', ['role'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes and alter columns back
    op.drop_index('ix_users_role', table_name='users')
    
    # Revert users table
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('users', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('true'))
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT USING role::TEXT")
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Revert processing_logs table
    op.drop_constraint(None, 'processing_logs', type_='foreignkey')
    op.create_foreign_key(op.f('processing_logs_dashboard_id_fkey'), 'processing_logs', 'dashboards', ['dashboard_id'], ['id'])
    op.alter_column('processing_logs', 'finished_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.alter_column('processing_logs', 'started_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.alter_column('processing_logs', 'message',
               existing_type=sa.String(length=1000),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.alter_column('processing_logs', 'status',
               existing_type=sa.String(length=50),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Revert processing_configs table
    op.alter_column('processing_configs', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('processing_configs', 'settings',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    
    # Revert layouts table
    op.alter_column('layouts', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('layouts', 'definition',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.alter_column('layouts', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Revert graphs table
    op.drop_constraint('uq_graph_dashboard_name', 'graphs', type_='unique')
    op.create_unique_constraint(op.f('graphs_dashboard_id_name_key'), 'graphs', ['dashboard_id', 'name'], postgresql_nulls_not_distinct=False)
    op.alter_column('graphs', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('graphs', 'metrics',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.alter_column('graphs', 'dimensions',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.alter_column('graphs', 'config',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.alter_column('graphs', 'type',
               existing_type=sa.String(length=50),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('graphs', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Revert filters table
    op.alter_column('filters', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('filters', 'config',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.alter_column('filters', 'type',
               existing_type=sa.String(length=50),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('filters', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Revert dashboards table
    op.drop_constraint(None, 'dashboards', type_='foreignkey')
    op.drop_constraint(None, 'dashboards', type_='foreignkey')
    op.create_foreign_key(op.f('dashboards_layout_id_fkey'), 'dashboards', 'layouts', ['layout_id'], ['id'])
    op.create_foreign_key(op.f('dashboards_created_by_fkey'), 'dashboards', 'users', ['created_by'], ['id'])
    op.alter_column('dashboards', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('dashboards', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('dashboards', 'config',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.alter_column('dashboards', 'name',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=False)
    
    # Revert dashboard_access - permission column
    op.execute("ALTER TABLE dashboard_access ALTER COLUMN permission TYPE TEXT USING permission::TEXT")
    op.create_index(op.f('idx_access_user'), 'dashboard_access', ['user_id'], unique=False)
    
    # Revert aggregated_data table
    op.create_index(op.f('idx_agg_graph_id'), 'aggregated_data', ['graph_id'], unique=False)
    op.create_index(op.f('idx_agg_dims_gin'), 'aggregated_data', ['dims'], unique=False, postgresql_using='gin')
    op.create_index(op.f('idx_agg_dashboard_id'), 'aggregated_data', ['dashboard_id'], unique=False)
    op.alter_column('aggregated_data', 'id',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               autoincrement=True)
    
    # Drop dashboard_filters table
    op.drop_index('idx_dashboard_filter', table_name='dashboard_filters')
    op.drop_table('dashboard_filters')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS dashboard_permission_level")
    op.execute("DROP TYPE IF EXISTS user_role")
    
    # Re-create CHECK constraints
    op.execute("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role = ANY (ARRAY['admin'::text, 'editor'::text, 'viewer'::text]))")
    op.execute("ALTER TABLE dashboard_access ADD CONSTRAINT dashboard_access_permission_check CHECK (permission = ANY (ARRAY['view'::text, 'edit'::text, 'admin'::text]))")
