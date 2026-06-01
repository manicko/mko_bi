# Phase 06 Audit Findings — Test Quality

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: 233 of 603 Backend Tests Fail Due to Database Port Not Exposed on Host

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `tests/` (all integration/API/repository tests), `tests/conftest.py` |
| **Classification** | mandatory |

**Description:** Running `uv run pytest tests/` from the Windows host results in **233 ERRORs** out of 603 tests (370 pass, 233 errors). Every error is `ConnectionRefusedError: [WinError 1225]` because all DB-dependent tests require a PostgreSQL connection on `localhost:5432`, but the Docker Compose `db` service does not expose port 5432 to the host machine.

The base `docker/docker-compose.yml` does not declare `ports` on the `db` service. The override file `docker/docker-compose.override.yml` does declare `"5432:5432"`, but the override is **not active** — `docker inspect docker-db-1` confirms the container's port bindings are `{"5432/tcp": null}` (unpublished). The container metadata also shows `config_files` only references `docker-compose.yml`, confirming the merge is absent.

**Evidence:**
- Runtime: `370 passed, 233 errors in 314.81s` from `uv run pytest tests/ -v --tb=short`
- Error: `ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection` across all 233 failures, traceable to `conftest.py:306` → `DatabaseStarter.recreate_test_database()` → `admin_engine.connect()`
- `docker inspect docker-db-1 --format '{{json .NetworkSettings.Ports}}'` returns `{"5432/tcp": null}`
- `docker port docker-db-1 5432` returns no output
- The `conftest.py` sets `DATABASE__HOST=localhost`, `DATABASE__PORT=5432` (lines 17-18)
- Base compose file `docker/docker-compose.yml` service `db` has no `ports:` section
- `docker/db` directory: `docker-compose.override.yml` line 91 has `"5432:5432"` but this file is not used when running `docker compose -f docker/docker-compose.yml up -d`
- `bidb_test` database does not exist inside container (only `bidb` exists), and since port isn't exposed, it can't be created from host

**Affected test files (all 233 errors):** `test_auth.py`, `test_auth_api.py`, `test_dashboards_api.py`, `test_data_endpoint.py`, `test_data_service.py`, `test_deps.py`, `test_filters.py`, `test_graphs.py`, `test_layouts.py`, `test_permissions.py`, `test_processing_logs.py`, `test_repositories.py`, `test_services_integration.py`, `test_storage_manager.py`, `test_upload_api.py`, `test_users_api.py`

**Recommendation:** Either (a) expose port 5432 on the `db` service in the base `docker-compose.yml`, or (b) always start services with the override: `docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d`, and document this requirement clearly in the commands doc. Alternatively, add a host-native PostgreSQL configuration for test runs or use `testcontainers` (already in dev dependencies).

---

### TST-002: Stale `.pyc` Cache Files from Deleted Test Modules

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/__pycache__/` |
| **Classification** | advisory |

**Description:** The `tests/__pycache__/` directory contains compiled `.pyc` files for test modules that no longer have corresponding `.py` source files. These stale cache artifacts can cause confusion when inspecting test coverage or investigating test failures.

**Evidence:**
- `test_yoy_calculation.cpython-314-pytest-9.0.3.pyc` exists in `__pycache__/` but no `test_yoy_calculation.py` exists in `tests/`
- `test_share_calculation.cpython-314-pytest-9.0.3.pyc` exists in `__pycache__/` but no `test_share_calculation.py` exists in `tests/`
- `test_data_processing.cpython-314-pytest-9.0.3.pyc` exists in `__pycache__/` but no `test_data_processing.py` exists in `tests/`
- `test_models.cpython-314-pytest-9.0.3.pyc` exists in `__pycache__/` but no `test_models.py` exists in `tests/`

**Recommendation:** Add `__pycache__/` to `.gitignore` and run `Remove-Item -Recurse -Force tests/__pycache__` to clean up. Consider adding `find . -type d -name __pycache__ -exec rm -rf {} +` as part of the test setup or Makefile clean target.

---

### TST-003: Backup Test File `test_upload_api.py.bak` Committed to Repository

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_upload_api.py.bak` |
| **Classification** | advisory |

**Description:** A backup copy of `test_upload_api.py` named `test_upload_api.py.bak` exists in the `tests/` directory. It contains 757 lines of upload tests with fixtures and realistic CSV content, but is not maintained alongside the main file. Backup files committed to the repository create confusion about which version is canonical and may accidentally be executed by test runners depending on glob configuration.

