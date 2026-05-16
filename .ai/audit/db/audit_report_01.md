# Database Architecture Audit Report — mkobi BI Dashboard

**Date:** 2026-05-16  
**Auditor:** OWL (Architecture Audit Agent)  
**Scope:** PostgreSQL database architecture, schema lifecycle, reproducibility  
**Databases audited:** `bidb` (main), `bidb_test` (test)

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | dev / prod / staging | Main application database | `DATABASE__DBNAME=bidb` (constructed to `postgresql+asyncpg://postgres:{password}@host:5432/bidb`) | Docker Compose `POSTGRES_DB: bidb` env var; auto-created by PostgreSQL init; migrations applied via Alembic on app startup when `AUTO_MIGRATE=true` |
| `bidb_test` | test / dev | Test database (pytest) | `DATABASE__TEST_DBNAME=bidb_test` (constructed to `postgresql+asyncpg://postgres:{password}@host:5432/bidb_test`) | Created/dropped at runtime by `DatabaseStarter.recreate_test_database()` when `RECREATE_TEST_DB=true`; migrations applied via Alembic |

**DSN Construction:** The application never uses a raw `DATABASE_URL` environment variable. The URL is always constructed from nested `DATABASE__*` settings (`DATABASE__HOST`, `DATABASE__PORT`, `DATABASE__USER`, `DATABASE__PASSWORD`, `DATABASE__DBNAME`) via `PostgresDsn.build(scheme="postgresql+asyncpg", ...)`.

**Key observation:** The `alembic.ini` file contains a hardcoded default URL (`postgresql+asyncpg://postgres:1234@localhost:5432/bidb`), but `env.py` overrides it from the application config at runtime.

---

## 2. Schema Documentation — `bidb` (Main Database)

### 2.1 Extensions

| Extension | Version | Purpose |
|---|---|---|
| `plpgsql` | 1.0 | PL/pgSQL procedural language (system) |

**Note:** The `uuid-ossp` extension is NOT installed in the real database despite being created in `create_db.sql` and the initial migration using `uuid_generate_v4()`. The real database uses `gen_random_uuid()` (built-in to PostgreSQL 13+) instead. This is a schema drift item.

### 2.2 Custom Types (Enums)

| Type | Values |
|---|---|
| `user_role` | `admin`, `editor`, `viewer` |
| `dashboard_permission_level` | `view`, `edit`, `admin` |
| `graph_type` | `bar`, `line`, `pie`, `table` |
| `filter_type` | `select`, `multiselect`, `range`, `date` |
| `processing_status` | `started`, `uploaded`, `processing`, `success`, `failed`, `completed` |
| `registration_status` | `pending`, `approved`, `rejected` |

### 2.3 Tables

#### `users`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` | PK |
| `email` | VARCHAR(255) | NO | — | UNIQUE |
| `password_hash` | VARCHAR(255) | NO | — | |
| `role` | `user_role` (enum) | NO | `'viewer'::user_role` | |
| `is_active` | BOOLEAN | NO | `true` | |
| `created_at` | TIMESTAMPTZ | NO | `now()` | |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | |

**Constraints:** PK(`id`), UNIQUE(`email`), CHECK(`length(email) <= 255`)  
**Indexes:** `users_pkey` (PK), `users_email_key` (unique), `ix_users_role` (btree on role)  
**Triggers:** `update_users_updated_at` (BEFORE UPDATE → `update_updated_at_column()`)

#### `layouts`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` |
| `name` | VARCHAR(255) | NO | — |
| `definition` | JSONB | NO | — |
| `created_at` | TIMESTAMPTZ | NO | `now()` |
| `updated_at` | TIMESTAMPTZ | NO | `now()` |

**Constraints:** PK(`id`), UNIQUE(`name`)  
**Indexes:** `layouts_pkey`, `layouts_name_key`  
**Triggers:** None in real DB (ORM model has `onupdate` but no trigger was created for layouts)

#### `dashboards`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` |
| `name` | VARCHAR(255) | NO | — |
| `description` | TEXT | YES | — |
| `layout_id` | UUID | YES | — |
| `created_by` | UUID | YES | — |
| `created_at` | TIMESTAMPTZ | NO | `now()` |
| `updated_at` | TIMESTAMPTZ | NO | `now()` |
| `config` | JSONB | YES | `'{}'::jsonb` |

