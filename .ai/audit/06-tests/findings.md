# Phase 06 Audit Findings — Test Quality

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: Tautological Tests in test_dev_seeders.py

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `tests/test_dev_seeders.py` |
| **Classification** | mandatory |

**Description:** Two tests in `test_dev_seeders.py` only assert that `run_dev_seeders` is `callable()` — a tautological check that always passes for any Python function. These tests do not verify any behavior: they confirm the function is importable rather than that `DatabaseStarter` actually invokes it in development mode or avoids it in test mode.

`test_starter_calls_dev_seeders_in_development_mode` (line 223) patches `run_dev_seeders` but never calls `DatabaseStarter.startup()`, so the mock is never exercised. The only assertion is `assert callable(run_dev_seeders)` (line 262), which would pass for any function.

`test_starter_does_not_call_dev_seeders_in_test_mode` (line 274) only asserts the environment value and `assert callable(run_dev_seeders)` (line 286) — again tautological.

**Evidence:**
- `tests/test_dev_seeders.py:223-271`: `test_starter_calls_dev_seeders_in_development_mode` — patches `run_dev_seeders` but never triggers startup; final assertion is `assert callable(run_dev_seeders)`.
- `tests/test_dev_seeders.py:274-286`: `test_starter_does_not_call_dev_seeders_in_test_mode` — final assertion is `assert callable(run_dev_seeders)`.
- Both tests give a false sense of security for environment-dependent seeder behavior.

**Recommendation:** Replace these tests with actual behavioral assertions:
1. For dev mode: call `DatabaseStarter.startup()` and assert `mock_run_seeders.assert_called_once()`.
2. For test mode: call `DatabaseStarter.startup()` and assert `mock_run_seeders.assert_not_called()`.
If full startup is too expensive, extract the seeder-invocation decision into a testable function and unit-test that.

---

### TST-002: Overall Test Coverage Below Configured Threshold (72% vs 80%)

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/` (entire codebase) |
| **Classification** | mandatory |

**Description:** The project configures `fail_under = 80` in `[tool.coverage.report]` (`pyproject.toml:212`), indicating 80% coverage is the required minimum. Actual coverage is 72.20%, failing the threshold by 7.8 percentage points. This means ~28% of production statements (1,978 of 7,114) are untested, including critical security and business logic paths.

**Evidence:**
- `pyproject.toml:212`: `fail_under = 80`
- Coverage run output: `TOTAL 7114 1978 72%` — `FAIL Required test coverage of 80.0% not reached. Total coverage: 72.20%`
- 1,978 uncovered statements across 60+ source modules.

**Recommendation:** Prioritize adding tests for the lowest-coverage critical modules first (see TST-003, TST-004, TST-005). Then progressively increase coverage to meet the 80% threshold. Consider adding `pytest-cov` to CI to fail the pipeline on coverage regression.

---

### TST-003: Critical API Routes With Under 35% Coverage

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/dashboards_filters.py`, `src/mkobi/api/routes/dashboards_access.py`, `src/mkobi/api/routes/processing_configs.py`, `src/mkobi/api/routes/users.py` |
| **Classification** | mandatory |

**Description:** Several API route modules — handling access control, filter binding, processing configuration, and user management — have critically low test coverage. These routes enforce authorization boundaries and handle mutating operations; lack of tests means bugs in access control or data validation could go undetected.

**Evidence:**
- `src/mkobi/api/routes/dashboards_filters.py`: 26% coverage (50 of 68 stmts uncovered, lines 49-102, 123-175, 195-208)
- `src/mkobi/api/routes/dashboards_access.py`: 32% coverage (38 of 56 stmts uncovered, lines 65-124, 155-168, 200-224)
- `src/mkobi/api/routes/processing_configs.py`: 39% coverage (27 of 44 stmts uncovered, lines 41-53, 72-91, 108-117)
- `src/mkobi/api/routes/users.py`: 34% coverage (63 of 96 stmts uncovered, lines 59-74, 105-112, 150-178, 216-240, 277-291, 329-331, 342-346)

**Recommendation:** Add integration tests for each route module:
1. `dashboards_filters.py`: Test bind/unbind filter to dashboard (admin-only, authorization errors).
2. `dashboards_access.py`: Test grant/revoke access, list access records.
3. `processing_configs.py`: Test CRUD on processing configurations per dashboard.
4. `users.py`: Test user CRUD, role assignment, activation/deactivation.

---

### TST-004: Critical Service Layer With Under 55% Coverage

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/user_service.py`, `src/mkobi/services/filter_service.py`, `src/mkobi/services/dashboard_service.py` |
| **Classification** | mandatory |

**Description:** Key business logic services have low coverage. `user_service.py` handles user creation, password changes, activation, and deletion at 51%. `filter_service.py` handles filter CRUD and value resolution at 56%. `dashboard_service.py` handles dashboard management at 60%. These services contain authorization checks and data mutations — gaps mean correctness bugs pass undetected.

**Evidence:**
- `src/mkobi/services/user_service.py`: 51% coverage (49 of 99 stmts uncovered, lines 37-46, 67, 126-132, 144-150, 173-204, 226-246, 269, 284-285, 310, 327, 343-347)
- `src/mkobi/services/filter_service.py`: 56% coverage (59 of 135 stmts uncovered)
- `src/mkobi/services/dashboard_service.py`: 60% coverage (63 of 157 stmts uncovered)

**Recommendation:** Add unit tests for each service using the existing `mock_db` and `mock_*_repo` patterns. Focus on edge cases: password change validation, user activation/deactivation, filter value resolution with missing data, dashboard ownership checks.

---

### TST-005: Worker and Utility Modules With Critical Gaps

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/utils/validators.py`, `src/mkobi/utils/time_utils.py`, `src/mkobi/utils/file_utils.py`, `src/mkobi/core/task_queue.py` |
| **Classification** | advisory |

