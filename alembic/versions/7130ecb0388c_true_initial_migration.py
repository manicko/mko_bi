"""True initial migration - creates all tables from scratch

Revision ID: 7130ecb0388c
Revises:
Create Date: 2026-05-03 17:10:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7130ecb0388c'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables from scratch according to SPEC.md."""
    # Create enum types (with existence check for idempotency)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('admin', 'editor', 'viewer');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'dashboard_permission_level') THEN
                CREATE TYPE dashboard_permission_level AS ENUM ('view', 'edit', 'admin');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'graph_type') THEN
                CREATE TYPE graph_type AS ENUM ('bar', 'line', 'pie', 'table');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'filter_type') THEN
                CREATE TYPE filter_type AS ENUM ('select', 'multiselect', 'range', 'date');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_status') THEN
                CREATE TYPE processing_status AS ENUM ('started', 'uploaded', 'processing', 'success', 'failed', 'completed');
            END IF;
        END $$;
    """)

    # Create users table (with existence check)
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role user_role NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)")

    # Create layouts table
    op.execute("""
        CREATE TABLE IF NOT EXISTS layouts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            definition JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_layouts_name ON layouts (name)")

    # Create dashboards table
    op.execute("""
        CREATE TABLE IF NOT EXISTS dashboards (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            layout_id UUID REFERENCES layouts(id) ON DELETE SET NULL,
            created_by UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboards_name ON dashboards (name)")

    # Create graphs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS graphs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            type graph_type NOT NULL,
            config JSONB NOT NULL,
            dimensions JSONB NOT NULL,
            metrics JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_graphs_dashboard_name ON graphs (dashboard_id, name)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_graphs_dashboard ON graphs (dashboard_id)")

    # Create filters table
    op.execute("""
        CREATE TABLE IF NOT EXISTS filters (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            type filter_type NOT NULL,
            config JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_filters_name ON filters (name)")

    # Create dashboard_access table
    op.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_access (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
            permission dashboard_permission_level NOT NULL,
            PRIMARY KEY (user_id, dashboard_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_access_user ON dashboard_access (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_access_dashboard ON dashboard_access (dashboard_id)")

    # Create dashboard_filters table (many-to-many)
    op.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_filters (
            dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
            filter_id UUID NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
            PRIMARY KEY (dashboard_id, filter_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_filters_dashboard_filter ON dashboard_filters (dashboard_id, filter_id)")

    # Create processing_configs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS processing_configs (
            dashboard_id UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
            settings JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    # Create aggregated_data table with BIGSERIAL
    op.execute("""
        CREATE TABLE IF NOT EXISTS aggregated_data (
            id BIGSERIAL PRIMARY KEY,
            dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
            graph_id UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
            dims JSONB NOT NULL,
            metrics JSONB NOT NULL
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_id ON aggregated_data (dashboard_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_graph_id ON aggregated_data (graph_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dims_gin ON aggregated_data USING GIN (dims)")

    # Create processing_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS processing_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dashboard_id UUID REFERENCES dashboards(id) ON DELETE SET NULL,
            status processing_status NOT NULL,
            message TEXT,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ
        );
    """)


def downgrade() -> None:
    """Drop all tables and enum types."""
    # Drop tables in reverse order (respecting foreign keys)
    op.execute("DROP TABLE IF EXISTS dashboard_access CASCADE")
    op.execute("DROP TABLE IF EXISTS dashboard_filters CASCADE")
    op.execute("DROP TABLE IF EXISTS filters CASCADE")
    op.execute("DROP TABLE IF EXISTS graphs CASCADE")
    op.execute("DROP TABLE IF EXISTS dashboards CASCADE")
    op.execute("DROP TABLE IF EXISTS layouts CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS aggregated_data CASCADE")
    op.execute("DROP TABLE IF EXISTS processing_configs CASCADE")
    op.execute("DROP TABLE IF EXISTS processing_logs CASCADE")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS processing_status")
    op.execute("DROP TYPE IF EXISTS filter_type")
    op.execute("DROP TYPE IF EXISTS graph_type")
    op.execute("DROP TYPE IF EXISTS dashboard_permission_level")
    op.execute("DROP TYPE IF EXISTS user_role")
