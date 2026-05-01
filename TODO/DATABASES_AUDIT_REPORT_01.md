# DATABASES_AUDIT_REPORT.md

## 1. Database Inventory

| Logical Name | DSN Variable | Environment | Purpose | Creation Method |
|--------------|--------------|-------------|---------|-----------------|
| bidb | DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD | Development | Main application database | Manual creation via create_db.sql or application startup |
| bidb_test | Same as above but DB_NAME=bidb_test | Testing | Test database for pytest | Created and dropped by tests conftest.py |

## 2. Schema Documentation

### Database: bidb (Development)

#### Tables Overview
- users
- layouts
- dashboards
- graphs
- filters
- dashboard_access
- processing_configs
- aggregated_data
- processing_logs

#### Detailed Schema

##### users
- id: UUID, PRIMARY KEY, default uuid_generate_v4()
- email: TEXT, UNIQUE NOT NULL
- password_hash: TEXT NOT NULL
- role: TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer'))
- is_active: BOOLEAN DEFAULT TRUE
- created_at: TIMESTAMP DEFAULT NOW()
- Index: ix_users_role on role

##### layouts
- id: UUID, PRIMARY KEY, default uuid_generate_v4()
- name: TEXT UNIQUE NOT NULL
- definition: JSONB NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()

##### dashboards
- id: UUID, PRIMARY KEY, default uuid_generate_v4()
- name: TEXT UNIQUE NOT NULL
- description: TEXT
- layout_id: UUID REFERENCES layouts(id) ON DELETE SET NULL
- created_by: UUID REFERENCES users(id) ON DELETE SET NULL
- config: JSONB NOT NULL DEFAULT '{}'
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- Unique constraint on name
- Foreign keys: layouts(id), users(id)

##### graphs
- id: UUID, PRIMARY KEY, default uuid_generate_v4()
- dashboard_id: UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE
- name: TEXT NOT NULL
- type: TEXT NOT NULL CHECK (type IN ('bar', 'line', 'pie', 'table'))
- config: JSONB NOT NULL
- dimensions: JSONB NOT NULL
- metrics: JSONB NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()
- Unique constraint on (dashboard_id, name)
- Foreign key: dashboards(id) ON DELETE CASCADE

##### filters
- id: UUID, PRIMARY KEY, default uuid_generate_v4()
- name: TEXT UNIQUE NOT NULL
- type: TEXT NOT NULL
- config: JSONB NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()

##### dashboard_access
- user_id: UUID REFERENCES users(id) ON DELETE CASCADE
- dashboard_id: UUID REFERENCES dashboards(id) ON DELETE CASCADE
- permission: TEXT NOT NULL CHECK (permission IN ('view', 'edit', 'admin'))
- PRIMARY KEY (user_id, dashboard_id)
- Indexes: idx_access_user (user_id), idx_access_dashboard (dashboard_id)

##### processing_configs
- dashboard_id: UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE
- settings: JSONB NOT NULL
- updated_at: TIMESTAMP DEFAULT NOW()

##### aggregated_data
- id: BIGSERIAL PRIMARY KEY
- dashboard_id: UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE
- graph_id: UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE
- dims: JSONB NOT NULL
- metrics: JSONB NOT NULL
- Indexes: idx_agg_graph_id (graph_id), idx_agg_dashboard_id (dashboard_id), idx_agg_dims_gin GIN on dims
- Foreign keys: dashboards(id), graphs(id) both ON DELETE CASCADE

##### processing_logs
- id: UUID PRIMARY KEY DEFAULT uuid_generate_v4()
- dashboard_id: UUID REFERENCES dashboards(id)
- status: TEXT NOT NULL CHECK (status IN ('started', 'success', 'failed'))
- message: TEXT
- started_at: TIMESTAMP
- finished_at: TIMESTAMP
- Foreign key: dashboards(id)

#### Extensions
- uuid-ossp: generates universally unique identifiers

#### Sequences
- aggregated_data_id_seq: for aggregated_data.id

### Database: bidb_test (Test)
Same schema as bidb, but initially empty and populated by tests.

## 3. Schema Drift Report

Comparison between ORM models (src/mko_bi/db/models/) and real database (bidb):

