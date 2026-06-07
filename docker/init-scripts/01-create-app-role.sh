#!/bin/bash
# =============================================================================
# Create dedicated application role with limited privileges (least-privilege)
# This script is run on PostgreSQL container initialization.
# Password is substituted by Docker postgres image from MKOBI_APP_PASSWORD env var.
# =============================================================================

set -e

# Drop role if exists, then recreate with correct password
# This ensures password is always in sync with MKOBI_APP_PASSWORD environment variable
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOF
DROP ROLE IF EXISTS mkobi_app;
CREATE ROLE mkobi_app WITH LOGIN PASSWORD $${MKOBI_APP_PASSWORD}$$;
-- CREATEDB privilege NOT granted - admin credentials (postgres superuser)
-- are used for CREATE/DROP DATABASE operations in recreate_test_database()

-- Grant connection to the database
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO mkobi_app;

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

echo "Application role mkobi_app created successfully"