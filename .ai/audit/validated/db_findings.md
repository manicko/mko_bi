# Phase 03 Audit Findings — Database Architecture

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** yes (ruff, mypy passed; alembic check failed on model/migration drift)

---

## Findings

### DB-001: Model/migration drift on `processing_logs` index declaration

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/db/models/processing_logs.py`, `alembic/versions/b749bc53b1ee_add_processing_logs_status_index.py` |
| **Classification** | mandatory |

**Description:** The `ProcessingLog` model in `processing_logs.py` (lines 67-69) declares only `__table_args__ = (Index("idx_processing_logs_dashboard_id", "dashboard_id"),)` but the migration `b749bc53b1ee` creates `idx_processing_logs_status_finished_at ON processing_logs (status, finished_at)`. Alembic autogenerate detects this mismatch and reports "New upgrade operations detected: [('remove_index', ...)]", indicating it would drop the index that exists in the database. This creates a dangerous inconsistency where the database schema may diverge from the declared model on future migrations.

**Evidence:**
- Model declares: `idx_processing_logs_dashboard_id` (line 68) - matches database
- Migration creates: `idx_processing_logs_status_finished_at ON processing_logs (status, finished_at)` (line 23-24)
- Database has: Both indexes confirmed via `SELECT indexname, indexdef FROM pg_indexes`
- Alembic check output: "FAILED: New upgrade operations detected: [('remove_index', Index('idx_processing_logs_status_finished_at', ...))]"

**Recommendation:** Add the composite index declaration to `ProcessingLog.__table_args__`:
```python
__table_args__ = (
    Index("idx_processing_logs_dashboard_id", "dashboard_id"),
    Index("idx_processing_logs_status_finished_at", "status", "finished_at"),
)
```

**Effort:** trivial | **Priority:** mandatory (fixes alembic drift)

### DB-002: Missing index on `processing_logs.started_at` degrades stale log cleanup performance

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/db/starter.py` |
| **Classification** | advisory |

**Description:** The `cleanup_stale_processing_logs()` function in `data_worker.py` (lines 217-228) queries for stale processing logs using `started_at < cutoff` to detect jobs stuck in PROCESSING state. Once DB-001 is fixed by adding the index declaration, the existing `idx_processing_logs_status_finished_at` index is on `(status, finished_at)`, which does not support queries filtering by `started_at`. This forces an Index Scan with a Filter operation instead of a direct Index Scan, causing degraded performance as the table grows.

The `cleanup_old_logs()` function in `starter.py` (line 382) also uses `started_at < :cutoff` for log retention cleanup, compounding the performance impact.

**Evidence:**
- Query in `data_worker.py` line 218-219: `WHERE status = 'processing' AND started_at < cutoff`
- Query in `starter.py` line 382: `WHERE started_at < :cutoff AND status IN (:completed_status, 'failed')`
- Index exists: `idx_processing_logs_status_finished_at ON processing_logs (status, finished_at)` (will be declared in model after DB-001 fix)
- Missing index: `started_at` column has no dedicated index

Query plan from test database shows the index is used for status but requires a filter on `started_at`:
```
Update on processing_logs  (cost=0.14..8.17 rows=0 width=0)
  ->  Index Scan using idx_processing_logs_status_finished_at on processing_logs
        Index Cond: (status = 'processing'::processing_status)
        Filter: (started_at < (now() - '00:30:00'::interval))
```

Note: The `delete_old_logs()` function in `processing_log_repo.py` (line 352) correctly uses `finished_at < cutoff` which matches the existing composite index.

**Recommendation:** The stale log cleanup query uses `started_at < cutoff`. Either: (a) change the query to use `finished_at` instead (if semantically valid for detecting stuck jobs), or (b) add a composite index on `(status, started_at)` for efficient stale log detection. Option (b) is recommended since `started_at` is the natural field for detecting jobs that started but never completed.

**Effort:** trivial | **Priority:** recommended

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 0 |

## Mandatory Fixes

- DB-001: Model/migration drift on `processing_logs` index declaration (HIGH)

## Advisory Recommendations

- DB-002: Missing index on `processing_logs.started_at` for stale processing cleanup (MEDIUM)

## Doc Updates Needed

None