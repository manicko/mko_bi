# Database Audit Report - BI Dashboard System

**Generated:** 2026-05-03  
**Auditor:** Automated Analysis  
**Scope:** PostgreSQL databases in mko_bi project

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | development | Main application database | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Manual (`create_db.sql`) + Alembic migrations |
| `bidb_test` | test | Automated testing | `DB_NAME=bidb_test` in conftest.py | Alembic migrations (via pytest) |

### DSN Details

**Main Database:**
```
postgresql://postgres:****@localhost:5432/bidb
```

**Test Database:**
```
postgresql+asyncpg://postgres:****@localhost:5432/bidb_test
```

---

## 2. Schema Documentation

### 2.1. Tables in `bidb` Database

#### `users`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| `email` | varchar(255) | NOT NULL | | UNIQUE |
| `password_hash` | varchar(255) | NOT NULL | | |
| `role` | user_role (enum) | NOT NULL | | CHECK: admin, editor, viewer |
| `is_active` | boolean | NOT NULL | true | |
| `created_at` | timestamp with time zone | NOT NULL | now() | |

**Indexes:**
- `users_pkey` (PRIMARY KEY, btree, id)
- `idx_users_email` (UNIQUE, btree, email)
- `idx_users_role` (btree, role)

---

#### `layouts`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| `name` | varchar(255) | NOT NULL | | UNIQUE |
| `definition` | jsonb | NOT NULL | | |
| `created_at` | timestamp with time zone | NOT NULL | now() | |

**Indexes:**
- `layouts_pkey` (PRIMARY KEY, btree, id)
- `idx_layouts_name` (UNIQUE, btree, name)

---

#### `dashboards`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| `name` | varchar(255) | NOT NULL | | UNIQUE |
| `description` | text | YES | | |
| `layout_id` | uuid | YES | | FK → layouts(id) ON DELETE SET NULL |
| `created_by` | uuid | YES | | FK → users(id) ON DELETE SET NULL |
| `config` | jsonb | NOT NULL | '{}' | |
| `created_at` | timestamp with time zone | NOT NULL | now() | |
| `updated_at` | timestamp with time zone | NOT NULL | now() | |

**Indexes:**
- `dashboards_pkey` (PRIMARY KEY, btree, id)
- `idx_dashboards_name` (UNIQUE, btree, name)

---

#### `graphs`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| `dashboard_id` | uuid | NOT NULL | | FK → dashboards(id) ON DELETE CASCADE |
| `name` | varchar(255) | NOT NULL | | |
| `type` | graph_type (enum) | NOT NULL | | CHECK: bar, line, pie, table |
| `config` | jsonb | NOT NULL | | |
| `dimensions` | jsonb | NOT NULL | | |
| `metrics` | jsonb | NOT NULL | | |
| `created_at` | timestamp with time zone | NOT NULL | now() | |

**Constraints:**
- `idx_graphs_dashboard_name` (UNIQUE, dashboard_id, name)

**Indexes:**
- `graphs_pkey` (PRIMARY KEY, btree, id)

---

#### `filters`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| `name` | varchar(255) | NOT NULL | | UNIQUE |
| `type` | filter_type (enum) | NOT NULL | | |
| `config` | jsonb | NOT NULL | | |
| `created_at` | timestamp with time zone | NOT NULL | now() | |

**Indexes:**
- `filters_pkey` (PRIMARY KEY, btree, id)
- `idx_filters_name` (UNIQUE, btree, name)

---

#### `dashboard_access`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `user_id` | uuid | NOT NULL | | FK → users(id) ON DELETE CASCADE |
| `dashboard_id` | uuid | NOT NULL | | FK → dashboards(id) ON DELETE CASCADE |
| `permission` | dashboard_permission_level (enum) | NOT NULL | | CHECK: view, edit, admin |

**Primary Key:** (user_id, dashboard_id)

**Indexes:**
- `dashboard_access_pkey` (PRIMARY KEY, btree, user_id, dashboard_id)
- `idx_dashboard_access_user` (btree, user_id)
- `idx_dashboard_access_dashboard` (btree, dashboard_id)

---

#### `dashboard_filters`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `dashboard_id` | uuid | NOT NULL | | FK → dashboards(id) ON DELETE CASCADE |
| `filter_id` | uuid | NOT NULL | | FK → filters(id) ON DELETE CASCADE |

**Primary Key:** (dashboard_id, filter_id)

