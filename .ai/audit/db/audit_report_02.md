# Database Architecture Audit Report 02 — mkobi BI Dashboard

**Date:** 2026-05-16
**Auditor:** OWL (Architecture Audit Agent)
**Scope:** PostgreSQL database architecture, schema lifecycle, reproducibility, drift analysis
**Databases audited:** `bidb` (main/production), `bidb_test` (test)
**Real DB inspected:** Yes (via MCP PostgreSQL tools)

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | dev / prod / staging | Main application database | `DATABASE__DBNAME=bidb` → constructed to `postgresql+asyncpg://postgres:{password}@host:5432/bidb` | Docker Compose `POSTGRES_DB: bidb`; auto-created by PostgreSQL init; migrations applied via Alembic on app startup when `AUTO_MIGRATE=true` |
| `bidb_test` | test / dev (override) | Test database (pytest) | `DATABASE__TEST_DBNAME=bidb_test` → constructed to `postgresql+asyncpg://postgres:{password}@host:5432/bidb_test` | Created/dropped at runtime by `DatabaseStarter.recreate_test_database()` when `RECREATE_TEST_DB=true`; migrations applied via Alembic |

**DSN Construction:** The application never uses a raw `DATABASE_URL` environment variable. The URL is always constructed from nested `DATABASE__*` settings via `PostgresDsn.build(scheme="postgresql+asyncpg", ...)`.

---

## 2. Schema Documentation

### 2.1 Extensions

| Extension | Owner | Purpose |
|---|---|---|
| `plpgsql` | postgres | PL/pgSQL procedural language (system) |
| `uuid-ossp` | — | UUID generation functions (`uuid_generate_v4()`) — **NOT installed in real DB** |

**Note:** The real database uses `gen_random_uuid()` (from `pgcrypto` or PostgreSQL 13+ built-in) instead of `uuid-ossp.uuid_generate_v4()`. The `uuid-ossp` extension is not installed. This is fine for PostgreSQL 16, but the `create_db.sql` script explicitly calls `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`.

### 2.2 Enum Types

| Enum Name | Values | Used In |
|---|---|---|
| `user_role` | `admin`, `editor`, `viewer` | `users.role` |
| `dashboard_permission_level` | `view`, `edit`, `admin` | `dashboard_access.permission` |
| `graph_type` | `bar`, `line`, `pie`, `table` | `graphs.type` |
| `filter_type` | `select`, `multiselect`, `range`, `date` | `filters.type` |
| `processing_status` | `started`, `uploaded`, `processing`, `success`, `failed`, `completed` | `processing_logs.status` |
| `registration_status` | `pending`, `approved`, `rejected` | `registration_requests.status` |

### 2.3 Tables

#### `users`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `email` | `character varying(255)` | NO | — | `str` | UNIQUE |
| `password_hash` | `character varying(255)` | NO | — | `str` | |
| `role` | `user_role` (enum) | NO | `'viewer'::user_role` | `UserRole` | |
| `is_active` | `boolean` | NO | `true` | `bool` | |
| `created_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |
| `updated_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |

**Indexes:** `users_pkey` (PK), `users_email_key` (UNIQUE), `ix_users_role` (btree)

**Constraints:** `users_email_length_check` (CHECK length <= 255)

#### `layouts`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `name` | `character varying(255)` | NO | — | `str` | UNIQUE |
| `definition` | `jsonb` | NO | — | `dict` | |
| `created_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |
| `updated_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |

**Indexes:** `layouts_pkey` (PK), `layouts_name_key` (UNIQUE)

#### `dashboards`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `name` | `character varying(255)` | NO | — | `str` | UNIQUE |
| `description` | `text` | YES | — | `str \| None` | |
| `layout_id` | `uuid` | YES | — | `UUID \| None` | FK → layouts.id (SET NULL) |
| `created_by` | `uuid` | YES | — | `UUID \| None` | FK → users.id (SET NULL) |
| `created_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |
| `updated_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |
| `config` | `jsonb` | YES | `'{}'::jsonb` | `dict \| None` | |

**Indexes:** `dashboards_pkey` (PK), `dashboards_name_key` (UNIQUE)

