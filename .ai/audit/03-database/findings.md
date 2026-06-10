---
name: 03-database-audit-findings
description: Database architecture audit findings for mkobi BI Dashboard
executor: auditor
template: .ai/audit/templates/audit-findings.md
status: complete
validated: no
---

# Phase 03 Audit Findings — Database Architecture

**Executor:** auditor  
**Template:** `.ai/audit/templates/audit-findings.md`  
**Status:** complete  
**Validated:** no

---

## Findings

### DB-001: Redundant Index on dashboard_filters Table

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Affected Modules** | `alembic/versions/000000000000_initial_migration.py`, `src/mkobi/db/models/filters.py` |
| **Classification** | advisory |

**Description:** The `dashboard_filters` junction table has a redundant index. The `dashboard_filters_pkey` unique index on `(dashboard_id, filter_id)` makes the `idx_dashboard_filters_dashboard_id` index on the same columns unnecessary. When an index is unique on a set of columns, a non-unique index on the same columns provides no additional benefit and only adds write overhead.

**Evidence:**
```sql
-- From pg_index query:
SELECT i.relname as indexname, indkey, indisunique FROM pg_index 
WHERE indrelid = 'dashboard_filters'::regclass::oid;

indexname: dashboard_filters_pkey, indkey: 1 2, indisunique: t
indexname: idx_dashboard_filters_dashboard_id, indkey: 1 2, indisunique: f
```

Both indexes reference columns 1 and 2 (`dashboard_id`, `filter_id`) with identical column ordering. The migration file at line 82-88 in `alembic/versions/000000000000_initial_migration.py` creates both indexes, and `src/mkobi/db/models/filters.py` at line 88 defines the same redundant index in ORM.

**Recommendation:** Remove the redundant `idx_dashboard_filters_dashboard_id` index from the migration file and ORM model. The unique primary key index already provides the same lookup performance.

**Effort:** trivial  
**Priority:** recommended

---

### DB-002: Missing Index on processing_logs.status Column

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Affected Modules** | `alembic/versions/000000000000_initial_migration.py`, `src/mkobi/db/models/processing_logs.py`, `src/mkobi/db/repositories/processing_log_repo.py` |
| **Classification** | advisory |

**Description:** The `processing_logs` table is frequently filtered by `status` (e.g., `ProcessingLog.status == ProcessingStatus.PROCESSING` in cleanup queries at `src/mkobi/workers/data_worker.py:122,139`), but no index exists on the `status` column. The `cleanup_stale_processing_logs` function queries by both `status` and `started_at`, which would benefit from a composite index.

**Evidence:**
- Query pattern in `src/mkobi/db/repositories/processing_log_repo.py:187`: `.where(ProcessingLog.status == filters.status)`
- Query pattern in `src/mkobi/workers/data_worker.py:122`: `ProcessingLog.status == ProcessingStatus.PROCESSING` combined with `started_at < cutoff`
- Current indexes: Only `processing_logs_pkey` (on `id`) and `idx_processing_logs_dashboard_id` exist
- Runtime evidence shows the primary key index is never used for lookups by status (idx_scan = 0 in test DB queries)

**Recommendation:** Add a composite index on `(status, started_at)` for efficient stale processing log cleanup queries. If status-only queries are common in the admin API, consider a separate index on `status` alone.

**Effort:** small  
**Priority:** recommended

---

### DB-003: Inefficient Index for Filter Value Queries on dashboard_filter_values

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Affected Modules** | `alembic/versions/000000000002_add_dashboard_filter_values_table.py`, `src/mkobi/db/models/dashboard_filter_values.py` |
| **Classification** | advisory |

**Description:** The `get_filter_values` query in `DashboardFilterValuesRepository` filters by `(dashboard_id, filter_name)` but `idx_dashboard_filter_values_lookup` has 112 scans with 0 tuple reads, suggesting queries aren't efficiently using the index. The unique constraint index `uq_dashboard_filter_values` on `(dashboard_id, filter_name, filter_value)` could potentially serve as an index skip scan for the lookup pattern, but the leading column pattern differs.

