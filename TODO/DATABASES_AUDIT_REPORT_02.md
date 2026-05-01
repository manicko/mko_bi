# Database Audit Report - BI Dashboard System

**Date**: 2026-05-01  
**Auditor**: Automated Analysis  
**Scope**: PostgreSQL databases, ORM models, migrations, environment configuration

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | Development/Production | Main application database | `DATABASE_URL` (DB_NAME="bidb") | Manual SQL (`create_db.sql`) or `Base.metadata.create_all()` |
| `bidb_test` | Test | Automated testing | `TEST_DB_URL` hardcoded in conftest.py | `Base.metadata.create_all()` in test fixture |

### Notes:
- Main database name configured via `config.py` (`DB_NAME = "bidb"`)
- Test database (`bidb_test`) does NOT exist - will cause test failures
- No Docker/docker-compose.yml found - database setup is manual

---

## 2. Schema Documentation - `bidb` Database

### 2.1 Tables

#### `users`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | uuid | PK, DEFAULT uuid_generate_v4() | |
| `email` | text | NOT NULL, UNIQUE | No length limit in DB (code: String(255)) |
| `password_hash` | text | NOT NULL | |
| `role` | text | NOT NULL, CHECK IN ('admin','editor','viewer') | DB: text, Code: Enum(UserRoleEnum) |
| `is_active` | boolean | DEFAULT true | DB: nullable, Code: NOT NULL |
| `created_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |

**Indexes**:
- `users_pkey` (PK, btree on id)
- `users_email_key` (UNIQUE, btree on email)

#### `layouts`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | uuid | PK, DEFAULT uuid_generate_v4() | |
| `name` | text | NOT NULL, UNIQUE | No length limit in DB (code: String(255)) |
| `definition` | jsonb | NOT NULL | |
| `created_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |

**Indexes**:
- `layouts_pkey` (PK, btree on id)
- `layouts_name_key` (UNIQUE, btree on name)

#### `dashboards`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | uuid | PK, DEFAULT uuid_generate_v4() | |
| `name` | text | NOT NULL, UNIQUE | No length limit in DB (code: String(255)) |
| `description` | text | nullable | |
| `layout_id` | uuid | FK to layouts(id), SET NULL | Code: ondelete="SET NULL" |
| `created_by` | uuid | FK to users(id), SET NULL | Code: ondelete="SET NULL" |
| `config` | jsonb | NOT NULL, DEFAULT '{}' | Code uses JSON type |
| `created_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |
| `updated_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |

**Indexes**:
- `dashboards_pkey` (PK, btree on id)
- `dashboards_name_key` (UNIQUE, btree on name)

**Foreign Keys**:
- `dashboards_created_by_fkey` → users(id) ON SET NULL
- `dashboards_layout_id_fkey` → layouts(id) ON SET NULL

#### `graphs`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | uuid | PK, DEFAULT uuid_generate_v4() | |
| `dashboard_id` | uuid | FK to dashboards(id) ON DELETE CASCADE | |
| `name` | text | NOT NULL | No length limit in DB (code: String(255)) |
| `type` | text | NOT NULL, CHECK IN ('bar','line','pie','table') | DB: text check, Code: String(50) |
| `config` | jsonb | NOT NULL | Code uses JSON type |
| `dimensions` | jsonb | NOT NULL | Code uses JSON type |
| `metrics` | jsonb | NOT NULL | Code uses JSON type |
| `created_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |

**Indexes**:
- `graphs_pkey` (PK, btree on id)
- `graphs_dashboard_id_name_key` (UNIQUE, btree on dashboard_id, name)

**Foreign Keys**:
- `graphs_dashboard_id_fkey` → dashboards(id) ON DELETE CASCADE

#### `filters`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | uuid | PK, DEFAULT uuid_generate_v4() | |
| `name` | text | NOT NULL, UNIQUE | No length limit in DB (code: String(255)) |
| `type` | text | NOT NULL | Code: String(50) |
| `config` | jsonb | NOT NULL | Code uses JSON type |
| `created_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |

**Indexes**:
- `filters_pkey` (PK, btree on id)
- `filters_name_key` (UNIQUE, btree on name)

#### `dashboard_access`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `user_id` | uuid | FK to users(id) ON DELETE CASCADE | Part of PK |
| `dashboard_id` | uuid | FK to dashboards(id) ON DELETE CASCADE | Part of PK |
| `permission` | text | NOT NULL, CHECK IN ('view','edit','admin') | DB: text, Code: Enum(PermissionEnum) |

**Indexes**:
- `dashboard_access_pkey` (PK, btree on user_id, dashboard_id)
- `idx_access_user` (btree on user_id)
- `idx_access_dashboard` (btree on dashboard_id)