**Indexes:**
- `dashboard_filters_pkey` (PRIMARY KEY, btree, dashboard_id, filter_id)
- `idx_dashboard_filters_dashboard_filter` (btree, dashboard_id, filter_id)

---

#### `processing_configs`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `dashboard_id` | uuid | NOT NULL | | PRIMARY KEY, FK → dashboards(id) ON DELETE CASCADE |
| `settings` | jsonb | NOT NULL | | |
| `updated_at` | timestamp with time zone | NOT NULL | now() | |

**Indexes:**
- `processing_configs_pkey` (PRIMARY KEY, btree, dashboard_id)

---

#### `processing_logs`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | uuid | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| `dashboard_id` | uuid | YES | | FK → dashboards(id) ON DELETE SET NULL |
| `status` | text | NOT NULL | | CHECK: started, success, failed |
| `message` | varchar(1000) | YES | | |
| `started_at` | timestamp with time zone | YES | | |
| `finished_at` | timestamp with time zone | YES | | |

**Indexes:**
- `processing_logs_pkey` (PRIMARY KEY, btree, id)

---

#### `aggregated_data`
| Column | Type | Nullable | Default | Constraints |
|---|---|---|---|---|
| `id` | integer | NOT NULL | nextval('aggregated_data_id_seq') | PRIMARY KEY |
| `dashboard_id` | uuid | NOT NULL | | FK → dashboards(id) ON DELETE CASCADE |
| `graph_id` | uuid | NOT NULL | | FK → graphs(id) ON DELETE CASCADE |
| `dims` | jsonb | NOT NULL | | |
| `metrics` | jsonb | NOT NULL | | |

**Indexes:**
- `aggregated_data_pkey` (PRIMARY KEY, btree, id)
- `idx_aggregated_data_dashboard_id` (btree, dashboard_id)
- `idx_aggregated_data_graph_id` (btree, graph_id)
- `idx_aggregated_data_dims_gin` (GIN, dims)

---

### 2.2. Enum Types

| Enum Name | Values |
|---|---|
| `user_role` | admin, editor, viewer |
| `dashboard_permission_level` | view, edit, admin |
| `graph_type` | bar, line, pie, table |
| `filter_type` | select, multiselect, range, date |
| `processing_status` | started, success, failed |

---

### 2.3. Extensions

| Extension | Schema | Description |
|---|---|---|
| `uuid-ossp` | public | Generate universally unique identifiers (UUIDs) |

---

## 3. Schema Drift Report

| Object | Problem | ORM Model | Alembic Migration | Real DB | Recommended Source of Truth |
|---|---|---|---|---|---|
| `aggregated_data.id` | Type mismatch: SPEC says BIGSERIAL, DB has integer | Integer | e86f3c8f7324 changes BIGINT→Integer | integer (not bigint) | Change to BIGSERIAL for capacity |
| `layouts.definition` | ORM uses JSON, DB has JSONB | JSON (wrong!) | 57f43a5c499d should fix | jsonb | Fix ORM to use JSONB |
| `dashboard_filters` | Not in SPEC.md | Present | e86f3c8f7324 creates it | Present | Add to SPEC or justify existence |
| `processing_logs.status` | SPEC says TEXT with CHECK | Using enum via model | Creates enum type | text with CHECK constraint | Standardize on enum type |
| Index naming | Inconsistent naming | N/A | 840a99edb818 standardizes | Standardized | Keep standardized names |

---

## 4. Migration Audit

| Check | Status | Notes |
|---|---|---|
| Migration chain integrity | PASS | All 4 migrations apply cleanly |
| Reproducibility from scratch | RISKY | Initial migration e86f3c8f7324 contains many ALTER statements suggesting manual DB creation first |
| Non-idempotent operations | WARN | e86f3c8f7324 drops and recreates constraints |
| Broken revisions | PASS | No broken revisions found |
| Cyclical dependencies | PASS | No circular dependencies |
| `alembic upgrade head` on empty DB | UNTESTED | Not verified in this audit |
| Schema-only vs data migrations | PASS | Migrations are schema-only |

### Migration Chain

```
e86f3c8f7324 (initial) → 57f43a5c499d (JSON→JSONB) → 2aa835fe1fac (composite index) → 840a99edb818 (standardize names)
```

**Current Version:** `840a99edb818`

---

## 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|---|---|---|---|
| Development | `bidb` | SEPARATE | LOW - Separate database |
| Test | `bidb_test` | SEPARATE | LOW - Separate database, uses TRUNCATE for cleanup |
| Production | Not configured | N/A | N/A |

