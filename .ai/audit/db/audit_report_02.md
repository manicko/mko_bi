# PostgreSQL Database Audit Report — mkobi BI Dashboard

**Audit Date:** 2026-05-19  
**Report Number:** 02  
**Database Version:** PostgreSQL 16.13  
**Audit Scope:** Schema architecture, drift detection, migration integrity, scalability, maintainability, operational safety  

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | dev/prod | Main application database | `DATABASE_URL` (built from `DATABASE__*` env vars) | Docker volume / manual |
| `bidb_test` | test | Isolated test database | `TEST_DATABASE_URL` (built from `DATABASE__*` + `test_dbname`) | Auto-recreated via `DatabaseStarter.recreate_test_database()` |
| `postgres` | — | Default admin database | — | PostgreSQL default |

**DSN Construction (from `src/mkobi/config.py`):**
- Main: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}` → `bidb`
- Test: Same pattern but `path={test_dbname}` → `bidb_test`

---

## 2. Schema Documentation — `bidb` (Main Database)

### 2.1 Extensions

| Extension | Version | Notes |
|---|---|---|
| `plpgsql` | 1.0 | Built-in, installed by default |
| `uuid-ossp` | — | **Available but NOT installed** — `gen_random_uuid()` used instead (pg13+ native) |

### 2.2 PostgreSQL ENUM Types

| ENUM Type | Values | StrEnum Class | Used In |
|---|---|---|---|
| `user_role` | admin, editor, viewer | `UserRole` | `users.role` |
| `dashboard_permission_level` | view, edit, admin | `DashboardPermission` | `dashboard_access.permission` |
| `graph_type` | bar, line, pie, table | `GraphType` | `graphs.type` |
| `filter_type` | select, multiselect, range, date | `FilterType` | `filters.type` |
| `processing_status` | started, uploaded, processing, success, failed, completed | `ProcessingStatus` | `processing_logs.status` |
| `registration_status` | pending, approved, rejected | `RegistrationStatus` | `registration_requests.status` |

### 2.3 Tables

#### `users`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `email` | VARCHAR(255) | NO | — | UNIQUE |
| `password_hash` | VARCHAR(255) | NO | — | |
| `role` | `user_role` (ENUM) | NO | `'viewer'::user_role` | |
| `is_active` | BOOLEAN | NO | `true` | |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | Trigger-updated |

**Indexes:** `users_pkey` (PK), `idx_users_email` (UNIQUE), `idx_users_role`  
**Triggers:** `update_users_updated_at` (BEFORE UPDATE)

#### `layouts`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `name` | VARCHAR(255) | NO | — | UNIQUE |
| `definition` | JSONB | NO | — | |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | Trigger-updated |

**Indexes:** `layouts_pkey` (PK), `idx_layouts_name` (UNIQUE)  
**Triggers:** `update_layouts_updated_at` (BEFORE UPDATE)

#### `dashboards`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `name` | VARCHAR(255) | NO | — | UNIQUE |
| `description` | TEXT | YES | — | |
| `config` | JSONB | **YES** | — | **See drift #1** |
| `layout_id` | UUID | YES | — | FK → layouts.id (SET NULL) |
| `created_by` | UUID | YES | — | FK → users.id (SET NULL) |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | Trigger-updated |

**Indexes:** `dashboards_pkey` (PK), `idx_dashboards_name` (UNIQUE)  
**Triggers:** `update_dashboards_updated_at` (BEFORE UPDATE)

#### `graphs`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `dashboard_id` | UUID | NO | — | FK → dashboards.id (CASCADE) |
| `name` | VARCHAR(255) | NO | — | |
| `type` | `graph_type` (ENUM) | NO | — | |
| `config` | JSONB | NO | — | |
| `dimensions` | JSONB | NO | — | |
| `metrics` | JSONB | NO | — | |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |

**Indexes:** `graphs_pkey` (PK), `idx_graphs_dashboard_name` (UNIQUE), `idx_graphs_dashboard`  
**Triggers:** `update_graphs_updated_at` (BEFORE UPDATE) — **See drift #4**

#### `filters`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `name` | VARCHAR(255) | NO | — | UNIQUE |
| `type` | `filter_type` (ENUM) | NO | — | |
| `config` | JSONB | NO | — | |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |

**Indexes:** `filters_pkey` (PK), `idx_filters_name` (UNIQUE)

#### `dashboard_access`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `user_id` | UUID | NO | — | FK → users.id (CASCADE), composite PK |
| `dashboard_id` | UUID | NO | — | FK → dashboards.id (CASCADE), composite PK |
| `permission` | `dashboard_permission_level` (ENUM) | NO | — | **See drift #2** |

**Indexes:** `dashboard_access_pkey` (PK composite), `idx_dashboard_access_user`, `idx_dashboard_access_dashboard`

#### `dashboard_filters` (many-to-many junction)

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `dashboard_id` | UUID | NO | — | FK → dashboards.id (CASCADE), composite PK |
| `filter_id` | UUID | NO | — | FK → filters.id (CASCADE), composite PK |

**Indexes:** `dashboard_filters_pkey` (PK composite), `idx_dashboard_filters_dashboard_filter`

#### `processing_configs`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `dashboard_id` | UUID | NO | — | FK → dashboards.id (CASCADE), PK |
| `settings` | JSONB | NO | — | |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | Trigger-updated |

**Indexes:** `processing_configs_pkey` (PK)  
**Triggers:** `update_processing_configs_updated_at` (BEFORE UPDATE)

#### `aggregated_data`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | BIGINT | NO | `nextval('aggregated_data_id_seq')` | PK, BIGSERIAL |
| `dashboard_id` | UUID | NO | — | FK → dashboards.id (CASCADE) |
| `graph_id` | UUID | NO | — | FK → graphs.id (CASCADE) |
| `dims` | JSONB | NO | — | GIN-indexed |
| `metrics` | JSONB | NO | — | |

**Indexes:** `aggregated_data_pkey` (PK), `idx_aggregated_data_dashboard_id`, `idx_aggregated_data_graph_id`, `idx_aggregated_data_dims_gin` (GIN), `uq_aggregated_data_dashboard_graph_dims` (UNIQUE on dashboard_id, graph_id, dims)  
**Sequence:** `aggregated_data_id_seq` (START 1, INCREMENT 1, MAX 9223372036854775807)

#### `processing_logs`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `dashboard_id` | UUID | YES | — | FK → dashboards.id (SET NULL) |
| `status` | `processing_status` (ENUM) | NO | — | |
| `message` | VARCHAR(1000) | YES | — | |
| `started_at` | TIMESTAMPTZ | YES | — | |
| `finished_at` | TIMESTAMPTZ | YES | — | |

**Indexes:** `processing_logs_pkey` (PK), `idx_processing_logs_dashboard_id`

#### `registration_requests`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `email` | VARCHAR(255) | NO | — | UNIQUE |
| `status` | `registration_status` (ENUM) | NO | `'pending'::registration_status` | |
| `requested_by_ip` | INET | YES | — | |
| `reviewed_by` | UUID | YES | — | FK → users.id (SET NULL) |
| `reviewed_at` | TIMESTAMPTZ | YES | — | |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |

**Indexes:** `registration_requests_pkey` (PK), `registration_requests_email_key` (UNIQUE)

#### `alembic_version` (Alembic internal)

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `version_num` | VARCHAR(32) | NO | — | PK |

**Current revision:** `7130ecb0388c`

### 2.4 Triggers

| Trigger | Table | Timing | Event |
|---|---|---|---|
| `update_users_updated_at` | users | BEFORE UPDATE | `EXECUTE FUNCTION update_updated_at_column()` |
| `update_layouts_updated_at` | layouts | BEFORE UPDATE | `EXECUTE FUNCTION update_updated_at_column()` |
| `update_dashboards_updated_at` | dashboards | BEFORE UPDATE | `EXECUTE FUNCTION update_updated_at_column()` |
| `update_graphs_updated_at` | graphs | BEFORE UPDATE | `EXECUTE FUNCTION update_updated_at_column()` |
| `update_processing_configs_updated_at` | processing_configs | BEFORE UPDATE | `EXECUTE FUNCTION update_updated_at_column()` |

**Trigger Function:** `update_updated_at_column()` — `LANGUAGE plpgsql`, sets `NEW.updated_at = NOW()`

### 2.5 Foreign Key Cascade Behavior

| Parent | Child | On Delete | On Update |
|---|---|---|---|
| dashboards | graphs | CASCADE | NO ACTION |
| dashboards | aggregated_data | CASCADE | NO ACTION |
| dashboards | dashboard_access | CASCADE | NO ACTION |
| dashboards | dashboard_filters | CASCADE | NO ACTION |
| dashboards | processing_configs | CASCADE | NO ACTION |
| dashboards | processing_logs | **SET NULL** | NO ACTION |
| dashboards | layouts (via layout_id) | **SET NULL** | NO ACTION |
| dashboards | users (via created_by) | **SET NULL** | NO ACTION |
| graphs | aggregated_data | CASCADE | NO ACTION |
| filters | dashboard_filters | CASCADE | NO ACTION |
| users | dashboard_access | CASCADE | NO ACTION |
| users | registration_requests (via reviewed_by) | **SET NULL** | NO ACTION |

### 2.6 Roles & Permissions

| Role | Superuser | Create Role | Create DB | Can Login | Notes |
|---|---|---|---|---|---|
| `postgres` | Yes | Yes | Yes | Yes | **Only role — used for everything** |

---

## 3. Schema Drift Report

| # | Object | Problem | ORM | Alembic Migration | Real DB (bidb) | `create_db.sql` | Recommended Source of Truth |
|---|---|---|---|---|---|---|---|
| 1 | `dashboards.config` | **NULLABLE mismatch** | `Mapped[dict[str, Any] \| None]`, `nullable=True` | `config JSONB` (nullable, no NOT NULL) | `is_nullable = YES` | `config JSONB NOT NULL DEFAULT '{}'` | **ORM + Alembic + Real DB agree**; `create_db.sql` is outdated |
| 2 | `dashboard_access.permission` | **Missing server_default** | `server_default=text("'view'")` | `permission dashboard_permission_level NOT NULL` (no default) | `column_default = NULL` | `permission TEXT NOT NULL CHECK (...)` (no default) | **Drift: ORM expects default, but none exists in DB or migration** |
| 3 | `users.updated_at` trigger | **Trigger exists but ORM also has `onupdate`** | `onupdate=text("now()")` + trigger | Trigger created | Both trigger and `onupdate` exist | No `updated_at` column at all | **Redundancy: trigger + onupdate both set updated_at** |
| 4 | `graphs.updated_at` | **Column + trigger exist but ORM has no `updated_at`** | No `updated_at` column in ORM model | `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` only | `update_graphs_updated_at` trigger exists but **no `updated_at` column** | No `updated_at` column | **Drift: trigger references non-existent column** |
| 5 | `layouts.updated_at` | **Trigger exists but ORM also has `onupdate`** | `onupdate=text("now()")` + trigger | Trigger created | Both exist | No `updated_at` column | **Redundancy: same as #3** |
| 6 | `processing_logs.status` | **ENUM value mismatch** | `ProcessingStatus` has 6 values (started, uploaded, processing, success, failed, completed) | 6 values in migration | 6 values in real DB | Only 3 values (started, success, failed) | `create_db.sql` is outdated |
| 7 | `processing_logs.dashboard_id` | **FK behavior mismatch** | `ondelete="SET NULL"` | `ON DELETE SET NULL` | `confdeltype = 'n'` (SET NULL) | `dashboard_id UUID REFERENCES dashboards(id)` (NO cascade/set null) | `create_db.sql` is outdated |
| 8 | `users.email` | **Type mismatch** | `String(255)` | `VARCHAR(255)` | `VARCHAR(255)` | `TEXT` | `create_db.sql` is outdated |
| 9 | `uuid-ossp` extension | **Not installed, but `create_db.sql` requires it** | N/A | Not used (uses `gen_random_uuid()`) | Not installed | `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` | **Not needed — `gen_random_uuid()` is native in PG13+** |
| 10 | `aggregated_data` unique index | **Migration casts dims::text, real DB doesn't** | `text("dims::text")` in UniqueIndex | `dims::text` in unique index | Index on `(dashboard_id, graph_id, dims)` — **no cast to text** | No such index | **Drift: unique index in real DB doesn't match migration** |
| 11 | `dashboard_access.permission` | **ORM has server_default, migration doesn't, real DB doesn't** | `server_default=text("'view'")` | No default | No default | No default | **Drift: ORM expects default value but DB has none** |
| 12 | `bidb_test` database | **Empty — no schema applied** | N/A | N/A | 0 tables, 0 enums, 0 triggers | N/A | **Test DB is not auto-populated** |

---

## 4. Migration Audit

| Check | Status | Notes |
|---|---|---|
| Single migration file | ✅ PASS | Only one migration: `7130ecb0388c` |
| Chain integrity | ✅ PASS | Single revision, no chain issues |
| `down_revision = None` | ✅ PASS | Correct for initial migration |
| Idempotent ENUM creation | ✅ PASS | Uses `checkfirst=True` |
| Idempotent table creation | ✅ PASS | Uses `CREATE TABLE IF NOT EXISTS` |
| Idempotent index creation | ✅ PASS | Uses `CREATE INDEX IF NOT EXISTS` |
| Idempotent trigger creation | ⚠️ PARTIAL | Uses `DROP TRIGGER IF EXISTS` + `DO $$` block, but trigger function is recreated with `CREATE OR REPLACE` |
| Downgrade correctness | ✅ PASS | Drops triggers, function, tables, and ENUMs in correct order |
| Reproducibility from scratch | ⚠️ ISSUE | See finding #1 below |
| No circular dependencies | ✅ PASS | Single revision |
| No mixed schema/data migrations | ✅ PASS | Only schema |
| `compare_type = True` in env.py | ✅ PASS | Enabled in both offline and online modes |

### Migration Issues Detected

1. **`dashboards.config` NOT NULL removed without migration**: The `create_db.sql` had `config JSONB NOT NULL DEFAULT '{}'`, but the Alembic migration has `config JSONB` (nullable). The real DB matches the migration (nullable). This is a silent schema change — no Alembic revision was generated to reflect the change from the original `create_db.sql`.

2. **`graphs.updated_at` trigger without column**: The migration creates `update_graphs_updated_at` trigger on `graphs`, but the `graphs` table has no `updated_at` column. The trigger function sets `NEW.updated_at = NOW()` which would fail on UPDATE. This is a **latent bug** — the trigger exists but will error if fired.

3. **`dashboard_access.permission` server_default drift**: ORM declares `server_default=text("'view'")` but the migration doesn't include a DEFAULT clause. The real DB has no default. This means INSERT via raw SQL without specifying `permission` will fail (NOT NULL constraint), while ORM inserts work fine (ORM provides the default).

---

## 5. Environment Isolation Audit

| Environment | Database | Isolation Status | Risk |
|---|---|---|---|
| Development | `bidb` | ✅ Isolated | Uses `DATABASE__DBNAME=bidb` |
| Test | `bidb_test` | ✅ Physically separate database | Uses `DATABASE__DBNAME=bidb_test` + `DATABASE__TEST_DBNAME=bidb_test` |
| Production | `bidb` | ⚠️ Same DB name as dev | Relies on Docker/env separation |

### Test Isolation Details

| Check | Status | Notes |
|---|---|---|
| Separate physical database | ✅ PASS | `bidb_test` ≠ `bidb` |
| Separate DSN | ✅ PASS | `TEST_DATABASE_URL` constructed with `test_dbname` |
| Test DB recreation | ✅ PASS | `RECREATE_TEST_DB=true` drops + recreates `bidb_test` |
| Migration applied to test DB | ✅ PASS | `_apply_migrations(test_url)` called after recreation |
| SAVEPOINT rollback per test | ✅ PASS | `async_db_session` fixture uses `session.begin_nested()` + rollback |
| NullPool for test engine | ✅ PASS | Prevents connection pooling issues |
| No prod access from test | ✅ PASS | Separate database, separate connection |
| Test DB is empty on cold start | ⚠️ ISSUE | `bidb_test` has no schema until test suite runs `setup_test_database` |

### Test Isolation Verdict: **SAFE** (with caveats)

The test database is physically separate and uses SAVEPOINT rollback. The `bidb_test` database starts empty and is populated by the test fixture. No risk of test data leaking into `bidb`.

**Caveat:** The `bidb_test` database persists between test runs if `RECREATE_TEST_DB` is not set. In CI/docker-compose.test.yml, it is set to `"true"`.

---

## 6. Architectural Problems

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| **CRITICAL** | Schema Design | `graphs` table | `update_graphs_updated_at` trigger exists but `graphs` has no `updated_at` column | Any UPDATE on `graphs` will fail with `column "updated_at" of relation "graphs" does not exist` | Remove the trigger: `DROP TRIGGER IF EXISTS update_graphs_updated_at ON graphs;` | This is a latent runtime bug. The first UPDATE to any graph row will crash. |
| **HIGH** | Schema Drift | `dashboard_access.permission` | ORM has `server_default=text("'view'")` but migration and real DB have no default | Raw SQL INSERT without `permission` value will violate NOT NULL constraint | Add `DEFAULT 'view'::dashboard_permission_level` to the column in a new migration, OR remove `server_default` from ORM | Inconsistency between ORM expectation and DB reality. Any bypass of ORM (manual SQL, data migration, bulk insert) will fail. |
| **HIGH** | Schema Drift | `dashboards.config` | `create_db.sql` says `NOT NULL DEFAULT '{}'`, but migration, ORM, and real DB all say nullable | `create_db.sql` is not the source of truth and cannot be used to recreate the schema | Delete or update `create_db.sql` to match the Alembic migration | Having a divergent `create_db.sql` creates confusion about the actual schema. New developers may use it to set up local DB and get different constraints. |
| **MEDIUM** | Maintainability | `users.updated_at`, `layouts.updated_at`, `dashboards.updated_at`, `processing_configs.updated_at` | Both trigger and `onupdate` set `updated_at` redundantly | No runtime failure, but confusing — which mechanism is authoritative? | Choose one mechanism. Recommended: keep triggers (DB-level, works for raw SQL), remove `onupdate=text("now()")` from ORM | Redundancy creates maintenance burden. Future developers won't know which mechanism to modify. |
| **MEDIUM** | Security | `postgres` role | Application uses superuser `postgres` for all operations (runtime + migrations) | Any SQL injection or application bug can execute superuser operations | Create a dedicated application role with limited privileges (CONNECT, SELECT, INSERT, UPDATE, DELETE on specific tables only) | Violates least-privilege principle. Superuser can drop databases, modify system catalogs, bypass RLS. |
| **MEDIUM** | Reproducibility | `create_db.sql` | Diverges from actual schema in 6+ ways (see drift report) | Cannot be used to bootstrap a new environment | Remove `create_db.sql` or replace with `pg_dump` of the actual schema | Misleading documentation that doesn't match reality. |
| **MEDIUM** | Indexing | `aggregated_data` unique index | Migration specifies `dims::text` cast but real DB index doesn't include the cast | Unique constraint may not work as intended for JSONB comparison | Verify the unique index behavior. If JSONB equality comparison is needed, the index should use `dims::text` or a expression index | The ORM model defines a unique index with `text("dims::text")` but the migration's `CREATE UNIQUE INDEX` doesn't include the cast. Real DB matches migration (no cast). |
| **LOW** | Schema Drift | `uuid-ossp` extension | `create_db.sql` creates it, but it's not installed and not needed | None — `gen_random_uuid()` is native | Remove `CREATE EXTENSION "uuid-ossp"` from `create_db.sql` | Dead code that creates confusion |
| **LOW** | Maintainability | `bidb_schema.sql` | File appears to be a pg_dump with encoding corruption (UTF-16 BOM + binary prefix) | Cannot be used for schema reference | Regenerate with `pg_dump --schema-only --no-owner` or remove | Unreadable file in the repository |
| **LOW** | Naming | Index naming convention | Mixed naming: `idx_<table>_<col>` vs `uq_<table>_<col>` vs `<table>_pkey` | None | Standardize: `idx_<table>_<col>` for regular indexes, `uq_<table>_<col>` for unique, `<table>_pkey` for PK | Minor inconsistency, but current names are functional |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|
| `aggregated_data` | Unbounded growth — each upload × graphs × dimension combinations adds rows | Table bloat, slow aggregation queries, GIN index degradation | Implement data retention policy (e.g., keep only latest N uploads per dashboard). Consider partitioning by `dashboard_id` when table exceeds ~10M rows. |
| `processing_logs` | Unbounded growth — every processing operation creates a log row | Table bloat, slow log queries | The `cleanup_old_logs()` method exists in `DatabaseStarter` but is **never called** from the application lifecycle. Wire it into the startup or a periodic task. |
| `aggregated_data` GIN index on `dims` | GIN indexes are expensive to maintain on high-write tables | INSERT/UPDATE degradation as table grows | Monitor GIN index size. Consider `gin_pending_list_limit` tuning. |
| `aggregated_data` unique index on `(dashboard_id, graph_id, dims)` | JSONB equality in unique index is expensive | INSERT performance degradation | The unique index prevents duplicate aggregation data but uses JSONB comparison. Consider hashing dims to a separate column and indexing that instead. |
| `registration_requests` | Grows indefinitely with user signup requests | Minor — low write volume | Archive rejected/approved requests older than 90 days. |
| Connection pool | `pool_size=10, max_overflow=20` in production | Under high concurrency, connections may exhaust | Monitor `pg_stat_activity`. Consider PgBouncer for connection pooling at scale. |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|
| `create_db.sql` | Divergent from actual schema | Confusion, cannot be used for bootstrapping | **HIGH** — Remove or regenerate |
| `graphs` trigger on non-existent column | Latent runtime bug | First UPDATE to graphs will crash | **CRITICAL** — Fix immediately |
| `dashboard_access.permission` server_default drift | ORM/DB mismatch | Raw SQL inserts fail | **HIGH** — Align ORM with DB or add DB default |
| Redundant `updated_at` mechanisms | Trigger + onupdate | Maintenance confusion | **MEDIUM** — Choose one |
| Superuser `postgres` for app | Security risk | Full DB access on any injection | **MEDIUM** — Create limited role |
| `cleanup_old_logs()` never called | Log table grows unbounded | Table bloat | **MEDIUM** — Wire into lifecycle |
| `bidb_schema.sql` encoding | Corrupted file | Cannot be used | **LOW** — Remove or regenerate |
| Single migration file | All schema in one revision | Hard to track history as schema evolves | **LOW** — Acceptable for current stage |

---

## 9. Required Architectural Improvements

### Critical (Fix Immediately)

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| CRITICAL | Schema Design | `graphs` table | `update_graphs_updated_at` trigger references non-existent `updated_at` column | UPDATE on any graph row will throw `column "updated_of" does not exist` | `DROP TRIGGER update_graphs_updated_at ON graphs;` | This will cause a runtime crash on the first graph update via API or any direct SQL UPDATE. |

### High (Fix in Current Sprint)

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| HIGH | Schema Drift | `dashboard_access.permission` | ORM declares `server_default` but DB has none | Any INSERT bypassing ORM (raw SQL, migration, admin tool) without explicit `permission` value will fail with NOT NULL violation | Add `DEFAULT 'view'::dashboard_permission_level` via `ALTER TABLE` in a new Alembic migration | Inconsistency between code and DB creates hidden failure modes. |
| HIGH | Reproducibility | `create_db.sql` | Diverges from actual schema in 6+ places | Cannot be used to bootstrap new environments; misleading to developers | Delete `create_db.sql` or replace with `pg_dump --schema-only` output | A divergent init script is worse than no init script — it creates false confidence. |
| HIGH | Schema Drift | `aggregated_data` unique index | ORM model has `text("dims::text")` in unique index, migration doesn't, real DB doesn't | Unique constraint may not prevent JSONB duplicates correctly | Add a new Alembic migration to drop and recreate the unique index with `dims::text` expression, OR remove the cast from the ORM model | The unique index is meant to prevent duplicate aggregation data. If JSONB comparison doesn't work as expected, duplicates will accumulate. |

### Medium (Plan for Next Iteration)

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| MEDIUM | Maintainability | `users`, `layouts`, `dashboards`, `processing_configs` | Both trigger and `onupdate=text("now()")` set `updated_at` | No runtime failure, but confusing for maintenance | Remove `onupdate=text("now()")` from ORM models; keep DB triggers as the single mechanism | Single source of truth for `updated_at` behavior. Triggers also protect raw SQL updates. |
| MEDIUM | Security | `postgres` role | Application uses superuser for all DB operations | SQL injection or app bug can execute destructive operations | Create `mkobi_app` role with limited grants: `GRANT CONNECT ON DATABASE bidb TO mkobi_app; GRANT USAGE ON SCHEMA public TO mkobi_app; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkobi_app; GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mkobi_app;` | Limits blast radius of any security vulnerability. |
| MEDIUM | Operational | `processing_logs` | `cleanup_old_logs()` exists but is never invoked | Table grows indefinitely, consuming disk and slowing queries | Add `await starter.cleanup_old_logs()` to the startup lifecycle or create a scheduled task | Prevents unbounded table growth. The code is already written — it just needs to be called. |
| MEDIUM | Schema Drift | `dashboards.config` | `create_db.sql` says `NOT NULL DEFAULT '{}'`, but actual schema is nullable | Confusion about whether `config` can be NULL | Update `create_db.sql` to match: `config JSONB` (nullable) | Aligns documentation with reality. |

### Low (Technical Debt — Address When Convenient)

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| LOW | Maintainability | `bidb_schema.sql` | File has encoding corruption (UTF-16 BOM) | Cannot be read or used | Remove or regenerate with `pg_dump --schema-only --no-owner -f bidb_schema.sql` | Clean repository. |
| LOW | Schema Drift | `uuid-ossp` | Referenced in `create_db.sql` but not installed and not needed | None | Remove from `create_db.sql` | `gen_random_uuid()` is native in PostgreSQL 13+. |

---

## 10. Summary

### What Works Well

1. **Clean single-migration architecture** — One initial migration with proper `checkfirst=True` for ENUMs and `IF NOT EXISTS` for tables/indexes.
2. **Proper ENUM usage** — All fixed-value columns use PostgreSQL ENUMs backed by Python `StrEnum` classes.
3. **TIMESTAMPTZ everywhere** — All timestamp columns use `timestamp with time zone`.
4. **JSONB (not JSON/TEXT)** — All flexible data columns use JSONB.
5. **Test isolation** — Separate `bidb_test` database with SAVEPOINT rollback per test.
6. **Async throughout** — `asyncpg` driver, async SQLAlchemy sessions, async engine.
7. **Consistent UUID PKs** — All entity tables use UUID PKs; only `aggregated_data` uses BIGSERIAL (intentional).
8. **CASCADE behavior** — Well-defined FK cascade rules matching the domain model.

### What Needs Immediate Attention

1. **`graphs` trigger bug** — Will crash on first UPDATE. Drop the trigger now.
2. **`dashboard_access.permission` default** — Align ORM with DB or add DB default.
3. **`create_db.sql` divergence** — Remove or regenerate.

### What Should Be Monitored

1. **`aggregated_data` growth** — Implement retention policy before table exceeds millions of rows.
2. **`processing_logs` growth** — Wire up `cleanup_old_logs()`.
3. **Connection pool sizing** — Monitor under production load.

---

*Audit completed. All findings based on direct inspection of ORM models (`src/mkobi/db/models/`), Alembic migration (`alembic/versions/`), configuration (`src/mkobi/config.py`, `.env`, `docker-compose*.yml`), test fixtures (`tests/conftest.py`), and live PostgreSQL `bidb` database.*