**Evidence:**
- Query in `src/mkobi/db/repositories/dashboard_filter_values_repo.py:44-50`: filters on `dashboard_id` and `filter_name` only
- Current index definition: `CREATE INDEX idx_dashboard_filter_values_lookup ON dashboard_filter_values (dashboard_id, filter_name)`
- Index stats: 112 scans, 0 tuple reads — indicates index-only scans aren't happening or queries need optimization
- Unique index: `uq_dashboard_filter_values` on `(dashboard_id, filter_name, filter_value)` exists but is unique, not optimal for range scans

**Recommendation:** Consider adding a covering index or including the `filter_value` column in the index to enable index-only scans for the common filter value retrieval pattern. Alternatively, investigate whether the GIN index approach or a different query pattern would be more efficient.

**Effort:** small  
**Priority:** recommended

---

### DB-004: Processing Config Table Missing updated_at Index

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Affected Modules** | `alembic/versions/000000000000_initial_migration.py`, `src/mkobi/db/models/processing_configs.py` |
| **Classification** | advisory |

**Description:** The `processing_configs` table has an `updated_at` column updated by a trigger, but no index exists on this column. If there are time-based queries or cleanup operations on old configurations, they would require full table scans.

**Evidence:**
- ORM model at `src/mkobi/db/models/processing_configs.py:39` defines `updated_at` with trigger-managed values
- Migration at `alembic/versions/000000000000_initial_migration.py:180-186` creates a trigger for `updated_at` but no index on `updated_at` column
- Only index: `processing_configs_pkey` on `dashboard_id`

**Recommendation:** Add an index on `updated_at` if time-based queries or cleanup operations on old processing configurations are planned. Currently there's no evidence such queries exist, but this should be documented or the column removed if unused.

**Effort:** trivial  
**Priority:** recommended

---

### DB-005: Tables Using Primary Key Index Shows Zero Usage

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Affected Modules** | `alembic/versions/000000000000_initial_migration.py`, ORM models for `users`, `registration_requests`, `layouts` |
| **Affected Tables** | `users`, `registration_requests`, `layouts` |
| **Classification** | advisory |

**Description:** Production query patterns may differ, but in the test database, primary key indexes on `users`, `registration_requests`, and `layouts` show zero tuple reads despite sequential scans on these tables. This indicates queries are not using index lookups as expected, which is unusual for tables with primary keys.

**Evidence:**
- Query: `SELECT relname, seq_scan, idx_scan FROM pg_stat_user_tables`
- Results: `users` has 116 seq_scans, 0 idx_scans; `registration_requests` has 3 seq_scans, 0 idx_scans; `layouts` has 2 seq_scans, 0 idx_scans
- For small tables in test environment, sequential scans may be preferred by the query planner over index scans, but this pattern should be verified for production

**Recommendation:** Monitor index usage in production. If primary key lookups via ID queries are used in production and still not using indexes, investigate query patterns and ensure proper parameter binding.

**Effort:** trivial  
**Priority:** recommended

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 3 |

## Advisory Recommendations

- DB-001: Redundant index on dashboard_filters table
- DB-002: Missing index on processing_logs.status column
- DB-003: Inefficient index for filter value queries on dashboard_filter_values
- DB-004: Processing config table missing updated_at index
- DB-005: Tables using primary key index shows zero usage (monitor in production)

---

## Notes

- Migration chain integrity verified: Linear chain from base → 000000000000 → 000000000001 → 000000000002 → 4479eb53fd4e (head), no forks detected
- All constraints validated (`convalidated = t`): Foreign keys, not-null constraints, and check constraints are properly enforced
- ENUM types match between Python StrEnum and PostgreSQL: `user_role`, `dashboard_permission_level`, `graph_type`, `filter_type`, `processing_status`, `registration_status` all have matching values
- Test database isolation verified: Tests run against isolated `bidb_test` database with separate volumes and ports
- Transaction handling verified: StorageManager and data_worker use single transaction contexts with proper rollback on errors
- Advisory lock in alembic/env.py prevents concurrent migrations: Implementation verified as correct