### Test Database Details

- **Isolation:** PHYSICALLY SEPARATE database (`bidb_test`)
- **DSN:** Configured in `conftest.py` with `DB_NAME=bidb_test`
- **Cleanup Strategy:** TRUNCATE TABLE CASCADE after each test function
- **Migration Strategy:** Assumed to be applied before test session (not in `pytest_sessionstart`)
- **Risk Level:** SAFE - Properly isolated from dev/prod

---

## 6. Architectural Problems

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| **HIGH** | Schema Design | `aggregated_data.id` | Using `integer` instead of `bigint`/`BIGSERIAL` | Will overflow after ~2.1B rows, causing insert failures | Change to `BIGSERIAL` or `bigint` with sequence | Dashboard aggregation data will grow unbounded; integer overflow will cause production outage |
| **HIGH** | Migrations | `e86f3c8f7324` initial migration | Migration does ALTER TABLE changes that suggest DB was created manually first | Hard to reproduce from scratch; migration may fail on clean DB | Rebase migrations: create proper initial migration that creates tables from scratch | Reproducibility is critical for onboarding, CI/CD, and disaster recovery |
| **MEDIUM** | Schema Design | `layouts.definition` | ORM model uses `JSON` while DB has `JSONB` | Inconsistency between ORM and DB; potential issues with PostgreSQL-specific features | Change ORM to use `JSONB` (already done in migration 57f43a5c499d, but model not updated) | JSONB provides better performance and GIN index support |
| **MEDIUM** | Maintainability | Index naming | Mixed naming conventions across codebase | Confusion when debugging; hard to predict index names | Already fixed in 840a99edb818; verify consistency | Consistent naming reduces cognitive load |
| **MEDIUM** | Test Isolation | Test cleanup | Uses TRUNCATE which doesn't reset sequences | Sequence values keep growing; may cause confusion in tests | Use DROP/CREATE or reset sequences after cleanup | Predictable test state is important for reproducibility |
| **LOW** | Schema Design | `processing_logs` | No index on `dashboard_id` | Slow queries when filtering logs by dashboard | Add btree index on `dashboard_id` | Log table will grow; queries need to be efficient |
| **LOW** | Maintainability | Enum types | Mix of CHECK constraints and enum types | Inconsistency in how constraints are defined | Standardize on PostgreSQL enums (already mostly done) | Enums are more explicit and PostgreSQL-native |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|
| `aggregated_data` table | **HIGH** - Uses `integer` for PK | After ~2.1B rows, inserts fail with overflow error | Change to `BIGSERIAL` immediately |
| `aggregated_data` table | **MEDIUM** - No partitioning strategy | Table scan slowdown as data grows beyond memory | Monitor growth; consider partitioning by `dashboard_id` or time if needed |
| `processing_logs` table | **MEDIUM** - Unbounded growth | Table becomes slow; backup/restore takes long | Implement log rotation/archival strategy |
| `aggregated_data.dims` GIN index | **LOW** - JSONB GIN index overhead | Slower INSERT performance as index grows | Monitor INSERT performance; current approach is correct for JSONB filtering |
| Concurrent users | **LOW** - No connection pooling config observed | Connection exhaustion under load | Configure `pool_size` and `max_overflow` in async engine |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|
| Migration history | Initial migration is a "change migration" not "create migration" | Hard to reproduce; risky for new environments | HIGH - Rebase migrations |
| `aggregated_data.id` type | Integer instead of BigInt | Will overflow | HIGH - Fix before production |
| `layouts` ORM model | Uses JSON instead of JSONB | Inconsistency | MEDIUM - Fix model |
| Test DB setup | Not automated in pytest session | Manual step required | MEDIUM - Add fixture |
| `processing_logs` | No index on dashboard_id | Slow queries | LOW - Add index |
| Sequence handling in tests | TRUNCATE doesn't reset sequences | Unpredictable test data | LOW - Reset sequences |

---

## 9. Required Architectural Improvements

### 9.1. CRITICAL: Fix `aggregated_data.id` Type

**Problem:** The `aggregated_data` table uses `integer` for the primary key, which will overflow after ~2.1 billion rows.

**Required Change:**
```sql
-- Migration to change integer to bigint
ALTER TABLE aggregated_data ALTER COLUMN id TYPE bigint;
ALTER SEQUENCE aggregated_data_id_seq AS bigint;
```

