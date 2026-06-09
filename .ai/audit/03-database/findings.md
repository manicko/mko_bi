# Phase 03 Audit Findings — Database Architecture

**Executor:** audit-executor
**Template:** `.ai/audit/templates/audit-findings.md`
**Status:** complete
**Validated:** no

---

## Findings

### DB-001: No-op migration without proper downgrade handling

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | alembic/versions/000000000001_add_missing_fk_indexes.py |
| **Classification** | advisory |

**Description:** Migration `000000000001_add_missing_fk_indexes.py` is a no-op migration with empty `upgrade()` and `downgrade()` functions. While documented as intentional (indexes are now created in initial migration), the migration chain could be simplified by removing this unnecessary migration.

**Evidence:**
- File: alembic/versions/000000000001_add_missing_fk_indexes.py, lines 21-27 - upgrade() and downgrade() contain only `pass`
- Migration history shows 3 revisions: 000000000000 -> 000000000001 (no-op) -> 4479eb53fd4e

**Recommendation:** Either remove `000000000001` migration entirely or document why it must remain. Consider squashing migrations if this creates operational complexity.

---

### DB-002: Missing GIN index on graphs JSONB columns

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/graphs.py, alembic/versions/000000000000_initial_migration.py |
| **Classification** | advisory |

**Description:** The `graphs` table has JSONB columns (`config`, `dimensions`, `metrics`) without GIN indexes, while `aggregated_data.dims` has a GIN index. If queries filter on these JSONB fields, full table scans will occur.

**Evidence:**
- File: alembic/versions/000000000000_initial_migration.py, lines 114-125 - Creates graphs table with JSONB config, dimensions, metrics - no GIN indexes
- File: alembic/versions/000000000000_initial_migration.py, lines 201-209 - Creates idx_aggregated_data_dims_gin on aggregated_data (dims) using GIN

**Recommendation:** Add GIN indexes on frequently queried JSONB columns (graphs.config, dashboards.config, filters.config) if queries filter on these fields.

---

### DB-003: No archival strategy for growing aggregated_data table

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table uses BIGSERIAL primary key and grows monotonically with each file upload. There is no archival or partitioning strategy implemented, which could lead to unbounded table growth and performance degradation over time.

**Evidence:**
- File: src/mkobi/db/models/aggregated_data.py, lines 64-68 - id column is BigInteger with autoincrement=True and no partitioning
- cleanup_old_logs in starter.py only cleans processing_logs, not aggregated_data

**Recommendation:** Implement table partitioning on aggregated_data by dashboard_id or created_date range, or add an archival job to move old data to cold storage.

---

### DB-004: ENUM migration history inconsistency - initial migration defines different values than current model

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/models/enums.py, alembic/versions/000000000000_initial_migration.py, alembic/versions/4479eb53fd4e_remove_unused_success_value_from_.py |
| **Classification** | advisory |

**Description:** The initial migration (000000000000) creates `processing_status` enum WITH a `success` value, but the current ProcessingStatus model enum does NOT include `success`. A subsequent migration (4479eb53fd4e) removes the `success` value. While the current database state is correct, this creates a gap where databases created before migration 4479eb53fd4e would have an extra enum value. The issue is resolved in the current DB but represents a historical inconsistency.

**Evidence:**
- Current database enum values: started, uploaded, processing, completed, failed (5 values, no success)
- File: src/mkobi/models/enums.py, line 65: FAILED = "failed" (no SUCCESS)
- File: alembic/versions/000000000000_initial_migration.py, lines 38-47: Creates processing_status enum with `success` value
- File: alembic/versions/4479eb53fd4e_remove_unused_success_value_from_.py: Migrations `success` out
- alembic_version table: 4479eb53fd4e (current)

**Recommendation:** Consider consolidating migrations or documenting that databases must be upgraded to head. No immediate action required as current state is correct.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 4 |
| LOW | 0 |

## Mandatory Fixes

None

## Advisory Recommendations

- DB-001: No-op migration without proper downgrade handling
- DB-002: Missing GIN index on graphs JSONB columns
- DB-003: No archival strategy for growing aggregated_data table
- DB-004: ENUM migration history inconsistency - initial migration defines different values than current model

---

## Notes

- Test and dev databases are at correct migration revision (4479eb53fd4e)
- All foreign key constraints are validated (convalidated = t)
- All enum types in database match the current ProcessingStatus enum (no success value)
- Migration chain is linear without forks
- Test isolation uses SAVEPOINT pattern with xdist database isolation