**Constraints:** PK(`id`), UNIQUE(`name`), FK(`layout_id` → `layouts.id` SET NULL), FK(`created_by` → `users.id` SET NULL)  
**Indexes:** `dashboards_pkey`, `dashboards_name_key`  
**Triggers:** `update_dashboards_updated_at`

#### `graphs`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` |
| `dashboard_id` | UUID | NO | — |
| `name` | VARCHAR(255) | NO | — |
| `type` | `graph_type` (enum) | NO | — |
| `config` | JSONB | NO | — |
| `dimensions` | JSONB | NO | — |
| `metrics` | JSONB | NO | — |
| `created_at` | TIMESTAMPTZ | NO | `now()` |

**Constraints:** PK(`id`), UNIQUE(`dashboard_id`, `name`), FK(`dashboard_id` → `dashboards.id` CASCADE)  
**Indexes:** `graphs_pkey`, `idx_graphs_dashboard_name` (unique), `idx_graphs_dashboard`  
**Triggers:** `update_graphs_updated_at`

#### `filters`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` |
| `name` | VARCHAR(255) | NO | — |
| `type` | `filter_type` (enum) | NO | — |
| `config` | JSONB | NO | — |
| `created_at` | TIMESTAMPTZ | NO | `now()` |

**Constraints:** PK(`id`), UNIQUE(`name`)  
**Indexes:** `filters_pkey`, `filters_name_key`

#### `dashboard_access`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `user_id` | UUID | NO | — |
| `dashboard_id` | UUID | NO | — |
| `permission` | `dashboard_permission_level` (enum) | NO | — |

**Constraints:** PK(`user_id`, `dashboard_id`), FK(`user_id` → `users.id` CASCADE), FK(`dashboard_id` → `dashboards.id` CASCADE)  
**Indexes:** `dashboard_access_pkey`, `idx_dashboard_access_user`, `idx_dashboard_access_dashboard`

#### `dashboard_filters`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `dashboard_id` | UUID | NO | — |
| `filter_id` | UUID | NO | — |

**Constraints:** PK(`dashboard_id`, `filter_id`), FK(`dashboard_id` → `dashboards.id` CASCADE), FK(`filter_id` → `filters.id` CASCADE)  
**Indexes:** `dashboard_filters_pkey`, `idx_dashboard_filters_dashboard_filter`

#### `processing_configs`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `dashboard_id` | UUID | NO | — |
| `settings` | JSONB | NO | — |
| `updated_at` | TIMESTAMPTZ | NO | `now()` |

**Constraints:** PK(`dashboard_id`), FK(`dashboard_id` → `dashboards.id` CASCADE)  
**Indexes:** `processing_configs_pkey`  
**Triggers:** `update_processing_configs_updated_at`

#### `aggregated_data`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | BIGINT | NO | `nextval('aggregated_data_id_seq')` |
| `dashboard_id` | UUID | NO | — |
| `graph_id` | UUID | NO | — |
| `dims` | JSONB | NO | — |
| `metrics` | JSONB | NO | — |

**Constraints:** PK(`id`), FK(`dashboard_id` → `dashboards.id` CASCADE), FK(`graph_id` → `graphs.id` CASCADE)  
**Indexes:** `aggregated_data_pkey`, `idx_aggregated_data_dashboard_id`, `idx_aggregated_data_graph_id`, `idx_aggregated_data_dashboard_graph`, `idx_aggregated_data_dims_gin` (GIN), `uq_aggregated_data_dashboard_graph_dims` (unique on `dashboard_id, graph_id, (dims::text)`)

#### `processing_logs`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` |
| `dashboard_id` | UUID | YES | — |
| `status` | `processing_status` (enum) | NO | — |
| `message` | VARCHAR(1000) | YES | — |
| `started_at` | TIMESTAMPTZ | YES | — |
| `finished_at` | TIMESTAMPTZ | YES | — |

**Constraints:** PK(`id`), FK(`dashboard_id` → `dashboards.id` SET NULL)  
**Indexes:** `processing_logs_pkey`, `idx_processing_logs_dashboard_id`

#### `registration_requests`
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | UUID | NO | `gen_random_uuid()` |
| `email` | VARCHAR(255) | NO | — |
| `status` | `registration_status` (enum) | NO | `'pending'::registration_status` |
| `requested_by_ip` | INET | YES | — |
| `reviewed_by` | UUID | YES | — |
| `reviewed_at` | TIMESTAMPTZ | YES | — |
| `created_at` | TIMESTAMPTZ | NO | `now()` |