| Object | Problem | ORM | Alembic | Real DB | Recommended Source of Truth |
|--------|---------|-----|---------|---------|----------------------------|
| users.role | ORM uses Enum with server_default text("'viewer'"), real DB uses TEXT with CHECK constraint | Enum(UserRoleEnum) with server_default text("'viewer'") | No migrations | TEXT with CHECK constraint | ORM (with migration to align) |
| users.created_at | ORM uses DateTime(timezone=True) with server_default text("now()"), real DB uses timestamp without time zone DEFAULT now() | DateTime(timezone=True) | No migrations | timestamp without time zone | Real DB (should change ORM to match or add timezone) |
| dashboards.created_at | Same as users.created_at | DateTime(timezone=True) | No migrations | timestamp without time zone | Real DB |
| dashboards.updated_at | ORM uses DateTime(timezone=True) with server_default text("now()") and onupdate=func.now(), real DB uses timestamp without time zone DEFAULT now() | DateTime(timezone=True) with onupdate | No migrations | timestamp without time zone | Real DB |
| dashboards.config | ORM uses JSON (JSON type), real DB uses jsonb | JSON | No migrations | JSONB | ORM should use JSONB for PostgreSQL |
| layouts.definition | Same as dashboards.config | JSON | No migrations | JSONB | ORM should use JSONB |
| filters.config | Same | JSON | No migrations | JSONB | ORM should use JSONB |
| graphs.config | Same | JSON | No migrations | JSONB | ORM should use JSONB |
| graphs.dimensions | Same | JSON | No migrations | JSONB | ORM should use JSONB |
| graphs.metrics | Same | JSON | No migrations | JSONB | ORM should use JSONB |
| processing_configs.settings | Same | JSON | No migrations | JSONB | ORM should use JSONB |
| processing_logs.dashboard_id | ORM allows NULL (UUID | None), real DB allows NULL (no NOT NULL) | UUID | No references | UUID (nullable) | Match (both nullable) |
| processing_logs.status | ORM uses TEXT without explicit CHECK, real DB has CHECK constraint | Text (no CHECK) | No migrations | TEXT with CHECK | Add CHECK in ORM or rely on DB |
| aggregated_data.dims | ORM uses custom JSONBType that falls back to JSON for non-PostgreSQL, real DB uses JSONB | JSONBType (JSONB for PG) | No migrations | JSONB | ORM is correct (abstracts away) |
| aggregated_data.metrics | Same | JSONBType | No migrations | JSONB | ORM is correct |

Notes:
- No Alembic migrations found, so no comparison possible.
- The ORM and real DB have differences in JSON vs JSONB and timezone-aware timestamps.
- The real DB uses timestamp without time zone, while ORM specifies timezone=True.

## 4. Migration Audit

| Check | Status | Notes |
|-------|--------|-------|
| Existence of migration scripts | NOT FOUND | No alembic directory or migration scripts found in the project. |
| Migration chain integrity | N/A | No migrations. |
| Reproducibility from zero | PARTIAL | Schema can be recreated using create_db.sql or SQLAlchemy Base.metadata.create_all(). |
| Broken revisions | N/A | No migrations. |
| Circular dependencies | N/A | No migrations. |
| Ability to run `alembic upgrade head` on empty DB | N/A | No alembic configured. |
| Manual SQL changes | UNKNOWN | No migration history to compare. |
| Non-idempotent migrations | N/A | No migrations. |
| State-dependent migrations | N/A | No migrations. |
| Migration drift | N/A | No migrations. |
| Mixing schema/data migrations | N/A | No migrations. |

## 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|-------------|----|------------------|------|
| Development | bidb | Isolated (separate database) | LOW |
| Testing | bidb_test | Isolated (separate database, created/dropped by tests) | LOW |
| Production | Not configured | N/A | N/A |

Notes:
- The test database is created and dropped by the test suite (see conftest.py).
- No shared credentials between environments (uses same DSN but different DB names).
- No evidence of shared usage between dev and test.

## 6. Architectural Problems