#### `graphs`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `dashboard_id` | `uuid` | NO | — | `UUID` | FK → dashboards.id (CASCADE) |
| `name` | `character varying(255)` | NO | — | `str` | |
| `type` | `graph_type` (enum) | NO | — | `GraphType` | |
| `config` | `jsonb` | NO | — | `dict` | |
| `dimensions` | `jsonb` | NO | — | `list[str]` | |
| `metrics` | `jsonb` | NO | — | `list[str]` | |
| `created_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |

**Indexes:** `graphs_pkey` (PK), `idx_graphs_dashboard_name` (UNIQUE on dashboard_id, name), `idx_graphs_dashboard` (btree on dashboard_id)

#### `filters`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `name` | `character varying(255)` | NO | — | `str` | UNIQUE |
| `type` | `filter_type` (enum) | NO | — | `FilterType` | |
| `config` | `jsonb` | NO | — | `dict` | |
| `created_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |

**Indexes:** `filters_pkey` (PK), `filters_name_key` (UNIQUE)

#### `dashboard_access`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `user_id` | `uuid` | NO | — | `UUID` | FK → users.id (CASCADE), PK |
| `dashboard_id` | `uuid` | NO | — | `UUID` | FK → dashboards.id (CASCADE), PK |
| `permission` | `dashboard_permission_level` (enum) | NO | — | `DashboardPermission` | |

**Indexes:** `dashboard_access_pkey` (PK), `idx_dashboard_access_user` (btree), `idx_dashboard_access_dashboard` (btree)

#### `dashboard_filters` (many-to-many junction)

| Column | Type (Real DB) | Nullable | Default | Notes |
|---|---|---|---|---|
| `dashboard_id` | `uuid` | NO | — | FK → dashboards.id (CASCADE), PK |
| `filter_id` | `uuid` | NO | — | FK → filters.id (CASCADE), PK |

**Indexes:** `dashboard_filters_pkey` (PK), `idx_dashboard_filters_dashboard_filter` (btree)

