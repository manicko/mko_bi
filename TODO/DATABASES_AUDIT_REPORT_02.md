# Database Audit Report - BI Dashboard System

**Date:** 2026-05-03  
**Auditor:** Automated Analysis  
**Scope:** PostgreSQL databases in mko_bi project

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | Development/Production | Main application data | `DATABASE_URL` (from config) | Manual (create_db.sql) + Alembic migrations |
| `bidb_test` | Test | Automated testing | `TEST_ASYNC_DB_URL` (hardcoded in conftest.py) | Manual / Assumed pre-applied |

### DSN Configuration

**Main Database (`bidb`):**
- From `app.yaml` / `config.py`: `postgresql://postgres:****@localhost:5432/bidb`
- Password via `DB_PASSWORD` environment variable

**Test Database (`bidb_test`):**
- Hardcoded in `tests/conftest.py`: `postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test`
- Environment variables set in conftest.py: `DB_PASSWORD=1234`, `DB_NAME=bidb_test`

---

## 2. Schema Documentation

### 2.1. Tables in `bidb` Database

| Table Name | Columns | Primary Key | Foreign Keys | Indexes | Notes |
|---|---|---|---|---|---|
| `users` | id(uuid), email(varchar(255)), password_hash(varchar(255)), role(user_role), is_active(boolean), created_at(timestamptz) | id | - | idx_users_email (UNIQUE), idx_users_role | Uses `user_role` ENUM |
| `layouts` | id(uuid), name(varchar(255)), definition(**json**), created_at(timestamptz) | id | - | idx_layouts_name (UNIQUE) | **Should be jsonb** |
| `dashboards` | id(uuid), name(varchar(255)), description(text), layout_id(uuid), created_by(uuid), config(jsonb), created_at(timestamptz), updated_at(timestamptz) | id | layout_id → layouts(id) SET NULL, created_by → users(id) SET NULL | idx_dashboards_name (UNIQUE) | |
| `graphs` | id(uuid), dashboard_id(uuid), name(varchar(255)), type(varchar(50)), config(jsonb), dimensions(jsonb), metrics(jsonb), created_at(timestamptz) | id | dashboard_id → dashboards(id) CASCADE | idx_graphs_dashboard_name (UNIQUE) | **Uses CHECK constraint, not ENUM** |
| `filters` | id(uuid), name(varchar(255)), type(varchar(50)), config(jsonb), created_at(timestamptz) | id | - | idx_filters_name (UNIQUE) | **Uses CHECK constraint, not ENUM** |
| `dashboard_access` | user_id(uuid), dashboard_id(uuid), permission(dashboard_permission_level) | (user_id, dashboard_id) | user_id → users(id) CASCADE, dashboard_id → dashboards(id) CASCADE | idx_dashboard_access_user, idx_dashboard_access_dashboard | Uses `dashboard_permission_level` ENUM |
| `dashboard_filters` | dashboard_id(uuid), filter_id(uuid) | (dashboard_id, filter_id) | dashboard_id → dashboards(id) CASCADE, filter_id → filters(id) CASCADE | idx_dashboard_filters_dashboard_filter | Many-to-many table |
| `processing_configs` | dashboard_id(uuid), settings(jsonb), updated_at(timestamptz) | dashboard_id | dashboard_id → dashboards(id) CASCADE | - | One-to-one with dashboards |
| `processing_logs` | id(uuid), dashboard_id(uuid), status(varchar(50)), message(varchar(1000)), started_at(timestamptz), finished_at(timestamptz) | id | dashboard_id → dashboards(id) SET NULL | - | **Uses CHECK constraint, not ENUM** |
| `aggregated_data` | id(**integer**), dashboard_id(uuid), graph_id(uuid), dims(jsonb), metrics(jsonb) | id | dashboard_id → dashboards(id) CASCADE, graph_id → graphs(id) CASCADE | idx_aggregated_data_dashboard_id, idx_aggregated_data_graph_id, idx_aggregated_data_dims_gin (GIN) | **id should be BIGINT** |
| `alembic_version` | version_num(varchar(32)) | version_num | - | - | Migration tracking |

### 2.2. PostgreSQL ENUM Types

