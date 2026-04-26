CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 2. layouts
CREATE TABLE layouts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    definition      JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 3. dashboards
CREATE TABLE dashboards (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    layout_id       UUID REFERENCES layouts(id),
    created_by      UUID REFERENCES users(id),
    config          JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 4. graphs
CREATE TABLE graphs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('bar', 'line', 'pie', 'table')),
    config          JSONB NOT NULL,
    dimensions      JSONB NOT NULL,
    metrics         JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (dashboard_id, name)
);

-- 5. filters
CREATE TABLE filters (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    type            TEXT NOT NULL,
    config          JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 6. dashboard_access
CREATE TABLE dashboard_access (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    permission      TEXT NOT NULL CHECK (permission IN ('view', 'edit', 'admin')),
    PRIMARY KEY (user_id, dashboard_id)
);

-- 7. processing_configs
CREATE TABLE processing_configs (
    dashboard_id    UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
    settings        JSONB NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 8. aggregated_data
CREATE TABLE aggregated_data (
    id              BIGSERIAL PRIMARY KEY,
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    graph_id        UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    dims            JSONB NOT NULL,
    metrics         JSONB NOT NULL
);

-- 9. processing_logs
CREATE TABLE processing_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id    UUID REFERENCES dashboards(id),
    status          TEXT NOT NULL CHECK (status IN ('started', 'success', 'failed')),
    message         TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP
);

-- Индексы
CREATE INDEX idx_agg_graph_id ON aggregated_data(graph_id);
CREATE INDEX idx_agg_dashboard_id ON aggregated_data(dashboard_id);
CREATE INDEX idx_agg_dims_gin ON aggregated_data USING GIN (dims);
CREATE INDEX idx_access_user ON dashboard_access(user_id);
CREATE INDEX idx_access_dashboard ON dashboard_access(dashboard_id);