**Constraints:** PK(`id`), UNIQUE(`email`), FK(`reviewed_by` → `users.id` SET NULL)  
**Indexes:** `registration_requests_pkey`, `registration_requests_email_key`

### 2.4 Sequences

| Sequence | Owned By |
|---|---|
| `aggregated_data_id_seq` | `aggregated_data.id` |

### 2.5 Triggers

| Trigger | Table | Timing | Event | Function |
|---|---|---|---|---|
| `update_users_updated_at` | `users` | BEFORE | UPDATE | `update_updated_at_column()` |
| `update_dashboards_updated_at` | `dashboards` | BEFORE | UPDATE | `update_updated_at_column()` |
| `update_graphs_updated_at` | `graphs` | BEFORE | UPDATE | `update_updated_at_column()` |
| `update_processing_configs_updated_at` | `processing_configs` | BEFORE | UPDATE | `update_updated_at_column()` |

**Missing trigger:** `layouts` table has no `update_layouts_updated_at` trigger despite the ORM model defining `updated_at` with `onupdate`. The migration `ce58bba5d461` lists `layouts` in `tables_with_updated_at` but the trigger was not created in the real DB.

### 2.6 Roles & Permissions

| Role | Database | Notes |
|---|---|---|
| `postgres` | superuser | Owner of all tables; used by the application at runtime |

**Critical finding:** The application connects as `postgres` (superuser) for all operations including runtime. There is no separation of privileges.

---

## 3. Schema Drift Report

| # | Object | Problem | ORM | Alembic (head) | Real DB | Recommended Source of Truth |
|---|---|---|---|---|---|---|
| 1 | `users.updated_at` | ORM has `nullable=False` but migration `20260507141843` adds it as `nullable=True` with `server_default` | `nullable=False, server_default=now()` | `nullable=True, server_default=now()` | `nullable=False, server_default=now()` | **Real DB** — the column was likely altered by a later migration or manually. ORM is correct for the target state. |
| 2 | `users.updated_at` trigger | Migration `ce58bba5d461` creates `update_users_updated_at` trigger | Has `onupdate=text("now()")` in ORM | Trigger created | Trigger exists | **Consistent** |
| 3 | `layouts.updated_at` trigger | Migration `ce58bba5d461` lists `layouts` in trigger creation loop, but `20260508145000` adds `updated_at` column AFTER triggers were created | Has `onupdate=text("now()")` in ORM | Trigger should exist per `ce58bba5d461` | **Trigger MISSING** | **Alembic** — the trigger creation in `ce58bba5d461` ran before the column existed in `20260508145000`, so it was silently skipped or the column didn't exist yet |
| 4 | `layouts.updated_at` column | Added by migration `20260508145000` | `nullable=False, server_default=now()` | `nullable=False, server_default=now()` | `nullable=False, server_default=now()` | **Consistent** |
| 5 | `dashboards.config` | Added/removed/added across migrations (`a1b2c3d4e5f6` adds, `a1e404502aac` drops, `c3cc391beded` re-adds) | `nullable=True` | Added by `c3cc391beded` | `nullable=True, default='{}'::jsonb` | **Consistent** |
| 6 | `uuid-ossp` extension | Referenced in `create_db.sql` and initial migration SQL, but `gen_random_uuid()` is used instead | N/A | Uses `gen_random_uuid()` | Extension NOT installed; `gen_random_uuid()` works natively in PG 13+ | **Real DB** — the extension is unnecessary on PG 13+ |
| 7 | `dashboard_filters` index | `idx_dashboard_filters_dashboard_filter` is redundant — it duplicates the PK `(dashboard_id, filter_id)` | ORM has no explicit index for this | Created by initial migration, dropped by `ce58bba5d461` (TASK-DB-006), then re-created by `c3cc391beded` | Index EXISTS (redundant with PK) | **Alembic** — TASK-DB-006 correctly identified this as redundant, but `c3cc391beded` re-created it |
| 8 | `processing_logs.status` CHECK constraint | SPEC defines 6 statuses (`started`, `uploaded`, `processing`, `success`, `failed`, `completed`); real DB enum has all 6, but `create_db.sql` only has 3 | ORM enum has 6 values | Initial migration creates enum with 6 values | Enum has 6 values | **Consistent** (SPEC.md `create_db.sql` is outdated) |
| 9 | `processing_logs.dashboard_id` FK | `ON DELETE` behavior differs | ORM: no explicit `ondelete` | Initial migration: no `ondelete` | Real DB: `ON DELETE SET NULL` | **Real DB** — FK was likely altered manually or by a migration not in the chain |
| 10 | `users.email` constraint name | Named `users_email_key` in real DB | ORM uses `unique=True` (SQLAlchemy auto-names) | Various migrations rename it | `users_email_key` | **Consistent** |
| 11 | `graphs` unique constraint name | Named `idx_graphs_dashboard_name` in real DB | ORM uses `UniqueConstraint` in `__table_args__` | Renamed by `840a99edb818` and `4bfb28b3732d` | `idx_graphs_dashboard_name` | **Consistent** |
| 12 | `alembic.ini` hardcoded credentials | Contains plaintext password `1234` | N/A | N/A | N/A | **Security risk** — should use environment variable reference |