| ENUM Name | Values | Used In | Status |
|---|---|---|---|
| `user_role` | admin, editor, viewer | `users.role` | ✅ Applied |
| `dashboard_permission_level` | view, edit, admin | `dashboard_access.permission` | ✅ Applied |
| `graph_type` | bar, line, pie, table | `graphs.type` | ❌ **NOT APPLIED** (uses CHECK) |
| `filter_type` | select, multiselect, range, date | `filters.type` | ❌ **NOT APPLIED** (uses CHECK) |
| `processing_status` | started, uploaded, processing, success, failed, completed | `processing_logs.status` | ❌ **NOT APPLIED** (uses CHECK) |

### 2.3. Extensions

| Extension | Schema | Purpose |
|---|---|---|
| `uuid-ossp` | public | UUID generation functions |

---

## 3. Schema Drift Report

| Object | Problem | ORM Model | Alembic Migration | Real DB | Recommended Source of Truth |
|---|---|---|---|---|---|
| `layouts.definition` | Type is `json` instead of `jsonb` | `JSON` (should be `JSONB`) | 57f43a5c499d tries to convert to JSONB | `json` | Apply migration correctly |
| `graphs.type` | Uses CHECK constraint instead of ENUM | `Enum(GraphTypeEnum, name="graph_type")` | e86f3c8f7324 creates enum but doesn't alter column | `varchar(50)` with CHECK | Use ENUM type |
| `filters.type` | Uses CHECK constraint instead of ENUM | `Enum(FilterTypeEnum, name="filter_type")` | e86f3c8f7324 doesn't address this | `varchar(50)` with CHECK | Use ENUM type |
| `processing_logs.status` | Uses CHECK constraint instead of ENUM | `Enum(ProcessingStatusEnum, name="processing_status")` | e86f3c8f7324 doesn't address this | `varchar(50)` with CHECK | Use ENUM type |
| `aggregated_data.id` | `integer` instead of `bigint` | `Integer` with `autoincrement=True` | e86f3c8f7324 changes from BIGINT to Integer | `integer` with sequence | Use `BIGINT`/`BIGSERIAL` |
| `users.role` | ✅ Correct | `Enum(UserRoleEnum, name="user_role")` | e86f3c8f7324 creates enum | `user_role` ENUM | - |
| `dashboard_access.permission` | ✅ Correct | `Enum(PermissionEnum, name="dashboard_permission_level")` | e86f3c8f7324 creates enum | `dashboard_permission_level` ENUM | - |

---

## 4. Migration Audit

| Check | Status | Notes |
|---|---|---|
| Migration chain integrity | ✅ OK | e86f3c8f7324 → 57f43a5c499d → 2aa835fe1fac → 840a99edb818 |
| Current version in `bidb` | ✅ 840a99edb818 | Latest migration applied |
| Reproducibility from scratch | ⚠️ **RISKY** | Migration e86f3c8f7324 is misnamed "initial" but alters existing schema. Running on empty DB will fail. |
| Non-idempotent migrations | ❌ **YES** | e86f3c8f7324 uses `op.alter_column` without checking existence |
| State-dependent migrations | ❌ **YES** | e86f3c8f7324 assumes certain columns exist with certain types |
| Broken revisions | ✅ None | All revisions are present |
| Cyclic dependencies | ✅ None | Linear migration chain |
| Data vs schema migrations | ✅ OK | Only schema changes (no data migrations) |
| Test DB migrations | ❌ **NOT APPLIED** | `bidb_test` has no `alembic_version` table |

### Migration Details

| Revision | Description | Issues |
|---|---|---|
| e86f3c8f7324 | "Initial migration" (creates ENUMs, alters existing tables) | - Misnamed (not truly initial) - Assumes pre-existing tables - Creates ENUMs but doesn't convert all columns |
| 57f43a5c499d | Change JSON to JSONB for PostgreSQL | - Only converts some columns (`dashboards.config`, `graphs.*`, `filters.config`, `processing_configs.settings`) - **Missed `layouts.definition`** |
| 2aa835fe1fac | Add composite index on aggregated_data | ✅ OK (but later dropped by 840a99edb818) |
| 840a99edb818 | Standardize index naming | ✅ OK - Renames constraints and indexes to `idx_` prefix |

---

## 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|---|---|---|---|
| Development | `bidb` | ✅ Separate DB | LOW |
| Test | `bidb_test` | ⚠️ **Separate but not properly initialized** | **HIGH** - No migrations applied |
| Production | Not defined | N/A | - |

### Test Database Issues

1. **No migrations applied:** `bidb_test` lacks `alembic_version` table
2. **Hardcoded credentials:** Password `1234` in `conftest.py`
3. **Assumption-based setup:** `conftest.py` has comment "Migrations assumed to be already applied"
4. **Cleanup strategy:** Uses `TRUNCATE CASCADE` instead of recreation (faster but risks state leakage)

