# Phase 06 Audit Findings — Test Quality

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: PostgreSQL Version Incompatibility Causing Test Database Recreation Failures

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/conftest.py:398, src/mkobi/db/starter.py:235 |
| **Classification** | mandatory |

**Description:** Test database recreation fails with `PostgresSyntaxError: syntax error at or near "COLLATION_VERSION"` when running with PostgreSQL 18+ in test environment. The error occurs during `ALTER DATABASE template1 REFRESH COLLATION_VERSION` which is automatically executed by SQLAlchemy 2.x when connecting to PostgreSQL 18+. This command is incompatible with the test database setup workflow.

**Evidence:** 
- File: tests/conftest.py, line 398 - `setup_test_database` fixture calls `DatabaseStarter(starter_config).recreate_test_database()`
- File: src/mkobi/db/starter.py, line 235 - Database recreation logic
- Error traceback shows: `asyncpg.exceptions.PostgresSyntaxError: syntax error at or near "COLLATION_VERSION"` during asyncpg connection initialization
- PostgreSQL 18+ uses builtin locale provider with immutable collation versions, but the SQLAlchemy asyncpg driver still attempts to execute `REFRESH COLLATION_VERSION` on the template1 database which may not have the required permissions

**Recommendation:** Modify the database engine configuration to skip collation version checks for the test environment, or downgrade to PostgreSQL 17 for test containers. Alternatively, add `connect_args={"check_collation_version": False}` to the async engine creation in `conftest.py` for test database connections.

### TST-002: Subprocess Tests Fail Due to Missing uv Command in Docker Container

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/test_dev_seeders.py:183-201, tests/test_dev_seeders.py:204-220 |
| **Classification** | mandatory |

**Description:** Tests `test_seed_script_ruff_mypy` and `test_dev_seeders_module_ruff_mypy` fail with `PermissionError: [Errno 13] Permission denied: 'uv'` because they attempt to run `uv run ruff check` and `uv run mypy` as subprocess commands, but the `uv` executable is not in the container's PATH or lacks execute permissions.

**Evidence:**
- File: tests/test_dev_seeders.py, lines 183-201 and 204-220
- Error: `PermissionError: [Errno 13] Permission denied: 'uv'` when calling `subprocess.run(["uv", "run", "ruff", ...])`
- The test-app container uses a pre-built environment but doesn't include `uv` in the container's PATH at runtime

**Recommendation:** Either remove these subprocess-based linting tests (since CI/CD should handle this) or modify them to run actual linting commands within the container environment. The tests should use `sys.executable` with the installed packages rather than relying on the `uv` wrapper.

### TST-003: Test Worker Crashes Due to Parallel Execution Instability

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | Multiple test files (any using async_db_session fixture) |
| **Classification** | mandatory |

**Description:** Pytest-xdist parallel test execution causes worker processes to crash with `node down: Not properly terminated` errors, resulting in ERROR status instead of PASSED/FAILED. This indicates test isolation issues where one test's failure brings down the entire worker, affecting dependent tests.

**Evidence:**
- Runtime output shows repeated patterns: `node down: Not properly terminated` and `replacing crashed worker gwX`
- Tests like `test_get_aggregated_data_with_filters`, `test_ensure_test_media_dash_creates_dashboard`, `test_refresh_valid_token` show as ERROR or FAILED due to worker crashes
- The issue stems from shared database state or resource contention between parallel workers

**Recommendation:** Review fixture scoping and ensure proper cleanup. The `async_test_engine` fixture has `session` scope which should be safe, but the worker crashes suggest database-level contention. Consider adding connection retry logic or disabling parallel execution for tests that require database isolation.

### TST-004: Missing Coverage Configuration for pytest-cov in CI Environment

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | pyproject.toml:196, tests/ |
| **Classification** | advisory |

**Description:** While `pytest-cov` is configured with `fail_under=65`, the coverage tool may not be properly integrated with the parallel xdist execution, potentially masking coverage gaps. The `-n auto` flag for xdist can interfere with coverage collection.

**Evidence:**
- pyproject.toml line 196: `addopts = "--import-mode=importlib -ra -v --strict-markers --cov-fail-under=65 -n auto"`
- The combination of `-n auto` with coverage requires `pytest-cov` xdist plugin for proper operation
- Runtime output shows coverage warnings about permission issues with pytest cache

**Recommendation:** Either install `pytest-cov[xdist]` for parallel coverage support or disable parallel execution when coverage is required. Consider adding `--cov` flag explicitly to ensure coverage is measured.

### TST-005: Shared Mock Redis State Between Tests Without Proper Reset

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py:260-300, tests/api/test_temp_password_retrieval.py |
| **Classification** | advisory |

**Description:** The `MockRedis` class used in tests has a `clear()` method but it's only called in specific tests (e.g., rate limiter tests). Tests that store data in mock Redis (like temp password retrieval tests) don't consistently reset state between tests, potentially causing false positives or negatives.

**Evidence:**
- File: tests/conftest.py, line 188 - `clear()` method exists but isn't called in the autouse `_auto_mock_redis` fixture
- File: tests/api/test_temp_password_retrieval.py - Tests store temp passwords in `app.state.mock_redis` without ensuring isolation
- Multiple tests access `app.state.mock_redis` for setting up test data

**Recommendation:** Add explicit `clear()` calls in fixture teardown or ensure each test starts with a clean mock Redis state. Consider using the `strict_redis` fixture which already clears state before tests.

### TST-006: Dashboard Config Test Relies on External Service State

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_dev_seeders.py:289-313 |
| **Classification** | advisory |

**Description:** The test `test_dashboard_config_contains_filters_definition` asserts specific config structure on the `test_media_dash` dashboard but doesn't account for state changes from previous tests. When run in parallel or after other tests, the dashboard config may have been modified.

**Evidence:**
- File: tests/test_dev_seeders.py:289-313 - Test calls `ensure_test_media_dash()` which modifies the dashboard
- Lines 300-308 assert `"filters" in dashboard.config` and `"graph_types" in dashboard.config`
- The test is marked as FAILED in the parallel run, suggesting state inconsistency

**Recommendation:** Tests should create fresh test data with unique identifiers rather than relying on seeded dashboard state that may be shared across test runs.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 0 |

## Mandatory Fixes

- TST-001: PostgreSQL version incompatibility preventing test database setup
- TST-002: Subprocess tests failing due to missing uv command in container

## Advisory Recommendations

- TST-003: Improve test isolation for parallel xdist execution
- TST-004: Review coverage configuration with parallel test execution
- TST-005: Ensure mock Redis state isolation between tests
- TST-006: Improve dashboard config test data isolation

## Doc Updates Needed

(None - no DOC-UPDATE findings in this phase)

---