---

## 4. Migration Audit

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Migration chain integrity | **PASS** | All 16 revisions form a valid DAG. Merge migration `f50a4054569c` correctly resolves two heads. |
| 2 | Current head revision | **PASS** | DB is at `4bfb28b3732d` (latest head). |
| 3 | Reproducibility from empty DB | **CONDITIONAL PASS** | Initial migration `7130ecb0388c` uses `IF NOT EXISTS` for idempotency. However, later migrations use raw SQL with `DO $$` blocks that may fail if run out of order or on a partially migrated DB. |
| 4 | No broken revisions | **PASS** | All revisions have valid `down_revision` pointers. |
| 5 | No circular dependencies | **PASS** | DAG is acyclic. |
| 6 | Migration `alembic upgrade head` on empty DB | **RISKY** | The initial migration creates enum types and tables with `IF NOT EXISTS`, but later migrations (e.g., `840a99edb818`) use `DO $$` blocks that check for old index/constraint names. If the initial migration already creates with the "new" names, the rename operations in `840a99edb818` will be no-ops, which is correct. However, `a1e404502aac` drops indexes with `DROP INDEX IF EXISTS` assuming old names exist — this is safe. |
| 7 | No manual SQL changes detected | **LIKELY PASS** | Schema matches the expected end state of the migration chain. |
| 8 | Schema/data migration separation | **PASS** | No data migrations mixed with schema changes. |
| 9 | Non-idempotent migrations | **FOUND ISSUES** | See §4.1 below. |
| 10 | Downgrade safety | **RISKY** | Several downgrade functions reference index/constraint names that may have been renamed by later migrations. |

### 4.1 Non-Idempotent Migration Issues

| Migration | Issue |
|---|---|
| `840a99edb818` | Uses `DO $$` blocks to conditionally rename indexes. If run twice, the second run is a no-op (safe). However, the `downgrade()` function recreates indexes with `CREATE INDEX IF NOT EXISTS` which may conflict with existing indexes from later migrations. |
| `a1e404502aac` | `upgrade()` drops indexes with `DROP INDEX IF EXISTS` using names that may have been renamed by `840a99edb818`. The order matters: if `840a99edb818` already renamed `idx_access_dashboard` → `idx_dashboard_access_dashboard`, then `a1e404502aac`'s `DROP INDEX IF EXISTS idx_access_dashboard` is a no-op (safe but confusing). |
| `ce58bba5d461` | Creates `update_layouts_updated_at` trigger, but the `updated_at` column doesn't exist on `layouts` until migration `20260508145000`. The trigger creation uses `IF NOT EXISTS` on the trigger name, but the trigger function references `NEW.updated_at` which would fail at runtime if the column doesn't exist. In practice, the trigger is created but will error on UPDATE of `layouts` until the column is added. |
| `c3cc391beded` | Adds `config` column with `IF NOT EXISTS` check. Safe for re-run. |

---

## 5. Environment Isolation Audit

| Environment | Database | Isolation Status | Risk |
|---|---|---|---|
| Production | `bidb` | **SAFE** — separate DB name; `RECREATE_TEST_DB=false` | LOW |
| Development | `bidb` | **RISKY** — uses same `bidb` as production if pointed to same server; `RECREATE_TEST_DB=true` in override | MEDIUM |
| Test (Docker) | `bidb_test` | **SAFE** — separate DB; `RECREATE_TEST_DB=true`; `DATABASE__DBNAME=bidb_test` | LOW |
| Test (local pytest) | `bidb_test` | **RISKY** — conftest.py sets `DATABASE__DBNAME=bidb_test` but if `DATABASE__HOST` points to a shared server, test DB recreation could affect other environments | MEDIUM |

