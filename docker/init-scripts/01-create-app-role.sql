-- =============================================================================
-- Create dedicated application role with limited privileges (least-privilege)
-- This script is run on PostgreSQL container initialization.
-- Password is substituted from MKOBI_APP_PASSWORD environment variable.
-- =============================================================================

-- Create application role with login capability
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mkobi_app') THEN
        -- Password is substituted by Docker postgres image from environment
        CREATE ROLE mkobi_app WITH LOGIN PASSWORD '${MKOBI_APP_PASSWORD}';
    END IF;
END $$;

-- Grant connection to the database
GRANT CONNECT ON DATABASE bidb TO mkobi_app;

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO mkobi_app;

-- Grant data manipulation privileges on all current tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkobi_app;

-- Grant sequence usage for auto-increment columns
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mkobi_app;

-- Grant default privileges for future tables (PostgreSQL 14+)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mkobi_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO mkobi_app;

-- Note: For new tables created by migrations (which use postgres role),
-- ensure ownership is transferred or permissions are granted after migration.
-- Alembic migrations run as postgres user and should handle permission grants.