#### `processing_configs`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `dashboard_id` | `uuid` | NO | — | `UUID` | FK → dashboards.id (CASCADE), PK |
| `settings` | `jsonb` | NO | — | `dict` | |
| `updated_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |

**Indexes:** `processing_configs_pkey` (PK)

#### `aggregated_data`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `bigint` | NO | `nextval('aggregated_data_id_seq')` | `int` | PK, BIGSERIAL |
| `dashboard_id` | `uuid` | NO | — | `UUID` | FK → dashboards.id (CASCADE) |
| `graph_id` | `uuid` | NO | — | `UUID` | FK → graphs.id (CASCADE) |
| `dims` | `jsonb` | NO | — | `dict` | |
| `metrics` | `jsonb` | NO | — | `dict` | |

**Indexes:** `aggregated_data_pkey` (PK), `idx_aggregated_data_graph_id` (btree), `idx_aggregated_data_dashboard_id` (btree), `idx_aggregated_data_dashboard_graph` (composite btree), `idx_aggregated_data_dims_gin` (GIN), `uq_aggregated_data_dashboard_graph_dims` (UNIQUE on dashboard_id, graph_id, dims::text)

#### `processing_logs`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `dashboard_id` | `uuid` | YES | — | `UUID \| None` | FK → dashboards.id (SET NULL) |
| `status` | `processing_status` (enum) | NO | — | `ProcessingStatus` | |
| `message` | `character varying(1000)` | YES | — | `str \| None` | |
| `started_at` | `timestamp with time zone` | YES | — | `datetime \| None` | |
| `finished_at` | `timestamp with time zone` | YES | — | `datetime \| None` | |

**Indexes:** `processing_logs_pkey` (PK), `idx_processing_logs_dashboard_id` (btree)

#### `registration_requests`

| Column | Type (Real DB) | Nullable | Default | ORM Type | Notes |
|---|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | `UUID` | PK |
| `email` | `character varying(255)` | NO | — | `str` | UNIQUE |
| `status` | `registration_status` (enum) | NO | `'pending'::registration_status` | `RegistrationStatus` | |
| `requested_by_ip` | `inet` | YES | — | `IPv4Address \| IPv6Address \| None` | |
| `reviewed_by` | `uuid` | YES | — | `UUID \| None` | FK → users.id (SET NULL) |
| `reviewed_at` | `timestamp with time zone` | YES | — | `datetime \| None` | |
| `created_at` | `timestamp with time zone` | NO | `now()` | `datetime` | |

**Indexes:** `registration_requests_pkey` (PK), `registration_requests_email_key` (UNIQUE)

### 2.4 Sequences

| Sequence | Owned By | Type |
|---|---|---|
| `aggregated_data_id_seq` | `aggregated_data.id` | bigint |

### 2.5 Triggers

| Trigger | Table | Event | Purpose |
|---|---|---|---|
| `update_dashboards_updated_at` | `dashboards` | BEFORE UPDATE | Auto-set `updated_at = NOW()` |
| `update_graphs_updated_at` | `graphs` | BEFORE UPDATE | Auto-set `updated_at = NOW()` |
| `update_processing_configs_updated_at` | `processing_configs` | BEFORE UPDATE | Auto-set `updated_at = NOW()` |
| `update_users_updated_at` | `users` | BEFORE UPDATE | Auto-set `updated_at = NOW()` |

**Note:** No trigger exists for `layouts` table despite the ORM model having `updated_at` with `onupdate=text("now()")`. The `20260508145000_add_updated_at_to_layouts.py` migration mentions the trigger but doesn't create it. The `ce58bba5d461` migration creates triggers for `['dashboards', 'processing_configs', 'layouts', 'graphs', 'users']` but the real DB only shows 4 triggers (missing `layouts`).

### 2.6 Roles & Permissions

| Role | Type | Notes |
|---|---|---|
| `postgres` | Superuser | Database owner, used by application |
| `pg_database_owner` | System | Owner of `public` schema |

**The application connects as `postgres` superuser.** No separate application-specific roles are created.

---

## 3. Schema Drift Report

| Object | Problem | ORM | Alembic | Real DB | Recommended Source of Truth |
|---|---|---|---|---|---|
| `dashboard_access.permission` column default | ORM sets `default=DashboardPermission.VIEW` with `server_default=text("'view'")`, but real DB has NO default | Has default | `7130ecb0388c` creates column with `permission dashboard_permission_level NOT NULL` (no default) | No default | Alembic (no default) — ORM default is Python-side only, not applied at DB level |
| `dashboards.config` nullable | ORM: `nullable=True`; SPEC.md: `NOT NULL DEFAULT '{}'`; Real DB: `nullable=True` | `nullable=True` | `a1b2c3d4e5f6` adds with `NOT NULL DEFAULT '{}'::jsonb`; `a1e404502aac` drops it; later re-added nullable | `nullable=True` | SPEC.md says NOT NULL — ORM and real DB are inconsistent with SPEC |
| `layouts.updated_at` trigger | ORM has `onupdate=text("now()")`; migration `ce58bba5d461` claims to create trigger for layouts | Has onupdate | Trigger listed in `ce58bba5d461` upgrade | **No trigger on layouts** | Alembic — trigger is missing in real DB |
| `dashboard_filters` redundant index | `idx_dashboard_filters_dashboard_filter` is a duplicate of `dashboard_filters_pkey` (same columns) | ORM defines it explicitly | Created in `7130ecb0388c` | Exists but redundant | ORM — should be removed |
| `aggregated_data` redundant indexes | `idx_aggregated_data_dashboard_id` is covered by `idx_aggregated_data_dashboard_graph` | ORM defines both | Created in `c3cc391beded` | Both exist, one is redundant | ORM — composite index covers single-column prefix |
| `dashboard_access` redundant index | `idx_dashboard_access_user` is covered by `dashboard_access_pkey` (btree on user_id, dashboard_id) | ORM defines it explicitly | Created in `7130ecb0388c` | Exists but redundant | ORM — PK btree covers user_id prefix |
| `graphs` redundant index | `idx_graphs_dashboard` is covered by `idx_graphs_dashboard_name` (composite on dashboard_id, name) | ORM defines both | Created in `c3cc391beded` | Both exist, one is redundant | ORM — composite index covers single-column prefix |
| `users.email` constraint name | ORM uses `unique=True` which would auto-generate `users_email_key`; real DB has `users_email_key` | `unique=True` | `7130ecb0388c` creates `idx_users_email` (renamed in `840a99edb818` back to `users_email_key`) | `users_email_key` | Alembic — final state after rename chain |
| `users.email` CHECK constraint | `users_email_length_check` exists in real DB but is NOT defined in any model or migration explicitly | Not in ORM | Added in `ce58bba5d461` | Exists | Alembic — undocumented constraint |
| `alembic.ini` hardcoded credentials | Contains `postgresql+asyncpg://postgres:1234@localhost:5432/bidb` | N/A | N/A | N/A | Config file — credentials in plain text |
| `uuid-ossp` extension | `create_db.sql` creates it; `bidb_schema.sql` creates it; real DB does NOT have it | N/A | `7130ecb0388c` uses `gen_random_uuid()` not `uuid_generate_v4()` | Not installed | Alembic — `gen_random_uuid()` is native in PG 16 |
| `dashboard_access` FK `ondelete` | ORM: `ForeignKey("users.id", ondelete="CASCADE")` — Real DB: `dashboard_access_user_id_fkey` with CASCADE | CASCADE | CASCADE in `7130ecb0388c` | CASCADE | Consistent |
| `processing_logs.dashboard_id` ondelete | ORM: `ForeignKey("dashboards.id", ondelete="SET NULL")` — Real DB confirms SET NULL | SET NULL | SET NULL in `7130ecb0388c` | SET NULL | Consistent |