### Test Isolation Details

| Aspect | Status | Notes |
|---|---|---|
| Physical separation | **PASS** | `bidb_test` is a separate PostgreSQL database |
| Separate DSN | **PASS** | `DATABASE__TEST_DBNAME=bidb_test` |
| No prod access from tests | **CONDITIONAL** | Tests use `bidb_test` by default, but if env vars are misconfigured, could hit `bidb` |
| Migration isolation | **PASS** | Test DB gets its own Alembic migrations applied |
| Test data cleanup | **PASS** | SAVEPOINT rollback pattern in `async_db_session` fixture |
| Session-scoped DB recreation | **RISKY** | `setup_test_database` is session-scoped and calls `recreate_test_database()` which drops and recreates `bidb_test`. If any other process is connected to `bidb_test`, `pg_terminate_backend` will kill those connections. |
| Credential separation | **FAIL** | Same `postgres` superuser credentials used for both `bidb` and `bidb_test` |

**Overall Test Isolation Rating: RISKY** — The test database is physically separate but shares the same server and credentials. The `pg_terminate_backend` call in `recreate_test_database()` is aggressive and could terminate connections to `bidb_test` from other processes.

---

## 6. Architectural Problems

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| **CRITICAL** | Security | `postgres` superuser | Application connects as `postgres` (superuser) for all runtime operations | Any SQL injection or bug can destroy the entire database cluster; violates least privilege principle | Create a dedicated application role with limited grants (SELECT, INSERT, UPDATE, DELETE on specific tables; USAGE on sequences; no DDL permissions) | This is the most critical security risk. A superuser connection means any application bug or injection can drop tables, modify pg_catalog, or access other databases. |
| **HIGH** | Schema Design | `layouts.updated_at` trigger | `update_layouts_updated_at` trigger does not exist in the real database | UPDATE on `layouts` will not auto-update `updated_at`; application logic relying on this will silently fail | Add the missing trigger: `CREATE TRIGGER update_layouts_updated_at BEFORE UPDATE ON layouts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()` | The ORM model defines `onupdate=text("now()")` but this only works for SQLAlchemy-generated UPDATEs. Direct SQL updates or updates from other clients won't trigger it. The trigger is the database-level enforcement. |
| **HIGH** | Migrations | Migration chain complexity | 16 migrations for a schema that could be defined in 1-2; multiple no-op migrations; redundant index add/drop/re-add cycles | Future developers cannot easily understand the schema evolution; high risk of errors when adding new migrations; `alembic history` is confusing | Consolidate the migration chain: squash all migrations into a single initial migration that represents the current schema state. Keep the old migrations in an archive directory for reference. | The current chain has migrations that add then drop the same column (`dashboards.config`), rename indexes back and forth, and create no-ops. This creates confusion and increases the chance of migration errors. |
| **HIGH** | Reproducibility | `alembic.ini` hardcoded credentials | `sqlalchemy.url = postgresql+asyncpg://postgres:1234@localhost:5432/bidb` contains plaintext password | Password leakage if `alembic.ini` is committed to VCS; different credentials across environments require manual editing | Remove the hardcoded URL from `alembic.ini`; use environment variable substitution or always pass the URL via `DatabaseStarter._apply_migrations()` | The `env.py` already supports overriding the URL, but the hardcoded default is a security risk and a source of confusion. |
| **MEDIUM** | Schema Design | `dashboard_filters` redundant index | `idx_dashboard_filters_dashboard_filter` on `(dashboard_id, filter_id)` duplicates the PRIMARY KEY | Unnecessary index consumes disk space and slows INSERT/UPDATE/DELETE operations on `dashboard_filters` | Drop the redundant index: `DROP INDEX IF EXISTS idx_dashboard_filters_dashboard_filter` | The PK already provides a btree index on `(dashboard_id, filter_id)`. The duplicate index provides no additional query benefit. |
| **MEDIUM** | Schema Design | `processing_logs.dashboard_id` FK `ON DELETE` | Real DB has `ON DELETE SET NULL` but ORM and initial migration don't specify this | Orphaned processing logs when a dashboard is deleted; inconsistent behavior between ORM expectations and actual DB | Add explicit `ondelete="SET NULL"` to the ORM relationship and create a migration to align the FK constraint | Without explicit `ondelete`, the behavior depends on the database's default (usually RESTRICT). The real DB has SET NULL, but this wasn't intentionally set. |
| **MEDIUM** | Schema Design | `aggregated_data` unbounded growth | No partitioning, no archival strategy, no TTL | As data grows (millions of rows per dashboard/graph), queries will slow down; the table will become the largest in the database | Plan for either: (a) table partitioning by `dashboard_id` or date, or (b) an archival strategy that moves old data to a history table | The `aggregated_data` table stores one row per chart data point. With many dashboards, graphs, and upload cycles, this table will grow indefinitely. |
| **MEDIUM** | Schema Design | `processing_logs` unbounded growth | No retention enforcement at the database level | Log table will grow indefinitely, consuming disk and slowing queries | Add a `started_at` index if not present (already exists via `idx_processing_logs_dashboard_id`), and implement a scheduled cleanup job or use PostgreSQL's `pg_partman` for time-based partitioning | The `DatabaseStarter.cleanup_old_logs()` method exists but is not automatically scheduled. |
| **MEDIUM** | Indexing | `aggregated_data` missing `metrics` GIN index | Only `dims` has a GIN index; queries filtering by `metrics` will require full table scans | Filtering aggregated data by metric values will be slow | Add `CREATE INDEX idx_aggregated_data_metrics_gin ON aggregated_data USING GIN (metrics)` if metric filtering is needed | The SPEC mentions filters are applied via SQL/Polars, but if any API endpoint filters by metric values, the lack of an index will cause performance issues. |
| **MEDIUM** | Maintainability | `create_db.sql` vs `bidb_schema.sql` vs migrations | Three different sources of truth for schema definition | Developers don't know which file to update; schema drift between these files and the actual DB | Deprecate `create_db.sql` and `bidb_schema.sql`; use Alembic migrations as the single source of truth | Having multiple schema definition files creates confusion and increases the risk of inconsistencies. |
| **LOW** | Schema Design | `uuid-ossp` extension | Extension is not installed but referenced in `create_db.sql` | `uuid_generate_v4()` calls in raw SQL will fail if the extension is not available | Remove `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` from `create_db.sql` since `gen_random_uuid()` is used instead | Minor inconsistency; doesn't affect functionality since `gen_random_uuid()` is native to PG 13+. |
| **LOW** | Schema Design | `dashboards.config` nullable | Column is `nullable=True` in ORM but has a `DEFAULT '{}'` | Inconsistent: the default suggests it should always have a value, but NULLs are allowed | Either make the column `nullable=False` with a non-null default, or ensure the application always sets a value | Minor data integrity concern. |
| **LOW** | Async Compatibility | `DatabaseStarter._apply_migrations` | Runs Alembic in a thread via `asyncio.to_thread()` | Alembic runs synchronously in a thread, which is correct, but the thread shares the same event loop | No change needed — this is the correct approach for running sync Alembic in an async context | Documented for completeness; the current implementation is correct. |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|
| `aggregated_data` | Unbounded row growth; no partitioning | As rows grow to millions, INSERT performance degrades (index maintenance on 6 indexes); SELECT queries slow down even with indexes; backup/restore times increase | Monitor row count; when exceeding ~1M rows, implement either: (a) partitioning by `dashboard_id` hash, or (b) a retention policy that archives old uploads' data |
| `processing_logs` | Unbounded log growth | Log table grows without bound; `cleanup_old_logs()` is not automatically scheduled; queries against logs slow down | Schedule `cleanup_old_logs()` via a background task or cron; consider partitioning by `started_at` |
| Connection pooling | `pool_size=10, max_overflow=20` | Under high concurrency (production with 4 uvicorn workers), the pool may be exhausted; each worker creates its own pool | Monitor connection usage; consider using PgBouncer for connection pooling in production; reduce per-worker pool size |
| JSONB filtering | GIN index on `dims` only | Queries filtering by `metrics` values require sequential scans; complex JSONB queries may not use indexes efficiently | Add GIN index on `metrics` if metric filtering is needed; consider expression indexes for frequently queried JSONB keys |
| `dashboard_access` | N+1 query pattern | The ORM uses `lazy="selectin"` for relationships, but access checks on every API request may cause repeated queries | The current `selectin` loading is appropriate; monitor query count per request |
| Backup/restore | Large `aggregated_data` table | `pg_dump` of `bidb` will become slower as `aggregated_data` grows; restore time increases | Consider excluding `aggregated_data` from regular backups (recomputable from uploads); use `pg_dump` with `--exclude-table` or separate backup strategies |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|
| Migration chain | 16 migrations with redundant operations, no-ops, and back-and-forth renames | Confusing history; harder to debug migration issues; increased risk of errors when adding new migrations | **HIGH** — Squash to a single initial migration |
| Superuser connection | Application uses `postgres` superuser | Security vulnerability; any bug can cause catastrophic data loss | **HIGH** — Create dedicated role with limited grants |
| Redundant index | `idx_dashboard_filters_dashboard_filter` duplicates PK | Wasted disk space; slower writes on `dashboard_filters` | **LOW** — Drop the redundant index |
| Multiple schema sources | `create_db.sql`, `bidb_schema.sql`, ORM models, and Alembic all define schema | Confusion about which is authoritative; schema drift | **MEDIUM** — Deprecate `create_db.sql` and `bidb_schema.sql` |
| Missing `layouts` trigger | `update_layouts_updated_at` not created | `updated_at` not auto-updated on direct SQL updates | **HIGH** — Add the missing trigger |
| Hardcoded credentials in `alembic.ini` | Plaintext password in config file | Security risk if file is committed or shared | **MEDIUM** — Remove hardcoded URL |
| No DB role separation | Single `postgres` user for all operations | No audit trail; no privilege separation | **MEDIUM** — Create app-specific roles |