**Foreign Keys**:
- `dashboard_access_user_id_fkey` → users(id) ON DELETE CASCADE
- `dashboard_access_dashboard_id_fkey` → dashboards(id) ON DELETE CASCADE

#### `processing_configs`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `dashboard_id` | uuid | PK, FK to dashboards(id) ON DELETE CASCADE | |
| `settings` | jsonb | NOT NULL | Code uses JSON type |
| `updated_at` | timestamp without time zone | DEFAULT now() | **Drift**: Code expects timezone-aware |

**Indexes**:
- `processing_configs_pkey` (PK, btree on dashboard_id)

**Foreign Keys**:
- `processing_configs_dashboard_id_fkey` → dashboards(id) ON DELETE CASCADE

#### `processing_logs`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | uuid | PK, DEFAULT uuid_generate_v4() | |
| `dashboard_id` | uuid | FK to dashboards(id) ON DELETE SET NULL | |
| `status` | text | NOT NULL, CHECK IN ('started','success','failed') | |
| `message` | text | nullable | |
| `started_at` | timestamp without time zone | nullable | **Drift**: Code expects timezone-aware |
| `finished_at` | timestamp without time zone | nullable | **Drift**: Code expects timezone-aware |

**Indexes**:
- `processing_logs_pkey` (PK, btree on id)

**Foreign Keys**:
- `processing_logs_dashboard_id_fkey` → dashboards(id) ON DELETE SET NULL

#### `aggregated_data`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | bigint | PK, DEFAULT nextval('aggregated_data_id_seq') | Code: Integer (compatible) |
| `dashboard_id` | uuid | NOT NULL, FK to dashboards(id) ON DELETE CASCADE | |
| `graph_id` | uuid | NOT NULL, FK to graphs(id) ON DELETE CASCADE | |
| `dims` | jsonb | NOT NULL | Code uses custom JSONBType |
| `metrics` | jsonb | NOT NULL | Code uses custom JSONBType |

**Indexes**:
- `aggregated_data_pkey` (PK, btree on id)
- `idx_agg_dashboard_id` (btree on dashboard_id)
- `idx_agg_graph_id` (btree on graph_id)
- `idx_agg_dims_gin` (GIN on dims)

**Foreign Keys**:
- `aggregated_data_dashboard_id_fkey` → dashboards(id) ON DELETE CASCADE
- `aggregated_data_graph_id_fkey` → graphs(id) ON DELETE CASCADE

### 2.2 Missing Table

#### `dashboard_filters` (NOT IN DATABASE)
Defined in code (`filters.py`) but missing from database.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `dashboard_id` | uuid | PK, FK to dashboards(id) ON DELETE CASCADE | |
| `filter_id` | uuid | PK, FK to filters(id) ON DELETE CASCADE | |

**Indexes** (from code):
- `idx_dashboard_filter` (dashboard_id, filter_id)

**Impact**: Many-to-many relationship between dashboards and filters is NON-FUNCTIONAL.

### 2.3 Extensions
- `uuid-ossp` (created in `bidb_schema.sql`, also in `create_db.sql`)

---

## 3. Schema Drift Report

| Object | Problem | ORM (SQLAlchemy) | Real DB (bidb) | Recommended Source of Truth |
|---|---|---|---|---|
| All timestamp columns | ORM uses `DateTime(timezone=True)`, DB has `timestamp without time zone` | timezone-aware | no timezone | **Align DB to ORM**: Use `timestamp with time zone` |
| `is_active` in `users` | ORM: `nullable=False`, DB: nullable | NOT NULL | nullable | **Align DB to ORM**: Add NOT NULL |
| `email`, `name` columns | ORM: `String(255)`, DB: `text` (no length limit) | length 255 | unlimited | Optional: Add CHECK constraint or align to text |
| `dashboard_filters` table | Exists in ORM (Table def) | defined | **MISSING** | **Create table in DB** |
| `config` column in `dashboards` | ORM: JSON type, DB: jsonb | JSON | jsonb | Compatible (jsonb is better for PG) |
| `dims`, `metrics` in `aggregated_data` | ORM: custom JSONBType, DB: jsonb | JSONB | jsonb | Compatible |

---

## 4. Migration Audit

| Check | Status | Notes |
|---|---|---|
| Alembic/Flask-Migrate setup | **NOT PRESENT** | No Alembic configuration found in project |
| Migration chain integrity | **N/A** | No migrations exist |
| Reproducibility from scratch | **PARTIAL** | `Base.metadata.create_all()` works but not idempotent |
| Broken revisions | **N/A** | No migrations |
| Cyclic dependencies | **N/A** | No migrations |
| `alembic upgrade head` on empty DB | **N/A** | Alembic not configured |
| Manual SQL changes | **YES** | `bidb_schema.sql` is a pg_dump output, manual edits possible |
| Non-idempotent schema creation | **YES** | `create_db.sql` has no `IF NOT EXISTS`, `create_all()` is idempotent |
| State-dependent migrations | **N/A** | No migrations |
| Mixed schema/data migrations | **N/A** | No migrations |

