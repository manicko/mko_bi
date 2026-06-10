---
name: 01-backend
status: complete
validated: no
executor: auditor
problems-only: true
---

# Phase 01 Audit — Backend Architecture

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete

---

## Findings

### BE-001: Redundant cast in processing_log_service.py (mypy error)

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/processing_log_service.py |
| **Classification** | advisory |

**Description:** Mypy reports redundant cast to "int" at lines 242 and 248. The `delete_old_logs` method in `ProcessingLogService` uses `cast(int, count)` but `count` is already typed as `int` by the repository's return type annotation. This is a code quality issue that adds unnecessary noise.

**Evidence:**
```
src\mkobi\services\processing_log_service.py:242: error: Redundant cast to "int"  [redundant-cast]
src\mkobi\services\processing_log_service.py:248: error: Redundant cast to "int"  [redundant-cast]
```

**Recommendation:** Remove the redundant `cast(int, ...)` calls at lines 242 and 248 since `result` from `await self.log_repo.delete_old_logs()` is already inferred as `int`.

---

### BE-002: Test seeder lacks idempotency - causes parallel test failures

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/seeders/test_media_dash.py, tests/test_dev_seeders.py |
| **Classification** | mandatory |

**Description:** The `ensure_test_media_dash()` seeder function is documented as idempotent but fails under parallel xdist test execution. When multiple workers run tests concurrently, they all attempt to create graphs with the same names ("Monthly TVR by Brand", "Monthly TVR by Advertiser") for the same dashboard, causing `UniqueViolationError` on the `idx_graphs_dashboard_name` constraint. This violates the spec requirement that tests should run in isolation.

**Evidence:**
```
sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint "idx_graphs_dashboard_name"
DETAIL:  Key (dashboard_id, name)=(6ae1751b-806c-4eae-9f6e-43085e622780, Monthly TVR by Brand) already exists.
```
Tests failing:
- test_ensure_test_media_dash_creates_dashboard
- test_ensure_test_media_dash_is_idempotent
- test_ensure_test_media_dash_creates_processing_config
- test_ensure_test_media_dash_creates_graphs_with_correct_config
- test_ensure_test_media_dash_creates_filters_binds_to_dashboard
- test_dashboard_config_contains_filters_definition
- test_development_seeders_runs_on_startup

**Recommendation:** Move graph creation inside the "if existing_dashboard" block to delete existing graphs before creating new ones, or use ON CONFLICT DO UPDATE/REPLACE pattern for graph inserts. The dashboard existence check at line 46-52 deletes graphs but the graph objects are created AFTER that block at lines 112-141, causing duplicate key violations.

---

### BE-003: cleanup_old_processing_logs uses separate session causing test isolation failure

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/file_cleanup.py |
| **Classification** | mandatory |

**Description:** The `cleanup_old_processing_logs` function in `file_cleanup.py` creates its own database session via `get_session()` at line 123, but tests use `async_db_session` fixture with SAVEPOINT pattern. The DELETE executed in a separate session doesn't see uncommitted changes from the test's session, causing the test to fail with 0 deleted records instead of the expected 2.

**Evidence:**
```
tests/test_file_cleanup.py:224: in test_cleanup_old_processing_logs_deletes_terminal_states
    assert deleted_count == 2, "Should have deleted 2 old logs (COMPLETED and FAILED)"
AssertionError: Should have deleted 2 old logs (COMPLETED and FAILED)
assert 0 == 2
```
The test creates logs in `async_db_session`, calls `cleanup_old_processing_logs(retention_days=30)` which uses a DIFFERENT session, so the DELETE doesn't see the uncommitted test data.

**Recommendation:** Modify `cleanup_old_processing_logs` to accept an optional `db` session parameter (similar to how `ProcessingLogService.delete_old_logs` does at line 220), or create a fixture that properly overrides the session at the module level.

---

### BE-004: Test file in wrong location - tests/api directory not discovered by pytest

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/api/test_temp_password_retrieval.py |
| **Classification** | mandatory |

**Description:** The test file `tests/api/test_temp_password_retrieval.py` exists but pytest with `-n auto` (xdist) reports "no tests ran". The `pyproject.toml` configures `testpaths = ["tests"]` and `python_files = ["test_*.py"]`, which should include subdirectories. However, the `tests/api/` directory contains only this one test file and the tests are completely bypassed during parallel test execution.

**Evidence:**
```
platform win32 -- Python 3.14.0 ...
created: 16/16 workers
16 workers [0 items]
scheduling tests via LoadScheduling
=========================== no tests ran in 47.08s ============================
```

**Recommendation:** The test file should either be moved to `tests/` root (matching the pattern of other test files) or the pytest configuration should be updated to explicitly include `tests/api`. Given project structure patterns, moving to `tests/` root is preferred.

---

### BE-005: no-any-return mypy errors in processing_log_service.py

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/processing_log_service.py |
| **Classification** | advisory |

**Evidence:**
```
src\mkobi\services\processing_log_service.py:78: error: Returning Any from function declared to return "list[Any]"  [no-any-return]
src\mkobi\services\processing_log_service.py:85: error: Returning Any from function declared to return "list[Any]"  [no-any-return]
src\mkobi\services\processing_log_service.py:217: error: Returning Any from function declared to return "list[Any]"  [no-any-return]
```

**Recommendation:** Add proper type annotations or tighten return types in `ProcessingLogRepository` methods to return explicit types instead of `Any`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |

---

## Mandatory Fixes

1. BE-002: Fix test seeder idempotency for parallel xdist test execution
2. BE-003: Fix `cleanup_old_processing_logs` to work with test session fixtures
3. BE-004: Move `tests/api/test_temp_password_retrieval.py` to discoverable location

---

## Advisory Recommendations

1. BE-001: Remove redundant `cast(int, count)` in processing_log_service.py
2. BE-005: Fix `no-any-return` mypy errors by tightening type annotations