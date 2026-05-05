"""Add DB constraints and fix schema issues

Revision ID: ce58bba5d461
Revises: a1b2c3d4e5f6
Create Date: 2026-05-05 07:04:50.452786

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ce58bba5d461'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # TASK-DB-002: Add default value to users.role column
    op.execute("""
        ALTER TABLE users ALTER COLUMN role SET DEFAULT 'viewer'::user_role;
    """)

    # TASK-DB-003: Add composite index on aggregated_data(dashboard_id, graph_id)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph 
        ON aggregated_data(dashboard_id, graph_id);
    """)

    # TASK-DB-005: Add email length constraint to users table
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'users_email_length_check'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_email_length_check 
                CHECK (length(email) <= 255);
            END IF;
        END $$;
    """)

    # TASK-DB-006: Remove redundant index idx_dashboard_filters_dashboard_filter
    # PRIMARY KEY (dashboard_id, filter_id) already covers the same query pattern
    op.execute("DROP INDEX IF EXISTS idx_dashboard_filters_dashboard_filter")

    # TASK-DB-009: Add updated_at triggers for tables
    # Create the trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create triggers for tables with updated_at column
    tables_with_updated_at = ['dashboards', 'processing_configs', 'layouts', 'graphs', 'users']

    for table_name in tables_with_updated_at:
        trigger_name = f"update_{table_name}_updated_at"
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger 
                    WHERE tgname = '{trigger_name}'
                ) THEN
                    CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON {table_name}
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                END IF;
            END $$;
        """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop triggers
    tables_with_updated_at = ['dashboards', 'processing_configs', 'layouts', 'graphs', 'users']
    for table_name in tables_with_updated_at:
        trigger_name = f"update_{table_name}_updated_at"
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table_name}")

    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Recreate the dropped index (TASK-DB-006)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_dashboard_filters_dashboard_filter 
        ON dashboard_filters(dashboard_id, filter_id)
    """)

    # Drop the email length constraint (TASK-DB-005)
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_length_check")

    # Drop composite index (TASK-DB-003)
    op.execute("DROP INDEX IF EXISTS idx_aggregated_data_dashboard_graph")

    # Remove default from users.role (TASK-DB-002)
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