---

## 4. Migration Audit

| Check | Status | Notes |
|---|---|---|
| Migration chain completeness | **BROKEN** | Multiple branch points without proper merge; see §4.1 |
| Reproducibility from empty DB | **PARTIAL** | `7130ecb0388c` uses `IF NOT EXISTS` but later migrations use raw `ALTER TABLE` without idempotency guards |
| No broken revisions | **FAIL** | `3f7a1b2c9d0e` has `down_revision = '840a99edb818'` but its `revises` comment says `e86f3c8f7324` — mismatch |
| No circular dependencies | **PASS** | No circular deps detected |
| `alembic upgrade head` on empty DB | **RISKY** | Multiple no-op migrations; redundant index creation attempts; `a1e404502aac` drops and recreates indexes conditionally |
| Rollback safety | **POOR** | Several downgrades use `DROP INDEX IF EXISTS` without specifying index names correctly; `57f43a5c499d` downgrade is a no-op |
| Schema/data migration separation | **PASS** | No data migrations mixed with schema changes |
| Idempotent migrations | **PARTIAL** | Initial migration uses `IF NOT EXISTS`; later migrations use DO blocks for some operations but not all |
| Current head version | `4bfb28b3732d` | Confirmed in real DB |

### 4.1 Migration Chain Analysis

The migration history has **two branch points** that were merged:

```
Branch A: 7130ecb0388c → e86f3c8f7324 (no-op) → 20260507141843 → f50a4054569c (merge)
Branch B: 7130ecb0388c → 57f43a5c499d (no-op) → 2aa835fe1fac → 840a99edb818 → ...
Branch C: 7130ecb0388c → e86f3c8f7324 → 3f7a1b2c9d0e → a1b2c3d4e5f6 → ce58bba5d461 → a1e404502aac → f50a4054569c (merge)
Branch D: ... → 91f5436a3098 → a2b3c4d5e6f7 → 20260508145000 → c3cc391beded → 4bfb28b3732d (HEAD)
```

**Critical issues:**

1. **`3f7a1b2c9d0e` has wrong `down_revision`:** The file header says `Revises: e86f3c8f7324` but the code sets `down_revision = "840a99edb818"`. This creates an inconsistent migration graph.

2. **Duplicate processing_logs index migrations:** Both `3f7a1b2c9d0e` and `4bfb28b3732d` create `idx_processing_logs_dashboard_id` on `processing_logs`. The second one uses a DO block for idempotency, but this is a design smell.

3. **Duplicate unique constraint migrations:** `91f5436a3098` creates `uq_aggregated_data_dashboard_graph_dims`, then `a2b3c4d5e6f7` drops and recreates it. This is a fix-up pattern that should have been a single migration.

4. **`a1e404502aac` is a "god migration":** It creates the `registration_requests` table AND drops/recreates indexes on 6 other tables AND alters columns on 5 tables. This violates single responsibility and makes rollback extremely risky.

5. **`840a99edb818` renames indexes back and forth:** It renames `idx_access_dashboard` → `idx_dashboard_access_dashboard` and `idx_dashboard_filter` → `idx_dashboard_filters_dashboard_filter`, but later migrations (`a1e404502aac`, `c3cc391beded`) recreate the original names. This is index naming churn.

---