---

## 9. Required Architectural Improvements

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| CRITICAL | Security | Database roles | Application uses `postgres` superuser for all operations | Any application vulnerability can lead to complete data loss or unauthorized access to other databases | Create a dedicated `mkobi_app` role with: `GRANT CONNECT ON DATABASE bidb TO mkobi_app; GRANT USAGE ON SCHEMA public TO mkobi_app; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkobi_app; GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mkobi_app;` Revoke all other privileges. Use this role in the application DSN. | This is the single most impactful security improvement. It limits the blast radius of any application bug or injection attack. |
| HIGH | Schema Design | `layouts` table | Missing `update_layouts_updated_at` trigger | `updated_at` column not auto-updated when layouts are modified via SQL or other clients | Create a migration that adds: `CREATE TRIGGER update_layouts_updated_at BEFORE UPDATE ON layouts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();` | Without this trigger, the `updated_at` field is only updated by SQLAlchemy's Python-side `onupdate`, which doesn't fire for raw SQL, migrations, or other clients. |
| HIGH | Migrations | Migration chain | 16 migrations with redundant operations | Confusing history; high maintenance cost; risk of migration errors | Squash all migrations into a single `001_initial.py` that creates the current schema. Archive old migrations. Update `alembic_version` to point to the new squashed revision. | A clean migration history makes onboarding easier, reduces errors, and makes the schema evolution understandable. |
| MEDIUM | Schema Design | `dashboard_filters` | Redundant index on `(dashboard_id, filter_id)` | Wasted disk space; unnecessary write overhead | `DROP INDEX IF EXISTS idx_dashboard_filters_dashboard_filter;` | The PK already provides the same index. This is low-risk but should be cleaned up. |
| MEDIUM | Schema Design | `aggregated_data` | No GIN index on `metrics` | Slow queries when filtering by metric values | If the application filters by metrics, add: `CREATE INDEX idx_aggregated_data_metrics_gin ON aggregated_data USING GIN (metrics);` | The SPEC mentions filters are applied via SQL/Polars. If any endpoint filters by metrics, this index is needed. |
| MEDIUM | Reproducibility | `alembic.ini` | Hardcoded credentials in config file | Security risk; environment-specific configuration in a shared file | Remove the `sqlalchemy.url` line from `alembic.ini` or set it to empty. Always pass the URL programmatically via `DatabaseStarter._apply_migrations()`. | The `env.py` already supports URL override, so the hardcoded value is unnecessary and risky. |
| MEDIUM | Schema Design | `processing_logs` | No automatic cleanup scheduled | Table grows indefinitely; disk space exhaustion | Schedule `DatabaseStarter.cleanup_old_logs()` as a periodic background task (e.g., via APScheduler or a cron job) | Without scheduled cleanup, the log table will grow without bound. The cleanup code exists but is never called automatically. |
| LOW | Maintainability | `create_db.sql`, `bidb_schema.sql` | Outdated schema definition files | Confusion about which file represents the current schema | Add a comment to both files: "DEPRECATED — use Alembic migrations as the source of truth." Remove from CI/CD pipelines if referenced. | These files are from early development and don't match the current schema. They create confusion for new developers. |
| LOW | Schema Design | `uuid-ossp` extension | Referenced in `create_db.sql` but not installed | Minor inconsistency; doesn't affect functionality | Remove the `CREATE EXTENSION` line from `create_db.sql` | `gen_random_uuid()` is native to PostgreSQL 13+ and doesn't require the extension. |