### Critical Finding:
**No migration system is configured.** Schema changes are managed via:
1. SQLAlchemy models
2. `Base.metadata.create_all()` (in `session.py` and `conftest.py`)
3. Manual SQL scripts (`create_db.sql`, `bidb_schema.sql`)

This makes schema versioning, rollback, and production deployments risky.

---

## 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|---|---|---|---|
| Development | `bidb` (localhost:5432) | Manual setup | LOW (single user) |
| Test | `bidb_test` (localhost:5432) | **DB DOES NOT EXIST** | **HIGH** - Tests will fail |
| Production | Not configured | Unknown | Unknown |

### Test Isolation Issues:
1. **Test database does not exist** - `bidb_test` not found on system
2. **Synchronous engine in tests** - `conftest.py` uses `create_engine()` (sync) while FastAPI is async
3. **Incomplete test cleanup** - `clean_db` fixture only cleans `DashboardAccess`, `Dashboard`, `User` - leaves orphaned data in other tables
4. **No test DB creation script** - No SQL or migration to set up test database

**Risk Level**: **HIGH** - Tests cannot run without manual database creation.

---

## 6. Architectural Problems

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| **CRITICAL** | Async Compatibility | All API routes + DB session | FastAPI uses `async def` endpoints but DB sessions are **synchronous** (`Session`). This blocks the event loop on every DB call. | Complete performance degradation; async FastAPI loses all benefits; request blocking | Use `sqlalchemy.ext.asyncio` (`AsyncSession`, `create_async_engine`) or make endpoints synchronous (`def` instead of `async def`) | Async endpoints with sync DB block the entire event loop, making the app effectively synchronous with extra overhead |
| **CRITICAL** | Schema Design | `dashboard_filters` table | Table defined in ORM but **missing from database** - many-to-many relationship between dashboards and filters is broken | Filter assignments to dashboards will fail at runtime or be silently ignored | Create `dashboard_filters` table in DB via migration or `create_all()` | Core feature (dashboard filters) is non-functional |
| **HIGH** | Migrations | Entire schema | No migration system (Alembic) configured | Cannot version schema, rollback changes, or safely deploy to production | Set up Alembic for PostgreSQL | Production deployments become high-risk; no audit trail for schema changes |
| **HIGH** | Test Isolation | `bidb_test` database | Test database does not exist; tests will fail immediately | CI/CD broken; cannot verify changes | Create `bidb_test` database; add to setup | Tests are the safety net - if they can't run, quality degrades |
| **HIGH** | Schema Design | All timestamp columns | ORM uses `DateTime(timezone=True)` but DB has `timestamp without time zone` | Timezone-aware datetimes from Python may be silently truncated; bugs in date filtering across timezones | Alter DB columns to `timestamp with time zone` (timestamptz) | Data integrity for time-based queries; especially important for YOY calculations |
| **MEDIUM** | Maintainability | `is_active` in `users` | ORM: `nullable=False`, DB: nullable | Inconsistent state possible (NULL values in DB) | Add NOT NULL constraint to DB column | Prevents inconsistent data states |
| **MEDIUM** | Test Isolation | `clean_db` fixture | Only cleans 3 tables, leaves data in `graphs`, `aggregated_data`, `filters`, etc. | Test pollution - tests may depend on data from previous tests | Extend cleanup to all tables or use transaction rollback | Reliable, isolated tests are essential for refactoring |
| **MEDIUM** | Async Compatibility | `conftest.py` | Uses synchronous `create_engine` for tests | Mismatch between test DB layer and production DB layer | Use async engine for tests or document that tests are sync | Consistent behavior between test and production |
| **LOW** | Schema Design | `email`, `name` columns | ORM: `String(255)`, DB: `text` (unlimited) | Minor: inconsistent validation (ORM validates length, DB doesn't) | Add CHECK constraints to DB or align to text | Consistency between validation layers |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|
| `aggregated_data` table | High growth potential (1 row = 1 graph point, multiple dashboards) | Full table scans on `dashboard_id` + `graph_id` filtering as data grows beyond millions of rows | Add composite index on `(dashboard_id, graph_id)` for common query pattern |
| `processing_logs` table | Unbounded growth (logs never deleted) | Table becomes huge over time, slowing down queries and backups | Add archival strategy (e.g., partition by month, or move old logs to archive table) |
| JSONB queries on `dims` | GIN index exists but complex queries may be slow | As `dims` JSONB grows in complexity, filtering may degrade | Monitor query performance; consider extracting frequently-filtered fields to columns |
| Synchronous DB calls | All DB calls block event loop | Under concurrent load, event loop blocks cause high latency | Switch to async DB driver (asyncpg + AsyncSession) |
| Connection pooling | Configured but for sync engine | Sync pool (10 + 20 overflow) may be insufficient for async workload | Reconfigure for async engine with appropriate pool size |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|
| Migration system | No Alembic; schema managed by `create_all()` + manual SQL | High risk for production deployments; no rollback capability | **HIGH** - Required before production |
| Async DB support | Sync SQLAlchemy in async FastAPI | Performance degradation; blocks event loop | **HIGH** - Core architecture issue |
| Missing table | `dashboard_filters` not in DB | Feature gap; filter-dashboard relationship broken | **HIGH** - Fix immediately |
| Timestamp consistency | Mix of timezone-aware (ORM) and naive (DB) | Bugs in date handling; YOY calculations may be wrong | **HIGH** - Data integrity issue |
| Test infrastructure | Test DB missing; incomplete cleanup; sync engine in tests | Cannot reliably test; CI/CD broken | **HIGH** - Testing is foundational |
| JSON vs JSONB | ORM uses JSON (cross-platform), DB uses JSONB | Compatibility issue if switching DBs; minor | **LOW** - PostgreSQL-only app works fine |
| No DB roles | Single user (`postgres`) for all operations | Security risk; no principle of least privilege | **MEDIUM** - Set up dedicated app user with limited permissions |

---

## 9. Required Architectural Improvements

### 9.1 Critical (Do Immediately)

1. **Fix Async DB Support**
   - Install `asyncpg` driver
   - Switch to `sqlalchemy.ext.asyncio.create_async_engine`
   - Use `AsyncSession` in all routes
   - Update `get_db` dependency to yield async session
   - **Impact**: Unblocks event loop, enables true async behavior

2. **Create Missing `dashboard_filters` Table**
   - Run `Base.metadata.create_all()` or create migration
   - Verify many-to-many relationship works
   - **Impact**: Enables dashboard-filter associations

3. **Set Up Alembic Migrations**
   - Configure Alembic for PostgreSQL
   - Generate initial migration from current models
   - Apply migration to `bidb` database
   - **Impact**: Enables safe schema versioning and rollbacks

4. **Fix Timestamp Columns**
   - Alter all timestamp columns to `timestamp with time zone`
   - Verify ORM models have `DateTime(timezone=True)`
   - **Impact**: Prevents timezone-related bugs

5. **Set Up Test Database**
   - Create `bidb_test` database
   - Update `conftest.py` to use async engine (consistent with app)
   - Fix `clean_db` fixture to clean all tables
   - **Impact**: Enables reliable testing

### 9.2 Recommended (Before Production)

6. **Create Dedicated DB User**
   - Create app user with SELECT, INSERT, UPDATE, DELETE on tables
   - Create migration user with DDL permissions
   - Remove use of `postgres` superuser in app
   - **Impact**: Follows security best practices

7. **Add Composite Index**
   - Add index on `aggregated_data(dashboard_id, graph_id)`
   - Common query pattern for dashboard data retrieval
   - **Impact**: Prevents full table scans as data grows

8. **Add Archival Strategy for Logs**
   - Partition `processing_logs` by time (monthly)
   - Or create cleanup job to archive old logs
   - **Impact**: Prevents unbounded table growth

### 9.3 Optional (Future)

9. **Standardize Column Types**
   - Align DB column lengths with ORM (e.g., `varchar(255)` for emails)
   - Or document that `text` is intentional
   - **Impact**: Consistency, minor

10. **Add DB Monitoring**
    - Query performance monitoring
    - Connection pool monitoring
    - **Impact**: Operational visibility

---

## 10. Summary

### Critical Issues Found: 5
1. Synchronous DB in async FastAPI (blocks event loop)
2. Missing `dashboard_filters` table (broken feature)
3. No migration system (production risk)
4. Test database does not exist (tests broken)
5. Timestamp timezone mismatch (data integrity risk)

### Recommended Immediate Actions:
1. Set up async DB support with `asyncpg` and `AsyncSession`
2. Create `dashboard_filters` table
3. Configure Alembic migrations
4. Create `bidb_test` database
5. Fix timestamp columns to be timezone-aware

### Databases Requiring Attention:
- `bidb` - Fix schema drift, set up migrations
- `bidb_test` - Create database, fix test infrastructure

---

**End of Report**