---

## 6. Architectural Problems

| Severity | Area | Problem | Risk | Recommendation |
|---|---|---|---|---|
| **HIGH** | Schema Design | `aggregated_data.id` uses `integer` (max ~2.1B) instead of `bigint` | Integer overflow when table grows beyond 2.1B rows | Change to `BIGINT`/`BIGSERIAL` as per SPEC |
| **HIGH** | Migrations | Migration e86f3c8f7324 is not reproducible from scratch | Cannot set up new environment reliably | Create true initial migration that creates tables from scratch |
| **HIGH** | Test Isolation | Test DB `bidb_test` has no migrations applied | Tests may fail or use wrong schema | Run `alembic upgrade head` on test DB in CI/setup |
| **MEDIUM** | Schema Drift | `layouts.definition` is `json` instead of `jsonb` | Loses PostgreSQL JSONB advantages (GIN indexes, operators) | Apply migration 57f43a5c499d correctly to convert to JSONB |
| **MEDIUM** | Schema Design | ENUM types `graph_type`, `filter_type`, `processing_status` not applied | Drift between ORM (uses ENUM) and DB (uses CHECK) | Alter columns to use ENUM types |
| **MEDIUM** | Maintainability | Migration e86f3c8f7324 mixes "initial" and "alter" operations | Difficult to understand migration intent | Split into true initial + alter migrations |
| **MEDIUM** | Security | Test credentials hardcoded in `conftest.py` | Credentials exposure | Use environment variables |
| **LOW** | Indexing | `processing_configs` has no index on `dashboard_id` | FK lookup performance | Add index (though PK serves as lookup) |
| **LOW** | Maintainability | `layouts.definition` uses `JSON` in ORM model instead of `JSONB` | Inconsistency with other JSON columns | Change ORM model to use `JSONB` |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|
| `aggregated_data` table | `id` as `integer` (32-bit) | Overflow after ~2.1B rows inserted | Change to `BIGINT` (64-bit, up to 9.2M billion rows) |
| `aggregated_data` table | Growth unbounded | Table scans become slow, storage pressure | Consider partitioning by `dashboard_id` or time if growth is rapid |
| `processing_logs` table | Unbounded growth | Historical logs accumulate, slow queries | Implement log rotation/archival strategy |
| JSONB queries | Heavy `dims` GIN index usage | Write amplification on `aggregated_data` | Monitor write performance; GIN indexes have overhead |
| Concurrent users | No connection pooling analysis | Connection exhaustion under load | Configure `pool_size` and `max_overflow` for async engine |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|
| Migrations | e86f3c8f7324 is not reproducible from empty DB | Cannot set up new environments reliably | HIGH |
| Schema | Missing ENUM types (`graph_type`, `filter_type`, `processing_status`) | ORM-DB drift, potential type errors | HIGH |
| Schema | `layouts.definition` not JSONB | Lost JSONB features | MEDIUM |
| Test DB | Migrations not applied | Tests may use wrong schema | HIGH |
| Indexing | Inconsistent naming (old migrations had different names) | Confusion when examining DB | LOW |
| Config | Password in `app.yaml` (even with comment to change) | Security risk if file is committed | MEDIUM |

---

## 9. Required Architectural Improvements

### 9.1. Fix `aggregated_data.id` Type

**Problem:** SPEC defines `BIGSERIAL`, but DB has `integer` with sequence.

**Required Change:**
```sql
-- In a new migration:
ALTER TABLE aggregated_data ALTER COLUMN id TYPE BIGINT;
-- Then update the sequence type
ALTER SEQUENCE aggregated_data_id_seq AS BIGINT;
```

**Why It Matters:** Prevents integer overflow when table grows beyond 2.1B rows. This is especially important for `aggregated_data` which grows with each data processing run.

---

### 9.2. Apply Missing ENUM Types

**Problem:** ORM models define ENUM types, but DB uses CHECK constraints for `graphs.type`, `filters.type`, `processing_logs.status`.