**Why It Matters:** Dashboard aggregation data grows over time. Integer overflow will cause production failure. This is a simple fix now but becomes expensive after data accumulates.

---

### 9.2. HIGH: Rebase Alembic Migrations

**Problem:** The initial migration `e86f3c8f7324` contains ALTER statements that suggest the database was created manually first, then migrations were generated. This makes reproduction from scratch unreliable.

**Required Change:**
1. Create a clean initial migration that creates all tables from scratch
2. Ensure `alembic upgrade head` works on a completely empty database
3. Remove the ALTER-heavy initial migration

**Why It Matters:** Reproducibility is essential for:
- New developer onboarding
- CI/CD pipeline setup
- Disaster recovery
- Creating test databases

---

### 9.3. MEDIUM: Fix `layouts.definition` ORM Model

**Problem:** The ORM model `layouts.py` uses `JSON` while the database has `JSONB`. The migration `57f43a5c499d` attempts to fix this, but the model itself wasn't updated.

**Required Change:**
In `src/mko_bi/db/models/layout.py`:
```python
# Change:
definition: Mapped[dict[str, object]] = mapped_column(
    JSON,
    nullable=False,
    default=dict,
)

# To:
from sqlalchemy.dialects.postgresql import JSONB
definition: Mapped[dict[str, object]] = mapped_column(
    JSONB,
    nullable=False,
    default=dict,
)
```

**Why It Matters:** Using the correct type in ORM ensures compatibility and enables PostgreSQL-specific JSONB features.

---

### 9.4. MEDIUM: Add Index to `processing_logs.dashboard_id`

**Problem:** The `processing_logs` table has no index on `dashboard_id`, which will slow down queries filtering logs by dashboard.

**Required Change:**
```sql
CREATE INDEX idx_processing_logs_dashboard_id ON processing_logs(dashboard_id);
```

**Why It Matters:** As the log table grows, queries need to be efficient. This is a simple fix with high impact.

---

### 9.5. LOW: Reset Sequences in Test Cleanup

**Problem:** Tests use TRUNCATE to clean up, but this doesn't reset sequences. This can lead to unpredictable test data.

**Required Change:**
In `conftest.py`, after TRUNCATE:
```python
# Reset sequences
await conn.execute(text("ALTER SEQUENCE aggregated_data_id_seq RESTART WITH 1"))
```

---

## 10. Summary of Findings

### Critical Issues (Fix Immediately)
1. `aggregated_data.id` uses `integer` instead of `bigint`/`BIGSERIAL`

### High Priority (Fix Before Production)
1. Rebase Alembic migrations for reproducibility
2. Fix `layouts` ORM model to use JSONB

### Medium Priority (Fix in Near Term)
1. Add index on `processing_logs.dashboard_id`
2. Automate test database setup in pytest

### Low Priority (Nice to Have)
1. Reset sequences in test cleanup
2. Standardize enum type usage across all tables

---

## 11. Compliance Checklist

| Requirement | Status | Notes |
|---|---|---|
| UUID primary keys | PASS | All tables use UUID except `aggregated_data` (integer - PROBLEM) |
| JSONB for flexible data | MOSTLY PASS | `layouts` model uses JSON, but DB has JSONB |
| Timezone-aware timestamps | PASS | All timestamp columns use `timestamp with time zone` |
| Foreign key constraints | PASS | All relationships have proper FKs with CASCADE/SET NULL |
| Async-compatible drivers | PASS | Uses `asyncpg` for async operations |
| Test DB isolation | PASS | Separate `bidb_test` database |
| Enum types for constrained values | PASS | Uses PostgreSQL enums |
| GIN index for JSONB filtering | PASS | `aggregated_data.dims` has GIN index |
| Migration chain integrity | PASS | All migrations apply cleanly |
| Reproducible from scratch | RISKY | Initial migration is problematic |

---

## 12. Recommended Action Plan

1. **Immediate (This Week):**
   - Create migration to change `aggregated_data.id` from `integer` to `bigint`
   - Fix `layouts` ORM model to use `JSONB`

2. **Before Production (Next Sprint):**
   - Rebase Alembic migrations to enable clean reproduction
   - Add index on `processing_logs.dashboard_id`
   - Document the database setup process

3. **Ongoing:**
   - Monitor `aggregated_data` and `processing_logs` growth
   - Consider archival strategy for old data
   - Automate test database setup

---

**End of Report**