**Evidence:**
- `tests/test_upload_api.py.bak` exists (757 bytes), `tests/test_upload_api.py` also exists (different file)
- The `.bak` file contains different test implementations (e.g., `TestTempFileCleanup` class with `monkeypatch` and `mocker` fixtures) not present in the current `test_upload_api.py`
- `pyproject.toml` testpaths uses `test_*.py` pattern, which would match this file

**Recommendation:** Remove `tests/test_upload_api.py.bak` from the repository. Add `*.bak` to `.gitignore` to prevent future occurrences.

---

### TST-004: Frontend Test Coverage Is Extremely Limited — 82 Tests Across 6 Files

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/` (features/admin, features/users, shared/components, shared/hooks, shared/utils, features/upload/ui/UploadModal) |
| **Classification** | mandatory |

**Description:** The frontend test suite consists of only **82 tests across 6 test files**, all passing. While the individual tests are well-structured, coverage is critically sparse for a production BI dashboard application. The following critical frontend components have **zero test coverage**:

- **Admin features** (6 components: `AdminPanel`, `DashboardManagement`, `LogViewer`, `RegistrationRequests`, `ResetPasswordResultDialog`, `UserManagement`) — no tests
- **Auth UI** (`RegisterForm` exists but has no unit tests, only integration-level form validation tests)
- **Dashboard features** (`DashboardList`, `DashboardFilters`) — no tests; only `DashboardView` has tests with fully mocked API responses
- **Charts** (`BarChart`, `LineChart`, `PieChart`, `PlotlyChart`, `TableChart`) — no tests
- **ProtectedRoute / access control** (`ProtectedRoute`, `RoleBasedAccess`, `AccessDenied`, `ErrorBoundary`) — no tests
- **User features** (`ChangePasswordPage`, `UserProfile`) — no tests
- **Shared API layer** (`axiosInstance`, `refreshHandler`) — no tests
- **Shared components** (`ConfirmDialog`, `ErrorPage`, `AppLayout`, `Header`, `NotFound`, `PlaceholderPage`) — no tests
- **Shared hooks** (`useConfirmDialog`) — no tests
- **Shared utils** (`shortUuid`) — no tests

**Evidence:**
- `npm run test -- --reporter=verbose` returns: `6 test Files, 82 tests passed`
- Only test files: `enums.test.ts`, `formSchemas.test.ts`, `authToken.test.ts`, `authFlow.test.tsx`, `DashboardView.test.tsx`, `FileDropzone.test.tsx`
- 10+ feature modules have no `__tests__` directory or test files
- The vitest config in `vite.config.ts` defines coverage thresholds (statements: 50%, branches: 40%, functions: 45%, lines: 50%) but these cannot be evaluated because coverage is not being run — the vitest config coverage thresholds pass even with the above gaps since the low threshold is met by the few existing tests

**Recommendation:** Prioritize tests for: (1) `ProtectedRoute` and `RoleBasedAccess` (security-critical), (2) `refreshHandler` and `axiosInstance` (auth token lifecycle), (3) `ConfirmDialog` (shared destructive action pattern), (4) at least one test per chart component. Consider enabling coverage enforcement in CI.

---

### TST-005: `baseline_data` Fixture Is a No-Op Placeholder

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/conftest.py` |
| **Classification** | advisory |

**Description:** The `baseline_data` fixture in `conftest.py` (lines 373-380) is a session-scoped async fixture that does nothing — it just `yield`s without loading any test data. This creates a false impression that baseline/reference data is loaded for integration tests. Tests that rely on finding specific reference data (e.g., users with specific roles, dashboards with specific configs) will fail silently or produce misleading results.

**Evidence:**
```python
# tests/conftest.py:373-380
@pytest.fixture(scope="session")
async def baseline_data(setup_test_database):
    """Load minimal reference data once per test session.

    This fixture is a placeholder for future reference data loading.
    Currently ensures the test database is properly initialized.
    """
    yield
```
- The docstring explicitly states "This fixture is a placeholder for future reference data loading"
- No test in the suite uses this fixture (verified by grep — no test function has `baseline_data` as a parameter)

**Recommendation:** Either implement the fixture with actual reference data loading, or remove it and the associated docstring to avoid confusion. If it's intended for future use, add a `# TODO` comment with a tracking issue reference.

---