---

## Appendix A: Migration Chain Diagram

```
7130ecb0388c (root) — True initial migration
  └── e86f3c8f7324 — Schema adjustments (no-op)
        ├── 57f43a5c499d — Change JSON to JSONB (no-op)
        │     └── 2aa835fe1fac — Add composite index on aggregated_data
        │           └── 840a99edb818 — Standardize index naming
        │                 └── (branch) a1b2c3d4e5f6 — Add config to dashboards
        │                       └── ce58bba5d461 — Add DB constraints and fix schema issues
        │                             └── a1e404502aac — Add registration requests table
        │                                   └── f50a4054569c (merge) ← merges a1e404502aac + 20260507141843
        │                                         └── 91f5436a3098 — Add unique constraint on aggregated_data
        │                                               └── a2b3c4d5e6f7 — Fix unique constraint
        │                                                     └── 20260508145000 — Add updated_at to layouts
        │                                                           └── c3cc391beded — Add config column and fix indexes
        │                                                                 └── 4bfb28b3732d (HEAD) — Add processing_logs dashboard_id index
        └── 3f7a1b2c9d0e — Add processing_logs dashboard_id index (orphaned branch, merged via f50a4054569c)
  └── 20260507141843 — Add updated_at to users (branch merged via f50a4054569c)
```