| Severity | Area | Problem | Risk | Recommendation |
|----------|------|---------|------|----------------|
| MEDIUM | Schema Design | Inconsistent use of JSON vs JSONB in ORM models | May cause issues when using ORM with non-PostgreSQL databases or when querying | Standardize on JSONB for PostgreSQL in ORM models (use JSONB type from sqlalchemy.dialects.postgresql) |
| MEDIUM | Schema Design | Timestamp columns without time zone in DB but timezone-aware in ORM | Potential confusion with time zones, especially if application spans multiple time zones | Align ORM and DB: either make DB columns timezone-aware (TIMESTAMP WITH TIME ZONE) or remove timezone=True from ORM. Given the use of `now()` which returns timestamp without time zone, the latter is simpler. |
| LOW | Indexing | No composite index on (dashboard_id, graph_id) in aggregated_data | Could lead to slower queries when filtering by both dashboard and graph (common in dashboards) | Add composite btree index on (dashboard_id, graph_id) |
| LOW | Constraints | Missing NOT NULL constraint on processing_logs.dashboard_id in ORM (allows NULL) while DB allows NULL | Inconsistent nullability | Decide if dashboard_id should be mandatory. If yes, add NOT NULL in DB and ORM. |
| LOW | Naming | Inconsistent index naming: some indexes prefixed with idx_*, others not | Minor maintainability issue | Adopt a consistent naming convention for all indexes (e.g., idx_<table>_<columns>). |

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|------|------|-----------------------|----------------|
| aggregated_data table | Growth of rows with number of dashboards, graphs, and data points | As data volume increases, queries on aggregated_data may slow down, especially without proper indexing | Already have indexes on dashboard_id and graph_id. Consider adding composite index (dashboard_id, graph_id) and partitioning by dashboard_id if volume grows very large (though premature partitioning is discouraged). |
| JSONB columns (dims, metrics) | Overuse of JSONB for fields that could be normalized | If the structure of dims and metrics becomes predictable, storing as JSONB may be less efficient than normalized columns | Monitor usage: if certain keys in dims/metrics are frequently queried, consider extracting them as separate columns. However, current flexibility is a feature. |
| dashboard_access table | Growth with number of users and dashboards | Querying access permissions could slow down | Existing indexes on user_id and dashboard_id are sufficient for typical lookups. |
| processing_logs table | Unbounded growth of log entries | Log table could grow indefinitely, consuming storage | Implement a log retention policy (e.g., delete logs older than X days) or archiving strategy. |

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|------|------|--------|----------------------|
| ORM vs DB type inconsistencies (JSON/JSONB, timezone) | Inconsistencies between ORM models and database schema | May cause bugs, confusion, and issues during migrations or when using ORM features | MEDIUM - Fix to align ORM with DB or vice versa. |
| Missing migrations | No migration system in place | Makes schema changes risky and hard to reproduce across environments | HIGH - Implement a migration system (e.g., Alembic) to manage schema changes. |
| No automated schema validation | No checks to ensure ORM matches DB | Schema drift can go unnoticed | MEDIUM - Implement automated checks in CI/CD to compare ORM models with DB schema. |
| Log table growth | processing_logs table unbounded | Potential storage issues over time | LOW - Add log retention policy. |

## 9. Required Architectural Improvements

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|----------|----------|--------|-----------------|--------------|-----------------|----------------|
| HIGH | Migrations | Schema | No migration system | Inability to safely evolve schema, reproduce environments, or rollback changes | Implement Alembic (or similar) for schema migrations | Ensures schema changes are versioned, reproducible, and safe. |
| MEDIUM | Schema Design | aggregated_data | Missing composite index on (dashboard_id, graph_id) | Queries filtering by both dashboard and graph may become slow as table grows | Add composite btree index on (dashboard_id, graph_id) | Improves query performance for dashboard-specific graph data lookups. |
| MEDIUM | Schema Design | ORM models | Inconsistent use of JSON vs JSONB | Potential issues when using ORM with different databases or querying | Change ORM to use JSONB from sqlalchemy.dialects.postgresql for PostgreSQL-specific columns | Ensures ORM accurately reflects PostgreSQL capabilities and avoids unnecessary conversions. |
| MEDIUM | Schema Design | Timestamp columns | Timestamp without time zone in DB vs timezone-aware in ORM | Confusion and potential errors in time-sensitive operations | Align: either change DB to TIMESTAMP WITH TIME ZONE or remove timezone=True from ORM. Given use of `now()`, recommend removing timezone=True from ORM. | Prevents timezone-related bugs and ensures consistent time handling. |
| LOW | Maintenance | Index naming | Inconsistent index naming conventions | Minor confusion when managing indexes | Adopt and enforce a consistent index naming standard (e.g., idx_<table>_<column(s)>) | Improves maintainability and clarity. |

---
### Conclusion

The database schema is well-designed for flexibility (using JSONB for dynamic attributes) and follows good practices (UUID primary keys, proper foreign keys with CASCADE, appropriate indexes). However, there are inconsistencies between the ORM models and the actual database schema, primarily in JSON/JSONB usage and timezone handling of timestamps. The lack of a migration system is a significant gap that should be addressed to ensure safe and reproducible schema evolution.

Addressing the recommended improvements will enhance maintainability, scalability, and operational stability.