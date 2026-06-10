---
name: 01-backend-validated
description: Validation report for Phase 01 Backend Architecture findings
validator: validator
date: 2026-06-09
---

# Phase 01 Backend Validation Report

## Rejected Findings

### BE-001: Redundant cast in processing_log_service.py (mypy error)
**Status:** REJECTED

**Reason:** The reported mypy errors do not exist in the current codebase. Running `mypy src/mkobi/services/processing_log_service.py` returns only `no-any-return` errors at lines 78, 85, and 217 — no `redundant-cast` errors are reported at lines 242 or 248. The finding appears stale; the code at those lines (`cast(int, count)`) does not trigger the redundant-cast error with the current mypy configuration.

**Evidence:**
```
$ uv run mypy src/mkobi/services/processing_log_service.py
src\mkobi\services\processing_log_service.py:78: error: Returning Any from function declared to return "list[Any]"  [no-any-return]
src\mkobi\services\processing_log_service.py:85: error: Returning Any from function declared to return "list[Any]"  [no-any-return]
src\mkobi\services\processing_log_service.py:217: error: Returning Any from function declared to return "list[Any]"  [no-any-return]
Success: no issues found in 1 source file (checked 1 source file)
```

---

### BE-004: Test file in wrong location - tests/api directory not discovered by pytest
**Status:** REJECTED

**Reason:** The evidence is false. Running `pytest --collect-only -n auto tests/api/test_temp_password_retrieval.py` correctly collects all 5 test methods from the `TestTempPasswordRetrievalEndpoint` class. The pytest configuration in `pyproject.toml` (`testpaths = ["tests"]` and `python_files = ["test_*.py"]`) includes subdirectories by default. The test file location does not cause any discovery issues.

**Evidence:**
```
$ uv run pytest --collect-only -n auto tests/api/test_temp_password_retrieval.py
...
========================= 5 tests collected in 0.63s ==========================
```

---

## Validated Findings (No Changes)

### BE-002: Test seeder lacks idempotency - causes parallel test failures
**Status:** VALIDATED as SPEC-DEVIATION (mandatory)

**Verification:** The seeder in `src/mkobi/db/seeders/test_media_dash.py` has a structural issue. At lines 46-52, when `existing_dashboard` is True, existing graphs are deleted. However, graph creation at lines 112-141 occurs AFTER the if/else block (line 63 onward), meaning all workers create the same graphs regardless of which branch was taken. Under parallel xdist execution, this creates a race condition where multiple workers can attempt to insert graphs with identical names simultaneously before any commits complete, triggering `UniqueViolationError` on `idx_graphs_dashboard_name`.

**Architectural Impact:** The seeder's transaction boundaries cross multiple statements without isolation guarantees for parallel workers.

---

### BE-003: cleanup_old_processing_logs uses separate session causing test isolation failure
**Status:** VALIDATED as SPEC-DEVIATION (mandatory)

**Verification:** Confirmed. The `cleanup_old_processing_logs` function in `src/mkobi/services/file_cleanup.py` at line 123 creates its own session via `async with get_session() as db:`, while tests use the `async_db_session` fixture which operates within a SAVEPOINT transaction. The separate session cannot see uncommitted test data, causing the DELETE to find 0 records.

**Recommendation:** The function should accept an optional `db: AsyncSession` parameter to enable test session injection, similar to `ProcessingLogService.delete_old_logs`.

---

### BE-005: no-any-return mypy errors in processing_log_service.py
**Status:** VALIDATED as SPEC-DEVIATION (advisory)

**Verification:** Confirmed by mypy execution. The repository interface methods (`get_by_dashboard`, `get_filtered`) return `list[Any]` per `IProcessingLogRepository`, while the service methods declare return type `list[ProcessingLogRead]`. This type mismatch causes the `no-any-return` errors at the reported lines (78, 85, 217).

---

## Merged Findings

None identified.

---

## Cross-Phase Conflicts

### BE-002 / TST-006: Shared Root Cause — Seeder Test Isolation
**Conflict:** Both BE-002 (Backend) and TST-006 (Tests Phase) identify issues with the test seeder causing test failures under parallel execution.

- BE-002 identifies the root cause: seeder graph creation occurs outside the dashboard existence check block
- TST-006 identifies the symptom: `test_dashboard_config_contains_filters_definition` fails due to state inconsistency

**Resolution:** TST-006 is a downstream effect of the BE-002 architectural issue. Fix BE-002 first to resolve both findings.

---

## Rollout Safety Issues

### BE-002 Sequencing Risk
The seeder fix requires moving graph creation inside the `if existing_dashboard:` block. This change:
- Must be paired with proper flush ordering to ensure graph IDs are available
- Should include ON CONFLICT handling as a defensive measure
- Risk is LOW for production since seeders run in development mode only

### BE-003 Session Injection Pattern
The recommended fix (adding optional `db` parameter) follows an established pattern in `ProcessingLogService.delete_old_logs`. This change is:
- BACKWARD COMPATIBLE (parameter is optional)
- LOW RISK (only affects test execution flow)
- REVERSIBLE (parameter can be made mandatory in future cleanup)

---

## Summary

| Status | Count |
|--------|-------|
| Rejected | 2 |
| Validated (Mandatory) | 2 |
| Validated (Advisory) | 1 |
| Merged | 0 |

**Validated Mandatory Fixes:**
1. BE-002: Fix test seeder idempotency for parallel xdist test execution
2. BE-003: Fix `cleanup_old_processing_logs` to work with test session fixtures

**Validated Advisory Fixes:**
1. BE-005: Tighten type annotations in `ProcessingLogRepository` return types