**Note:** Migration `3f7a1b2c9d0e` has `down_revision = '840a99edb818'` but is not reachable from the main chain. It was created as a parallel branch and its changes were superseded by `4bfb28b3732d`. This is a migration orphan that should be removed or marked as merged.

---

## Appendix B: Environment Variable Reference

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE__HOST` | `localhost` | PostgreSQL server host |
| `DATABASE__PORT` | `5432` | PostgreSQL server port |
| `DATABASE__USER` | `postgres` | Database user |
| `DATABASE__PASSWORD` | — | Database password (required) |
| `DATABASE__DBNAME` | `bidb` | Main database name |
| `DATABASE__TEST_DBNAME` | `bidb_test` | Test database name |
| `AUTO_MIGRATE` | `false` | Auto-run Alembic migrations on startup |
| `RECREATE_TEST_DB` | `false` | Drop and recreate test database on startup |
| `ENV` | `development` | Environment: `development`, `test`, `staging`, `production` |

---

## Appendix C: Files Analyzed

| File | Purpose |
|---|---|
| `.env.example` | Environment variable template |
| `docker-compose.yml` | Production Docker Compose |
| `docker-compose.override.yml` | Development overrides |
| `docker-compose.test.yml` | Test environment overrides |
| `Dockerfile` | Multi-stage Docker build |
| `alembic.ini` | Alembic configuration |
| `alembic/env.py` | Alembic environment (migration runner) |
| `alembic/versions/*.py` | 16 migration files |
| `create_db.sql` | Manual schema creation script (outdated) |
| `bidb_schema.sql` | pg_dump schema export |
| `src/mkobi/config.py` | Application settings (pydantic-settings) |
| `src/mkobi/db/session.py` | SQLAlchemy engine/session management |
| `src/mkobi/db/starter.py` | Database initialization and migration runner |
| `src/mkobi/db/base.py` | SQLAlchemy declarative base |
| `src/mkobi/db/models/*.py` | 10 ORM model files |
| `src/mkobi/models/enums.py` | StrEnum definitions |
| `src/mkobi/db/repositories/*.py` | Repository layer |
| `tests/conftest.py` | Test configuration and fixtures |
| `pyproject.toml` | Project configuration (pytest settings) |
