---
name: 03-database-validated-findings
description: Validated database architecture audit findings for mkobi BI Dashboard
validator: validator
template: .ai/audit/templates/audit-findings.md
status: complete
validated: yes
---

# Phase 03 Validated Findings — Database Architecture

**Validator:** validator  
**Status:** complete  
**Validated:** yes  

---

## Rejection Report

### DB-003 REJECTED: Inefficient Index for Filter Value Queries on dashboard_filter_values

| Field | Value |
|-------|-------|
| **Finding ID** | DB-003 |
| **Original Type** | [BEST-PRACTICE] |
| **Severity** | MEDIUM |
| **Rejection Reason** | Recommendation incorrect - a covering index already exists. The `uq_dashboard_filter_values` unique index on `(dashboard_id, filter_name, filter_value)` already covers the query pattern. The non-unique index is redundant overhead, but this is minor storage waste, not a critical performance issue. |

**Analysis Details:**

The query in `dashboard_filter_values_repo.py:44-50` filters on `dashboard_id` and `filter_name` and selects `filter_value` with ORDER BY `filter_value`. The unique index `uq_dashboard_filter_values` on `(dashboard_id, filter_name, filter_value)` covers all three columns and IS optimal for this query - it can serve index-only scans with rows naturally ordered by `filter_value`.

The recommendation to add a "covering index" is incorrect - a covering index already exists. The non-unique `idx_dashboard_filter_values_lookup` on `(dashboard_id, filter_name)` represents unnecessary storage overhead (duplicate leading columns without benefit). However, this is minor overhead on a small table, not a critical performance issue requiring action.

**Recommendation:** Rejected. The unique constraint index already provides optimal covering capability; removing the redundant non-unique index is optional micro-optimization.

---

### DB-004 REJECTED: Processing Config Table Missing updated_at Index

| Field | Value |
|-------|-------|
| **Finding ID** | DB-004 |
| **Original Type** | [BEST-PRACTICE] |
| **Severity** | LOW |
| **Rejection Reason** | Speculative recommendation. No codebase evidence of queries filtering or ordering by `updated_at` on `processing_configs` table. Premature optimization without demonstrated need. |

**Analysis Details:**

Evidence search found zero queries using `updated_at` for filtering, sorting, or cleanup operations on `processing_configs`:
- `processing_config_repo.py` queries only by `dashboard_id` (primary key lookup)
- `processing_config_service.py` reads/writes via dashboard_id only
- No cleanup or time-based queries exist

The finding acknowledges "Currently there's no evidence such queries exist" - making this speculative. Adding an index without a demonstrated use case violates the principle of avoiding overengineering.

**Recommendation:** Rejected. No action required.

---

### DB-005 REJECTED: Tables Using Primary Key Index Shows Zero Usage

| Field | Value |
|-------|-------|
| **Finding ID** | DB-005 |
| **Original Type** | [BEST-PRACTICE] |
| **Severity** | LOW |
| **Rejection Reason** | Correctly identified as test environment behavior, not a production issue. Small table sequential scans are query planner optimization, not a missing index problem. |

**Analysis Details:**

The finding correctly notes: "For small tables in test environment, sequential scans may be preferred by the query planner over index scans." This is accurate PostgreSQL behavior - for small tables, sequential scans are often faster than index traversal because the overhead of index navigation outweighs the benefit.

The primary key indexes exist and function correctly. The zero index usage on small tables (`users`, `registration_requests`, `layouts`) in a test database is expected behavior, not a defect requiring fixes. The recommendation to "monitor in production" is appropriate.

**Recommendation:** Rejected. Correctly characterized as monitoring item, not actionable finding.

---

## Approved Findings

### DB-001: Redundant Index on dashboard_filters Table

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Status** | APPROVED |
| **Classification** | mandatory fix |

**Evidence Verified:**
- Migration line 175: Creates `idx_dashboard_filters_dashboard_id` on `(dashboard_id, filter_id)`
- Migration line 170: PRIMARY KEY creates unique index `dashboard_filters_pkey` on same columns
- ORM line 88 in `filters.py`: Defines redundant `Index("idx_dashboard_filters_dashboard_id", "dashboard_id", "filter_id")`

The non-unique index is completely redundant since the primary key constraint already creates a unique index on the same column combination. Removing the redundant index reduces write overhead.

---

### DB-002: Missing Index on processing_logs.status Column

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Status** | APPROVED |
| **Classification** | mandatory fix |

**Evidence Verified:**

Query patterns using `status` filtering with and without `started_at`/`finished_at`:

1. `data_worker.py:122,139`: `status == ProcessingStatus.PROCESSING` AND `started_at < cutoff` (cleanup of stale processing logs)
2. `processing_log_repo.py:187`: `status == filters.status` (admin API filtering)
3. `processing_log_repo.py:349-350`: `status.in_([COMPLETED, FAILED])` AND `finished_at < cutoff` (delete old logs)
4. `file_cleanup.py:128-129`: `status.in_([COMPLETED, FAILED])` AND `finished_at < cutoff` (log cleanup service)

Only existing index: `idx_processing_logs_dashboard_id` on `dashboard_id`. No index covers `status` lookups, particularly the common cleanup pattern combining `status` + `started_at`/`finished_at`.

---

## Summary

| Status | Count |
|--------|-------|
| Approved | 2 |
| Rejected | 3 |

---

## Rollout Safety Analysis

**DB-001 (Redundant Index):**
- Safe to remove - no functional impact
- Can be done in any migration
- Rollback: simple index recreation if needed

**DB-002 (Missing Index):**
- Safe to add - PostgreSQL supports concurrent index creation
- For production: use `CREATE INDEX CONCURRENTLY` to avoid locks
- Rollback: simple index drop

---

## Required Fixes

1. **DB-001**: Remove redundant `idx_dashboard_filters_dashboard_id` index from migration and ORM model
2. **DB-002**: Add composite index on `(status, started_at)` for efficient stale processing log cleanup

---

## Advisory Recommendations

None. Rejected findings should not be implemented.