**Description:** The background data worker (48%), validators (26%), time utilities (39%), file utilities (31%), and task queue (45%) have low coverage. While some of these run in background processes, the data worker orchestrates the entire upload→parse→transform→aggregate pipeline and should be tested for error paths. Validators guard input integrity.

**Evidence:**
- `src/mkobi/workers/data_worker.py`: 48% (103 of 200 stmts uncovered, lines 83-85, 89-95, 133-148, 198-204, 215-222, 226-243, 247-249, 253-255, 261-281, 321-345, 389, 407-408, 447-518, 591, 615-625)
- `src/mkobi/utils/validators.py`: 26% (57 of 77 stmts uncovered)
- `src/mkobi/utils/time_utils.py`: 39% (19 of 31 stmts uncovered)
- `src/mkobi/utils/file_utils.py`: 31% (24 of 35 stmts uncovered)
- `src/mkobi/core/task_queue.py`: 45% (36 of 66 stmts uncovered)

**Recommendation:** Prioritize `data_worker.py` error path tests (processing failure, malformed data, missing dashboard). Add unit tests for `validators.py` input validation rules. Test `time_utils.py` date handling edge cases. Test `task_queue.py` task lifecycle.

---

### TST-006: Mypy Excludes Tests — No Type Safety Verification in Test Code

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/`, `pyproject.toml` |
| **Classification** | advisory |

**Description:** The mypy configuration in `pyproject.toml:169` explicitly excludes `tests/` from type checking (`exclude = ["tests/", "alembic/"]`). This means test code receives no type-safety verification, which can lead to incorrect mock signatures, wrong assertion types, and stale type references that pass CI silently but fail at runtime.

**Evidence:**
- `pyproject.toml:169`: `exclude = ["tests/", "alembic/"]`
- No mypy coverage for 37 test files containing 740 tests.

**Recommendation:** Remove `tests/` from the mypy exclude list. Run `uv run mypy tests/` and fix any reported errors. If the volume of errors is large, start by adding `--strict` to only new tests and gradually fix existing ones.

---

### TST-007: Test Suite Execution Time Exceeds 5 Minutes

| Field | Value |
|-------|-------|
| **ID** | TST-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/` |
| **Classification** | advisory |

**Description:** The full test suite takes ~325–390 seconds (5.4–6.5 minutes) to execute. This slows the feedback loop for developers and discourages frequent test runs. The primary bottleneck is likely the setup_test_database fixture which recreates the test database on each session, and many integration tests that perform real database I/O.

**Evidence:**
- First run: `740 passed in 390.72s (0:06:30)`
- Second run: `740 passed in 324.47s (0:05:24)`

**Recommendation:** Profile test execution to identify the slowest tests (`pytest --durations=20`). Consider:
1. Marking slow integration tests with `@pytest.mark.slow` and running them separately in CI.
2. Using `@pytest.mark.fast` with in-memory SQLite for unit-only tests where DB is not needed.
3. Caching the test database schema between runs instead of recreating from scratch each session.

---

### TST-008: Auth Service Tests Rely Heavily on Mock Assertions

| Field | Value |
|-------|-------|
| **ID** | TST-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_auth_service.py` |
| **Classification** | advisory |

**Description:** The `test_auth_service.py` unit tests (41 tests) use `AsyncMock` for the repository and database, then assert that specific mock methods were called (`mock_user_repo.create.assert_called_once()`, `mock_db.commit.assert_called_once()`). While acceptable for pure unit tests, this pattern verifies implementation details (which methods are called) rather than observable behavior (the result of the operation). Refactoring the service internals would break these tests even if behavior is preserved.

**Evidence:**
- `tests/test_auth_service.py:60`: `mock_user_repo.create.assert_called_once()`
- `tests/test_auth_service.py:446-447`: `mock_user_repo.update.assert_called_once()` / `mock_db.commit.assert_called_once()`
- `tests/test_auth_service.py:542-543`: `mock_user_repo.update.assert_not_called()` / `mock_db.commit.assert_not_called()`

**Recommendation:** Where possible, prefer state-based assertions (verify the returned data is correct) over interaction-based assertions. For example, after `register_user`, verify the returned `UserRead` fields rather than just asserting `create` was called. Keep mock assertions only for verifying that side effects (like DB commits) are properly conditional.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 4 |
| LOW | 1 |

## Mandatory Fixes

- **TST-001**: Tautological tests in `test_dev_seeders.py` — `assert callable()` gives false security
- **TST-002**: Overall coverage 72% vs required 80% threshold
- **TST-003**: Critical API routes (dashboards_filters, dashboards_access, processing_configs, users) under 35% coverage
- **TST-004**: Critical services (user_service, filter_service, dashboard_service) under 60% coverage

## Advisory Recommendations

- **TST-005**: Worker and utility modules with critical coverage gaps
- **TST-006**: Mypy excludes tests — no type safety verification in test code
- **TST-007**: Test suite execution time exceeds 5 minutes
- **TST-008**: Auth service tests rely heavily on mock interaction assertions

## Doc Updates Needed

None
