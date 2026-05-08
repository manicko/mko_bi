"""Script to recreate test database with correct schema."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def recreate_db():
    # Step 1: Drop and recreate database
    admin_url = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres"
    admin_engine = create_async_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
    )
    async with admin_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS bidb_test"))
        await conn.execute(text("CREATE DATABASE bidb_test"))
    await admin_engine.dispose()
    print("Database recreated")

    # Step 2: Create tables with correct schema
    test_url = "postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test"
    engine = create_async_engine(test_url)
    async with engine.begin() as conn:
        # Create enum types
        await conn.execute(text("""
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
        """))
        
        # Create tables
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role user_role NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email);
            
            CREATE TABLE IF NOT EXISTS layouts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                definition JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_layouts_name ON layouts (name);
            
            CREATE TABLE IF NOT EXISTS dashboards (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                description TEXT,
                config JSONB,
                layout_id UUID REFERENCES layouts(id) ON DELETE SET NULL,
                created_by UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboards_name ON dashboards (name);
            
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
            CREATE UNIQUE INDEX IF NOT EXISTS idx_graphs_dashboard_name ON graphs (dashboard_id, name);
            
            CREATE TABLE IF NOT EXISTS filters (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                type filter_type NOT NULL,
                config JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_filters_name ON filters (name);
            
            CREATE TABLE IF NOT EXISTS dashboard_access (
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
                permission dashboard_permission_level NOT NULL,
                PRIMARY KEY (user_id, dashboard_id)
            );
            
            CREATE TABLE IF NOT EXISTS dashboard_filters (
                dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
                filter_id UUID NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
                PRIMARY KEY (dashboard_id, filter_id)
            );
            
            CREATE TABLE IF NOT EXISTS processing_configs (
                dashboard_id UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
                settings JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            
            CREATE TABLE IF NOT EXISTS aggregated_data (
                id BIGSERIAL PRIMARY KEY,
                dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
                graph_id UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
                dims JSONB NOT NULL,
                metrics JSONB NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS processing_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                dashboard_id UUID REFERENCES dashboards(id) ON DELETE SET NULL,
                status processing_status NOT NULL,
                message TEXT,
                started_at TIMESTAMPTZ,
                finished_at TIMESTAMPTZ
            );
        """))
        print("Tables created")

        # Verify config column exists
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='dashboards' AND column_name='config'"
            )
        )
        columns = await result.fetchall()
        if not columns:
            print("ERROR: config column NOT found!")
        else:
            print("SUCCESS: config column exists!")

    await engine.dispose()

asyncio.run(recreate_db())