### TST-006: Test Database Not Isolated — Shared Docker DB Instance

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `tests/conftest.py`, `docker/docker-compose.yml` |
| **Classification** | mandatory |

**Description:** The test suite configuration uses a shared Docker database instance. The conftest targets `bidb_test` database on `localhost:5432`, which is the same PostgreSQL instance as the development database (`bidb`). This creates test isolation risks: tests that accidentally write to the wrong database, or the `RECREATE_TEST_DB=true` setting dropping/creating databases on a shared instance, could corrupt development data or cause non-deterministic behavior when dev and test runs overlap.

While the schema uses SAVEPOINT-based rollback (`conftest.py:341-370`) which provides transaction-level isolation, the database-level isolation is missing. The `docker-compose.test.yml` provides a fully isolated test environment (separate `test-db` on port 5433), but the conftest's default configuration (`DATABASE__PORT=5432`, `DATABASE__HOST=localhost`) targets the dev instance.

**Evidence:**
- `conftest.py` line 18: `os.environ.setdefault("DATABASE__PORT", "5432")` — this maps to the dev DB
- `conftest.py` line 19: `os.environ.setdefault("DATABASE__DBNAME", "bidb_test")`
- `docker/docker-compose.test.yml` defines `test-db` service on port `5433` with separate volumes
- The conftest uses `os.environ.setdefault()` so Docker Compose env vars would take precedence, but only when running *inside* Docker Compose
- The `test_user` fixture (line 431) calls `await async_db_session.commit()` which commits to the shared DB, not a test-isolated instance

**Recommendation:** When running natively on the host, use the test database container (`test-db` on port 5433) or a separate local PostgreSQL instance. Update the conftest or README to clearly document running `docker compose -f docker/docker-compose.test.yml up -d` before running tests natively. Alternatively, configure the conftest to detect whether it's inside a Docker container and adjust the connection parameters accordingly.

---

### TST-007: Auto-Mock Fixture Disables Rate Limiting in All Tests by Default

| Field | Value |
|-------|-------|
| **ID** | TST-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/conftest.py` |
| **Classification** | advisory |

**Description:** The `_auto_mock_redis` fixture (`conftest.py:182-221`) is `autouse=True`, meaning it patches Redis and disables rate limiting in **every** test, including tests that are specifically designed to test rate limiting behavior. While the `TestRateLimiting` tests in `test_auth.py` pass (5/5), they use the `strict_redis` fixture explicitly. Any future test that inadvertently relies on rate-limiting behavior being active will silently pass with the mock providing no actual rate limiting.

The fixture captures `AuthService.__init__` in a global variable (`_original_auth_init`, line 170) which is a fragile pattern — if the import order changes or the module is reloaded, the captured reference could become stale.

**Evidence:**
```python
# conftest.py:182-221
@pytest.fixture(autouse=True)
def _auto_mock_redis(monkeypatch):
    """Auto-mock Redis client for all tests to avoid requiring a real Redis server."""
    # ...patches get_async_redis_client and get_redis_client...
    # Patch auth service rate limiter to always allow (backward compatibility)
    monkeypatch.setattr(auth_service_module.AuthService, "__init__", patched_init)
```
- Global variable pattern: `_original_auth_init = None` at line 170
- The `strict_redis` fixture (line 257) exists to opt-out of this behavior but is only used by `TestRateLimiting`

**Recommendation:** Document the auto-mock behavior prominently at the top of conftest.py. Consider making the rate-limiting opt-out (`strict_redis`) more discoverable with better naming or documentation. Initialize `_original_auth_init` eagerly at module level rather than lazily to avoid import-order coupling.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

- **TST-001**: Expose PostgreSQL port 5432 to host or document the override requirement. Without this fix, 233/603 backend tests cannot run from the Windows host environment.
- **TST-004**: Add frontend tests for security-critical components (ProtectedRoute, RoleBasedAccess, refreshHandler).
- **TST-006**: Ensure test database isolation, either by using the test compose stack or a separate connection configuration.

## Advisory Recommendations

- **TST-002**: Clean up stale `.pyc` cache files from deleted test modules.
- **TST-003**: Remove `test_upload_api.py.bak` from the repository and add `*.bak` to `.gitignore`.
- **TST-005**: Implement or remove the no-op `baseline_data` fixture.
- **TST-007**: Improve documentation around auto-mocking behavior in conftest.py.

## Doc Updates Needed

None.