## 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|---|---|---|---|
| Production | `bidb` | **SAFE** — separate DSN, `AUTO_MIGRATE=true`, `RECREATE_TEST_DB=false` | LOW |
| Development | `bidb` (main) + `bidb_test` (optional) | **RISKY** — same PostgreSQL instance; `RECREATE_TEST_DB=true` in dev override | MEDIUM |
| Test (Docker) | `bidb_test` | **RISKY** — test compose sets `POSTGRES_DB: bidb_test` but `DatabaseStarter.recreate_test_database()` connects to `postgres` admin DB and drops/create `bidb_test` | MEDIUM |
| Test (local pytest) | `bidb_test` | **RISKY** — conftest.py sets `DATABASE__DBNAME=bidb_test`; if `bidb_test` doesn't exist, tests will fail | MEDIUM |

**Key risks:**
- Test database is created/dropped at runtime by connecting to the `postgres` admin database — requires superuser privileges
- No separate credentials for test vs. production — both use `postgres` superuser
- `conftest.py` hardcodes `DATABASE__PASSWORD = "1234"` — if the real DB uses a different password, tests silently connect to a different database or fail
- The `docker-compose.test.yml` sets `POSTGRES_DB: bidb_test` which means the PostgreSQL container initializes with `bidb_test` as the default DB, but the `postgres` admin DB also exists, allowing cross-database operations

---