**Required Change:**
```sql
-- Create missing ENUM types
CREATE TYPE graph_type AS ENUM ('bar', 'line', 'pie', 'table');
CREATE TYPE filter_type AS ENUM ('select', 'multiselect', 'range', 'date');
CREATE TYPE processing_status AS ENUM ('started', 'uploaded', 'processing', 'success', 'failed', 'completed');

-- Alter columns to use ENUMs
ALTER TABLE graphs ALTER COLUMN type TYPE graph_type USING type::graph_type;
ALTER TABLE filters ALTER COLUMN type TYPE filter_type USING type::filter_type;
ALTER TABLE processing_logs ALTER COLUMN status TYPE processing_status USING status::processing_status;
```

**Why It Matters:** Ensures consistency between ORM models and database schema. ENUM types provide better type safety and integration with SQLAlchemy's enum handling.

---

### 9.3. Fix `layouts.definition` to Use JSONB

**Problem:** Migration 57f43a5c499d was supposed to convert `layouts.definition` to JSONB, but it still shows as `json` in DB.

**Required Change:**
```sql
ALTER TABLE layouts ALTER COLUMN definition TYPE JSONB USING definition::jsonb;
```

Also update ORM model (`src/mko_bi/db/models/layout.py`) to use `JSONB` instead of `JSON`.

**Why It Matters:** JSONB provides better query performance (GIN indexes), more operators, and is the standard for PostgreSQL JSON storage.

---

### 9.4. Make Migrations Reproducible

**Problem:** Migration e86f3c8f7324 assumes pre-existing tables and alters them, making it impossible to run on a fresh database.

**Required Change:**
1. Create a true initial migration that creates all tables from scratch
2. Remove the alter logic from e86f3c8f7324 or mark it as non-reproducible
3. Document that new environments should run all migrations in order

**Why It Matters:** Essential for onboarding, CI/CD, and disaster recovery.

---

### 9.5. Initialize Test Database with Migrations

**Problem:** `bidb_test` doesn't have migrations applied.

**Required Change:**
Add to `conftest.py` or CI setup:
```python
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply Alembic migrations to test database."""
    import subprocess
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        env={**os.environ, "DB_NAME": "bidb_test"},
        cwd=PROJECT_ROOT
    )
    assert result.returncode == 0
```

**Why It Matters:** Tests must run against the correct schema that matches the application.

---

### 9.6. Standardize JSON/JSONB Usage

**Current State:**
- ORM models: Mix of `JSON` (layouts) and `JSONB` (others)
- DB: Mix of `json` (layouts.definition) and `jsonb` (others)

**Required Change:**
1. Update `src/mko_bi/db/models/layout.py` to use `JSONB`
2. Ensure migration applies JSONB to `layouts.definition`

**Why It Matters:** Consistency reduces cognitive load and prevents subtle bugs.

---

## 10. Summary of Critical Actions

| Priority | Action | Impact |
|---|---|---|
| **P0** | Fix `aggregated_data.id` to BIGINT | Prevents future overflow |
| **P0** | Apply missing ENUM types | Fixes ORM-DB drift |
| **P0** | Initialize test DB with migrations | Ensures test reliability |
| **P1** | Fix `layouts.definition` to JSONB | Consistency, performance |
| **P1** | Make migrations reproducible | Operational stability |
| **P2** | Remove/secure hardcoded credentials | Security |

---

## 11. Compliance with SPEC.md

| SPEC Requirement | Status | Notes |
|---|---|---|
| `users` table structure | ✅ Compliant | Matches SPEC (with ENUM applied) |
| `layouts` table structure | ⚠️ Partial | `definition` should be JSONB |
| `dashboards` table structure | ✅ Compliant | |
| `graphs` table structure | ⚠️ Partial | `type` should use ENUM |
| `filters` table structure | ⚠️ Partial | `type` should use ENUM |
| `dashboard_access` table structure | ✅ Compliant | |
| `processing_configs` table structure | ✅ Compliant | |
| `aggregated_data` table structure | ❌ **Non-compliant** | `id` should be BIGSERIAL |
| `processing_logs` table structure | ⚠️ Partial | `status` should use ENUM |
| Indexes on `aggregated_data` | ✅ Compliant | GIN index on `dims` present |
| Indexes on `dashboard_access` | ✅ Compliant | Both user and dashboard indexes present |

---

## 12. Recommendations Summary

The database architecture is generally sound with clear separation of concerns. The main issues are:

1. **Schema drift** between ORM models and actual database (ENUM types not applied)
2. **Non-reproducible migrations** (e86f3c8f7324 assumes existing schema)
3. **Test database not properly initialized**
4. **Type mismatch** on `aggregated_data.id` (integer vs bigint per SPEC)

Addressing these issues will improve maintainability, reproducibility, and prepare the system for growth.