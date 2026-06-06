# Phase 07 Validation Report — Data Processing Pipeline

**Validator:** validator-agent
**Source:** .ai/audit/07-data-processing/findings.md
**Validation Date:** 2026-06-06

---

## Rejected Findings

### DP-003: REJECTED — MVP design with documented migration path is intentional

| Field | Value |
|-------|-------|
| **Original ID** | DP-003 |
| **Original Type** | SPEC-DEVIATION |
| **Original Classification** | mandatory |

**Rejection Reason:** This finding mischaracterizes an intentional MVP design. The `TaskQueue` implementation uses `asyncio.Queue` as explicitly documented in the code comments: "MVP: Uses in-memory queue (non-persistent, tasks lost on restart)". The SPEC.md (line 121) confirms this is a deliberate design decision with a documented migration path to Redis/RQ. The specification explicitly states "Background task queue — In-memory TaskQueue (MVP) with a documented migration path to Redis/RQ" as a key design decision. While the issue is real, it represents an **intentional MVP limitation**, not a spec deviation. The code matches the documented architecture. The recommendation to extend `cleanup_stale_processing_logs` to handle `UPLOADED` status is valid, but the classification as "SPEC-DEVIATION" is incorrect because the code correctly implements the MVP specification. Reclassify as **DOC-UPDATE** to document the limitation in user-facing documentation, or keep as **BEST-PRACTICE** advisory for future migration.

### DP-006: REJECTED — Documented limitation with acceptable scope for current use case

| Field | Value |
|-------|-------|
| **Original ID** | DP-006 |
| **Original Type** | BEST-PRACTICE |
| **Original Classification** | advisory |

**Rejection Reason:** The formula parser explicitly documents these limitations in the docstring (lines 66-71). The left-to-right evaluation without operator precedence and no parentheses support is a **conscious design trade-off** for a simple, safe expression parser. Given the current use case (computed fields in data processing), this is an acceptable limitation. The code is honest about its constraints. The recommendation to implement precedence/parentheses adds complexity that may not justify the ROI for the current user base. The existing comment already warns users ("Known limitations"). This should remain as documented behavior, not be escalated to a mandatory fix. If aggregation functions are later needed in formulas, reconsider. For now, reject as overengineering.

---

## Merged Findings (Cross-Phase Conflicts)

### Conflict: DP-001, DP-009, and DP-003 all require `cleanup_stale_processing_logs` extension

| Field | Value |
|-------|-------|
| **Merged From** | DP-001, DP-009, DP-003 |
| |

**Analysis:** Multiple findings independently identify the same remedial action: extending `cleanup_stale_processing_logs` to handle `UPLOADED` status entries. DP-001 (enqueue failure) and DP-009 (file orphaned on enqueue failure) both result in tasks stuck at `UPLOADED` with no recovery path. DP-003 (server restart) also results in `UPLOADED` entries being orphaned. While each finding describes different failure scenarios, they share the same root cause and remediation. **Recommendation:** Consolidate into a single finding addressing the broader issue of stale status recovery for both `UPLOADED` and `PROCESSING` states, with the fix being a unified cleanup extension.

---

## Reclassified Findings

### DP-003: SPEC-DEVIATION → DOC-UPDATE (or BEST-PRACTICE)

| Field | Value |
|-------|-------|
| **Original Type** | SPEC-DEVIATION |
| **New Type** | DOC-UPDATE |
| |

**Rationale:** The in-memory queue is intentional MVP behavior as documented in SPEC.md. The finding should be reclassified as `DOC-UPDATE` to document this limitation in user-facing documentation, or as `BEST-PRACTICE` advisory. The code correctly implements the MVP specification.

---

## Cross-Phase Conflicts with Other Audits

### Conflict with Database Audit: DB-006 and DP-001/DP-009 overlap on commit-before-enqueue

| Field | Value |
|-------|-------|
| **Conflicting IDs** | DB-006, DP-001, DP-009 |
| **Conflict Type** | Same root cause (commit before enqueue), different severity classification |

**Analysis:** The database audit validates DB-006 as SPEC-DEVIATION (mandatory) for "Processing Log Commits Before Background Job Enqueue". The data processing audit identifies DP-001 (CRITICAL, mandatory) and DP-009 (MEDIUM, advisory) addressing the same issue with file lifecycle coordination. These are **three perspectives on the same coordination problem**:

- DP-001: Enqueue failure leaves task stuck at UPLOADED (missing return value check)
- DP-009: File move before enqueue creates orphaned files (coordination issue)
- DB-006: Database commit before job enqueue is architecturally wrong

**Resolution:** DP-001 correctly identifies the critical bug (ignores return value). DP-009 correctly identifies the file lifecycle aspect. DB-006 correctly identifies the architectural pattern issue. All three should be consolidated into a single coordinated fix addressing: (1) check enqueue return value, (2) coordinate file lifecycle with enqueue success/failure, (3) consider architectural reordering.

### Conflict with Backend Audit (BE-0xx series): Transaction boundary patterns

| Field | Value |
|-------|-------|
| **Conflicting With** | Architecture patterns in BE phase |
| |

**Analysis:** The `data_worker.py` transaction patterns are **inconsistent**. The `_update_processing_log_status` function (lines 39-96) demonstrates proper transaction management with proper error handling. However, `_store_aggregates` (lines 351-523) has a problematic test-mode path where the code explicitly states "Caller manages the transaction (SAVEPOINT pattern)" but the caller (`_process_csv_file_async`) does not establish a transaction when `db_session` is provided. This creates an actual transaction boundary issue that **DP-004 correctly identifies** but the pattern inconsistency with other service layers should be noted.

---

## Rollout Safety Issues

### DP-002: Transaction atomicity rollback is high-risk

| Field | Value |
|-------|-------|
| **Finding ID** | DP-002 |
| **Risk** | HIGH |

**Issue:** Wrapping the entire processing pipeline in a single database transaction requires careful consideration:
1. The `_store_aggregates` function performs multiple database operations (graph queries, filter queries, aggregate saves, filter value saves)
2. The `_update_processing_log_status` creates separate sessions in production mode
3. A single-transaction approach would require **significant refactoring** of session management throughout `_process_csv_file_async`
4. The current multi-transaction design may be intentional to allow partial progress visibility

**Recommendation:** The fix is valid from a data consistency perspective, but the execution plan must carefully consider:
- How to handle long-running transactions (CSV processing can take minutes for large files)
- Whether to maintain the ability to observe intermediate progress
- The impact on connection pool utilization during large file processing

### DP-004: Test-mode transaction is low-risk but requires verification

The test-mode SAVEPOINT recommendation is **safe but low-ROI**. The test suite likely doesn't exercise partial failure scenarios within `_store_aggregates`. Before implementing, verify whether tests actually validate transaction rollback behavior in this function. If not, the fix adds complexity without immediate test coverage benefit.

---

## Validated Counts

| Classification | Count |
|----------------|-------|
| Mandatory | 3 (DP-001, DP-002, DP-008) |
| Advisory | 4 (DP-004, DP-005, DP-007, DP-009) |

---

## Summary

| Category | Count |
|----------|-------|
| Rejected | 2 |
| Merged/Conflicted | 1 |
| Reclassified | 1 |
| Mandatory Fixes | 3 (DP-001, DP-002, DP-008) |
| Advisory Recommendations | 4 (DP-004, DP-005, DP-007, DP-009) |