## 6. Architectural Problems

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| **CRITICAL** | Security | `postgres` superuser | Application connects as `postgres` superuser for all operations including runtime queries | Any SQL injection or bug can drop databases, modify system catalogs, bypass RLS | Create a dedicated application role with limited privileges (CONNECT, SELECT, INSERT, UPDATE, DELETE on specific tables only) | Principle of least privilege; limits blast radius of any security vulnerability |
| **CRITICAL** | Environment Separation | Test DB credentials | `conftest.py` hardcodes `DATABASE__PASSWORD = "1234"` and `DATABASE__HOST = "localhost"` — if local dev DB uses different credentials, tests may target wrong DB | Tests could accidentally drop/modify the production `bidb` database | Use environment-specific `.env.test` file or pytest-env plugin; never hardcode credentials in source | Prevents accidental data loss in development |
| **HIGH** | Migrations | Migration chain | Multiple branch points, duplicate operations, god migrations (`a1e404502aac`), inconsistent `down_revision` | `alembic upgrade head` may fail on fresh DB; downgrade path is unreliable; future migrations may conflict | Consolidate migrations into a single linear chain; split `a1e404502aac` into focused migrations; fix `3f7a1b2c9d0e` down_revision | Unreliable migrations = unreliable deployments = production incidents |
| **HIGH** | Schema Design | `aggregated_data` table | No partitioning strategy; single table stores all graph data for all dashboards; `dims` and `metrics` are unstructured JSONB | As data grows (millions of rows per dashboard), queries will degrade; JSONB uniqueness constraint on `dims::text` is expensive; no archival strategy | Add `created_at` timestamp for data lifecycle management; consider range partitioning by `dashboard_id` or time; add a data retention policy | This is the highest-growth table; will become the primary bottleneck |
| **HIGH** | Indexing | Redundant indexes | 5 confirmed redundant indexes: `idx_aggregated_data_dashboard_id` (covered by composite), `idx_dashboard_access_user` (covered by PK), `idx_dashboard_filters_dashboard_filter` (covered by PK), `idx_graphs_dashboard` (covered by composite), `idx_aggregated_data_graph_id` (standalone, may be needed for graph-only lookups) | Unnecessary write overhead on every INSERT/UPDATE; wasted disk space; confusion for query planner | Remove `idx_aggregated_data_dashboard_id`, `idx_dashboard_access_user`, `idx_dashboard_filters_dashboard_filter`, `idx_graphs_dashboard`; keep `idx_aggregated_data_graph_id` if graph-only queries exist | Each redundant index adds ~20-50 byte overhead per row on writes |
| **HIGH** | Schema Design | `dashboard_access.permission` default | No database-level default; application must always provide a value | If application code forgets to set permission, INSERT will fail with NOT NULL violation | Add `server_default` in a migration or handle consistently in application code | Silent failures in access control are security-critical |
| **MEDIUM** | Schema Design | `dashboards.config` nullable | SPEC.md says `NOT NULL DEFAULT '{}'` but ORM and real DB have `nullable=True` | Inconsistent behavior; some code paths may expect config to always be dict, others handle None | Align ORM and DB: either make it `NOT NULL DEFAULT '{}'` everywhere or handle None in all service code | Inconsistent nullability causes bugs that are hard to trace |
| **MEDIUM** | Maintainability | Index naming churn | Indexes renamed multiple times across migrations (`idx_access_dashboard` → `idx_dashboard_access_dashboard` → back to `idx_access_dashboard` → `idx_dashboard_access_dashboard`) | Confusion about canonical names; risk of creating duplicate indexes with different names | Establish a naming convention (e.g., `idx_{table}_{column}`) and enforce it; never rename indexes without a compelling reason | Naming consistency reduces cognitive load and prevents duplicate index creation |
| **MEDIUM** | Schema Design | `layouts.updated_at` trigger missing | ORM defines `onupdate=text("now()")` but no database trigger exists for `layouts` table | `updated_at` will NOT auto-update on direct SQL updates; only updates via SQLAlchemy ORM with `onupdate` | Either create the trigger in a migration or remove the `onupdate` from the ORM and handle in application code | Inconsistent behavior between ORM and raw SQL paths |
| **MEDIUM** | Reproducibility | `alembic.ini` hardcoded URL | Contains `postgresql+asyncpg://postgres:1234@localhost:5432/bidb` with real credentials | If committed to VCS, credentials are leaked; developers may accidentally use this instead of env vars | Move to environment variable reference or remove entirely; `env.py` already handles URL override | Credential leakage risk; also causes confusion about which URL is actually used |
| **MEDIUM** | Schema Design | `dashboard_filters` redundant index | `idx_dashboard_filters_dashboard_filter` on `(dashboard_id, filter_id)` is identical to the PRIMARY KEY | Wasted space and write overhead on a junction table that may have many rows | Drop the redundant index; the PK already provides the same coverage | Junction tables for many-to-many often grow large; redundant indexes compound the problem |
| **LOW** | Schema Design | `uuid-ossp` extension | `create_db.sql` creates it, but real DB doesn't have it and doesn't need it (uses `gen_random_uuid()`) | Confusion about which UUID function to use; `create_db.sql` is not aligned with actual migrations | Remove `uuid-ossp` creation from `create_db.sql`; rely on `gen_random_uuid()` (native in PG 13+) | Reduces setup confusion; `uuid-ossp` is legacy |
| **LOW** | Maintainability | `create_db.sql` vs Alembic divergence | `create_db.sql` creates tables with different column types (TEXT vs VARCHAR), different defaults, and different index names than Alembic | Developers may use `create_db.sql` for local setup and get a different schema than production | Either remove `create_db.sql` entirely (use Alembic only) or keep it in sync with the latest Alembic head | Dual schema sources guarantee drift |
| **LOW** | Schema Design | `processing_logs.status` CHECK | Real DB has no CHECK constraint on `processing_logs.status` — it uses the `processing_status` ENUM type which restricts values | None — ENUM type already constrains values | None needed | Documented for completeness |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|
| `aggregated_data` growth | Unbounded growth; single table for all dashboards/graphs; JSONB uniqueness on `dims::text` is O(n) per insert | As rows grow to millions, INSERT with UPSERT (unique index check) will slow down; SELECT with JSONB dims filtering will require GIN index scans; table bloat from frequent updates | Add `created_at` column for data lifecycle; implement archival/purging strategy; consider partitioning by `dashboard_id` hash or range when exceeding 10M rows |
| `processing_logs` growth | No retention enforcement; logs accumulate indefinitely | Table grows without bound; queries for recent logs slow down; backup size increases | The `cleanup_old_logs()` method exists in `starter.py` but is never called automatically; add a scheduled job or trigger it on startup |
| `dashboard_filters` junction table | Redundant index on PK columns | Write amplification on every filter assignment; negligible at small scale but wasteful | Drop redundant index |
| Connection pooling | `pool_size=10, max_overflow=20` with 4 uvicorn workers | Each worker creates its own pool; 4 workers × 30 connections = 120 max connections; PostgreSQL default is 100 | Reduce `pool_size` to 5 and `max_overflow` to 10 per worker, or use PgBouncer as connection pooler |
| JSONB `dims` filtering | GIN index on `dims` supports `@>` (containment) but not equality or prefix matching | Queries filtering by specific dim values may not use the GIN index efficiently; `dims::text` cast in unique index prevents GIN usage for uniqueness | Consider expression indexes for common filter patterns; benchmark GIN vs B-tree on `dims::text` for equality queries |
| `registration_requests` | No index on `status` column | Admin queries filtering by `status = 'pending'` will scan the full table | Add `CREATE INDEX idx_registration_requests_status ON registration_requests(status)` — low cost, high value for admin panel |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|
| Migration history | 16 migrations for a schema that could be 3-4; multiple no-op migrations; branch/merge complexity | Every new developer must understand the full chain; `alembic history` is confusing; risk of migration conflicts | **HIGH** — Squash migrations into a single initial + focused follow-ups after the schema stabilizes |
| Redundant indexes | 4-5 confirmed redundant indexes | Write overhead; confusion; wasted disk | **HIGH** — Remove in a single focused migration |
| `a1e404502aac` god migration | 1 migration that touches 7+ tables | Cannot be safely rolled back; hard to review; mixes concerns | **MEDIUM** — Split into focused migrations when next schema change is needed |
| Hardcoded test credentials | `conftest.py` has `DATABASE__PASSWORD = "1234"` | Environment-dependent test behavior; risk of targeting wrong DB | **HIGH** — Use `.env.test` or environment variable fallback |
| Superuser connection | App uses `postgres` superuser | Security risk; no privilege separation | **HIGH** — Create application-specific role |
| `create_db.sql` drift | Diverged from Alembic schema | Confusion; potential for wrong schema in local dev | **LOW** — Remove or sync with Alembic |
| Missing `layouts` trigger | `updated_at` doesn't auto-update for layouts | Inconsistent behavior | **LOW** — Add trigger or remove `onupdate` from ORM |

