#!/bin/bash
# =============================================================================
# Create dedicated application role.
# This script is run on PostgreSQL container initialization (first volume start).
#
# NOTE: PostgreSQL 18+ uses the 'builtin' locale provider with C.UTF-8, which
# provides immutable collation that never changes across OS updates. No template1
# locale fix is needed.
# =============================================================================

set -e

echo "Creating application role mkobi_app..."

# Create the role with password from environment variable.
# Use psql -v flag to pass the password safely (avoids shell expansion issues
# with $$ heredoc patterns that caused PID-based garbage passwords).
psql -v ON_ERROR_STOP=1 \
     -v app_password="'${MKOBI_APP_PASSWORD}'" \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" <<'EOF'
DROP ROLE IF EXISTS mkobi_app;
CREATE ROLE mkobi_app WITH LOGIN PASSWORD :app_password;
-- CREATEDB privilege NOT granted - admin credentials (postgres superuser)
-- are used for CREATE/DROP DATABASE operations in recreate_test_database()

-- Grant connection to the database
GRANT CONNECT ON DATABASE :DBNAME TO mkobi_app;

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO mkobi_app;

-- Grant data manipulation privileges on all current tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkobi_app;

-- Grant sequence usage for auto-increment columns
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mkobi_app;

-- Grant default privileges for future tables (PostgreSQL 14+)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mkobi_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO mkobi_app;
EOF

echo "Application role mkobi_app created successfully."