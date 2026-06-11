---
name: audit-findings
description: Test quality audit findings for mkobi BI Dashboard
agent: auditor
alwaysApply: false
---

# Phase 06 Audit Findings — Test Quality

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: Tests calling external subprocess commands fail in container environment

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/test_dev_seeders.py |
| **Classification** | mandatory |

**Description:** Tests `test_seed_script_ruff_mypy` and `test_dev_seeders_module_ruff_mypy` invoke `uv run ruff check` and `uv run mypy` via `subprocess.run()` and fail with `PermissionError: [Errno 13] Permission denied: 'uv'`. This is because the test container runs as a non-root user that cannot execute the `uv` binary installed at the system level.

**Evidence:**
```
tests/test_dev_seeders.py:188: result = subprocess.run(
    ["uv", "run", "ruff", "check", "src/mkobi/db/seeders/test_media_dash.py"],
    ...
)
PermissionError: [Errno 13] Permission denied: 'uv'
```

The tests run directly via `/app/.venv/bin/pytest` in the container, but the `uv` command is not accessible in the PATH or requires different permissions.

**Recommendation:** Modify the linting tests to run ruff/mypy directly without `uv run`, or skip these tests in the container environment. Change from:
```python
result = subprocess.run(["uv", "run", "ruff", "check", ...])
```
to:
```python
result = subprocess.run(["/app/.venv/bin/ruff", "check", ...])
```
or use `pytest.mark.skipif` to detect container environment.

---

### TST-002: pytest-xdist parallel execution causes worker crashes

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | pyproject.toml, tests/conftest.py |
| **Classification** | advisory |

**Description:** The test suite is configured with `-n auto` (pytest-xdist parallel execution) which creates 16 workers by default. Running tests in parallel with the current configuration causes "node down: Not properly terminated" errors for multiple tests (identified: `test_get_graph_cross_dashboard_forbidden`, `test_e2e_processing_log_status_transitions`, `test_get_by_id`, `test_read_access_with_permission`). This indicates potential shared state or resource contention issues.

**Evidence:**
```
[gw8] node down: Not properly terminated
[gw8] FAILED tests/test_graphs.py::TestGraphsAPI::test_get_graph_cross_dashboard_forbidden
...
replacing crashed worker gw8
```

The `pyproject.toml` line 196 shows: `addopts = "--import-mode=importlib -ra -v --strict-markers --cov-fail-under=65 -n auto"`

**Recommendation:** Either (1) remove `-n auto` from addopts and run tests sequentially, or (2) investigate and fix the underlying shared state issues. Sequential tests are more reliable; parallel only helps with large test suites where isolation is proven.

---

### TST-003: No coverage collection for frontend TypeScript tests

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | vite.config.ts |
| **Classification** | advisory |

**Description:** The `vite.config.ts` defines coverage thresholds (statements: 50, branches: 40, functions: 45, lines: 50) but vitest is run with `vitest run` without coverage collection. The coverage configuration exists but is not enforced during test runs.

**Evidence:** `vite.config.ts` lines 52-64 define coverage configuration, but `npm run test` runs `vitest run` without the `--coverage` flag.

**Recommendation:** Update `package.json` test script to include coverage: `"test": "vitest run --coverage"`. This ensures coverage thresholds are enforced and provides visibility into untested frontend code.

---

### TST-004: Incomplete cleanup in test_e2e_upload.py for multi-file test

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | LOW |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/test_e2e_upload.py |
| **Classification** | advisory |

**Description:** In `test_e2e_multiple_graphs_same_dashboard`, the `multi_file` temporary file cleanup at line 343 (`multi_file.unlink(missing_ok=True)`) is placed after all assertions but could be missed if earlier assertions fail, potentially leaving temp files.

**Evidence:** `tests/test_e2e_upload.py:306-343` - the temp file cleanup is outside the try/finally pattern used in other tests in this file.

**Recommendation:** Wrap the temporary file creation and deletion in a try/finally block to ensure cleanup even on test failure.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 1 |

## Mandatory Fixes

- TST-001: Tests calling external subprocess commands fail in container environment (tests cannot run in CI/test container)

## Advisory Recommendations

- TST-002: pytest-xdist parallel execution causes worker crashes (test reliability)
- TST-003: No coverage collection for frontend TypeScript tests (observability)
- TST-004: Incomplete cleanup in test_e2e_upload.py for multi-file test (resource leak)

---

## Notes on Positive Patterns

The test suite demonstrates strong patterns in several areas:

1. **Database isolation** (`tests/conftest.py`): Uses SavePoint pattern with `session.begin_nested()` for proper rollback, combined with `NullPool` to prevent connection pooling issues. Worker isolation via `PYTEST_XDIST_WORKER` database suffix is well-implemented.

2. **Mock Redis for rate limiting** (`tests/conftest.py`): `MockRedis` class provides proper async interface for testing without requiring real Redis, and `strict_redis` fixture enables testing real rate limiting behavior.

3. **Dependency override pattern** (`tests/conftest.py`): `async_client` fixture properly overrides `get_db_dependency` and other dependencies for integration testing.

4. **Frontend test structure**: Tests use Testing Library best practices with proper setup file importing `@testing-library/jest-dom`.

5. **Test data cleanup**: Most tests use `try/finally` with `Path.unlink(missing_ok=True)` for temp file cleanup.

6. **Critical path coverage**: Tests exist for authentication flows, authorization boundaries, file upload processing, data transformations, and error handling formats.