---

## 9. Required Architectural Improvements

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| CRITICAL | Security | Database roles | Application uses `postgres` superuser for all DB operations | Any vulnerability grants full database control; violates least privilege | Create `mkobi_app` role with limited grants: `GRANT CONNECT ON DATABASE bidb TO mkobi_app; GRANT USAGE ON SCHEMA public TO mkobi_app; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkobi_app; GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mkobi_app;` | Limits blast radius; required for production deployments; standard security practice |
| CRITICAL | Test Isolation | `conftest.py` credentials | Hardcoded `DATABASE__PASSWORD = "1234"` and `DATABASE__HOST = "localhost"` | Tests may connect to wrong database if local config differs; risk of data loss | Use `os.environ.get("DATABASE__PASSWORD", "1234")` pattern; add a check that `DATABASE__DBNAME` contains `_test` suffix before running destructive operations | Prevents accidental production data modification during test runs |
| HIGH | Migrations | Migration chain | 16 migrations with branches, no-ops, god migrations, and inconsistent `down_revision` | Unreliable `alembic upgrade head` on fresh DB; unmaintainable history | After schema stabilizes, squash to: (1) initial schema, (2) registration_requests addition, (3) any future changes. Fix `3f7a1b2c9d0e` `down_revision` immediately | Clean migration history = reliable deployments = fewer production incidents |
| HIGH | Indexing | Redundant indexes | 4-5 indexes that duplicate PK or composite index coverage | Unnecessary write overhead; confusion for query planner; wasted disk | Create migration to drop: `idx_aggregated_data_dashboard_id`, `idx_dashboard_access_user`, `idx_dashboard_filters_dashboard_filter`, `idx_graphs_dashboard` | Reduces write overhead by ~10-20% on INSERT-heavy tables; simplifies index maintenance |
| HIGH | Schema Design | `aggregated_data` lifecycle | No `created_at` column; no retention policy; unbounded growth | Table will grow indefinitely; queries degrade; backups grow | Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` column; implement scheduled cleanup of old data; consider partitioning when >10M rows | This is the core data table; without lifecycle management, it will become the primary operational burden |
| MEDIUM | Schema Design | `dashboards.config` nullability | ORM says nullable, SPEC says NOT NULL DEFAULT '{}' | Inconsistent behavior; potential None-related bugs | Decide: either make it `NOT NULL DEFAULT '{}'` in DB and ORM, or handle None consistently in all service code. Recommend NOT NULL DEFAULT '{}' per SPEC | Consistency prevents bugs; NOT NULL DEFAULT '{}' is safer for downstream code |
| MEDIUM | Schema Design | `dashboard_access.permission` default | No DB-level default; relies on application code | INSERT without explicit permission value fails | Add `ALTER TABLE dashboard_access ALTER COLUMN permission SET DEFAULT 'view'::dashboard_permission_level;` or ensure application always provides value | Defensive schema design; prevents silent failures |
| MEDIUM | Maintainability | `alembic.ini` credentials | Hardcoded `postgresql+asyncpg://postgres:1234@localhost:5432/bidb` | Credential leakage if file is shared; confusion about which URL is used | Replace with `sqlalchemy.url = %(DATABASE_URL)s` and set `DATABASE_URL` env var, or remove the line entirely since `env.py` overrides it | Security best practice; reduces configuration confusion |
| MEDIUM | Schema Design | `layouts.updated_at` trigger | Missing trigger despite ORM `onupdate` definition | `updated_at` doesn't auto-update on raw SQL updates | Create migration: `CREATE TRIGGER update_layouts_updated_at BEFORE UPDATE ON layouts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();` | Consistent behavior across all tables with `updated_at` |
| LOW | Schema Design | `registration_requests.status` index | No index on `status` column | Admin panel queries filtering by status will scan full table | Add `CREATE INDEX idx_registration_requests_status ON registration_requests(status);` | Low cost index that significantly improves admin panel performance |
| LOW | Reproducibility | `create_db.sql` | Divergent from Alembic; uses different types and index names | Developers may use it and get wrong schema | Remove `create_db.sql` or replace with `alembic upgrade head` documentation | Single source of truth for schema |
| LOW | Schema Design | `uuid-ossp` extension | Referenced in `create_db.sql` but not installed in real DB; not needed | Confusion about UUID generation strategy | Remove `CREATE EXTENSION "uuid-ossp"` from `create_db.sql`; rely on `gen_random_uuid()` | Reduces setup steps; aligns with actual usage |

---

## 10. Async Compatibility Audit

| Check | Status | Notes |
|---|---|---|
| Async DB driver | **PASS** | `asyncpg` used via `postgresql+asyncpg://` scheme |
| Async SQLAlchemy | **PASS** | `create_async_engine` + `AsyncSession` + `async_sessionmaker` |
| Connection lifecycle | **PASS** | `get_session()` context manager ensures proper cleanup |
| Migration async handling | **PASS** | `env.py` uses `asyncio.run(run_async_migrations())` with `NullPool` |
| Blocking calls in async | **WARNING** | `DatabaseStarter._apply_migrations` uses `asyncio.to_thread()` which is correct, but `command.upgrade()` inside it is a long-running blocking operation |
| Pool configuration | **WARNING** | `pool_size=10, max_overflow=20` per engine instance; with 4 uvicorn workers, total connections could reach 120, exceeding PostgreSQL's default `max_connections=100` |
| Session-per-request | **PASS** | `get_db()` generator yields one session per request |
| Transaction handling | **PASS** | `autocommit=False`, `expire_on_commit=False` configured |

---

## 11. Summary of Findings

### Critical Issues (Must Fix Before Production)
1. **Application connects as `postgres` superuser** — create limited-privilege role
2. **Test credentials hardcoded in `conftest.py`** — risk of targeting wrong database

### High Priority (Fix in Next Sprint)
3. **Migration chain is unreliable** — squash and linearize after schema stabilizes
4. **Redundant indexes** — remove 4-5 duplicate indexes
5. **`aggregated_data` has no lifecycle management** — add `created_at` and retention policy

### Medium Priority (Fix When Convenient)
6. **`dashboards.config` nullability inconsistency** — align ORM with SPEC
7. **`dashboard_access.permission` missing DB default** — add `server_default`
8. **`alembic.ini` contains hardcoded credentials** — remove or use env var
9. **Missing `layouts` updated_at trigger** — add trigger

### Low Priority (Technical Debt)
10. **`create_db.sql` diverged from Alembic** — remove or sync
11. **`uuid-ossp` extension not needed** — remove from init scripts
12. **Missing index on `registration_requests.status`** — add for admin panel

---

## 12. Database Health Summary

| Metric | Value | Status |
|---|---|---|
| Invalid indexes | 0 | ✅ |
| Duplicate indexes | 5 | ⚠️ |
| Bloated indexes | 0 | ✅ |
| Connections | 33 total, 0 idle | ✅ |
| Vacuum health | No wraparound danger | ✅ |
| Sequence health | All healthy | ✅ |
| Buffer cache hit (indexes) | 98% | ✅ |
| Buffer cache hit (tables) | 99% | ✅ |
| Invalid constraints | 0 | ✅ |

---

*End of audit report 02.*
