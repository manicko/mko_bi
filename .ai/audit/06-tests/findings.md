---
name: 06-tests
description: Test Quality Audit Findings
status: complete
validated: no
---

# Phase 06 Audit Findings — Test Quality

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: Heavy mocking patches obscure actual business logic testing

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_data_service.py, tests/test_upload_api.py |
| **Classification** | advisory |

**Description:** Tests extensively mock internal dependencies (`check_dashboard_access`, `enqueue_job`, `find_task_file`, `enqueue_processing_job`) rather than testing actual business logic. This pattern in test_data_service.py (lines 89-90, 129, 160, 191-192, 319-321, 347, 425-433) and test_upload_api.py (line 215, 222) creates tests that verify mock calls rather than system behavior. When critical internal functions are patched, the test may pass despite the real implementation being broken.

**Evidence:**
```python
# tests/test_data_service.py:89-90
with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
    with patch("mkobi.services.file_processing.enqueue_job"):
```
The `check_dashboard_access` function is mocked to always return True, making the permission check test entirely synthetic.

**Recommendation:** Reduce mocking of internal functions. Test at API layer with real database state verification (as test_upload_api.py does well) rather than patching business logic to bypass it. Integration tests should verify actual end-to-end behavior.

---

### TST-002: Global graph endpoints lack dashboard access verification in tests

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_graphs.py |
| **Classification** | mandatory |

**Description:** The global `/graphs/{graph_id}` endpoints (GET, PUT, DELETE) in test_graphs.py do not verify that the user has access to the dashboard that owns the graph. Tests at lines 258-291 (test_get_graph_by_id) and 300-346 (test_update_graph_admin_required) test permission enforcement for `view`/`edit`/`admin` roles but never test the case where a user tries to access a graph belonging to a dashboard they don't have access to. This is a security coverage gap - the production code may incorrectly allow cross-dashboard access.

**Evidence:**
```python
# tests/test_graphs.py:258-291
async def test_get_graph_by_id(
    self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
) -> None:
    """Test getting graph by ID."""
    # No dashboard access check - just fetches any graph
    response = await authenticated_client.get(f"/graphs/{graph.id}")
    assert response.status_code == status.HTTP_200_OK
```

**Recommendation:** Add tests that create a graph on one dashboard and attempt to access it from a user who only has access to a different dashboard. Expect 403 Forbidden to verify dashboard-level access control on global graph endpoints.

---

### TST-003: Frontend has critically low test coverage (3 test files for entire React app)

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/features/, frontend/src/shared/ |
| **Classification** | mandatory |

**Description:** Frontend test coverage is critically low - only 3 test files exist for the entire React application codebase. The test files are:
- `frontend/src/features/auth/model/__tests__/authToken.test.ts` - token storage utilities only
- `frontend/src/shared/types/__tests__/formSchemas.test.ts` - form validation schemas only  
- `frontend/src/shared/types/__tests__/enums.test.ts` - enum value tests only

Critical features with zero test coverage include:
- Dashboard rendering and data fetching (DashboardView, DashboardList)
- Upload components (FileDropzone, UploadModal)
- Chart components (BarChart, LineChart, PieChart, PlotlyChart, TableChart)
- Authentication hooks (useAuth)
- Admin panels (LogViewer, RegistrationRequests, UserManagement)
- User profile and password change flows

**Evidence:**
```
$ glob pattern "**/*.test.{ts,tsx}" in frontend/src
C:\py_dev\mkobi\frontend\src\features\auth\model\__tests__\authToken.test.ts
C:\py_dev\mkobi\frontend\src\shared\types\__tests__\formSchemas.test.ts
C:\py_dev\mkobi\frontend\src\shared\types\__tests__\enums.test.ts
```

**Recommendation:** Add frontend tests for critical user flows:
- Dashboard data loading and rendering
- Authentication flow (login, token refresh, logout)
- File upload and processing status
- Chart rendering with sample data
- Access control on dashboard/graph operations

---

### TST-004: No coverage threshold enforcement in CI config

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | pyproject.toml, frontend/package.json |
| **Classification** | advisory |

**Description:** While pytest-cov is configured in pyproject.toml (lines 221-227) with `fail_under = 80`, the frontend has no coverage configuration at all in package.json. The vite.config.ts configures vitest but without any coverage thresholds. This allows test coverage to degrade without detection in CI pipelines.

**Evidence:**
```toml
# pyproject.toml:221-227
[tool.coverage.run]
source = ["src/mkobi"]

[tool.coverage.report]
fail_under = 80
```
No equivalent coverage configuration exists for frontend vitest.

**Recommendation:** Add coverage threshold to vitest config in vite.config.ts. Consider requiring coverage reports in CI to prevent coverage regression.

---

### TST-005: Tautological mock assertion in cleanup test

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_upload_api.py |
| **Classification** | advisory |

**Description:** test_upload_api.py line 669 uses `mock_cleanup.assert_called()` but the mock is created with `wraps=file_cleanup.cleanup_task_files`, meaning it calls the real function. The assertion only verifies that the real function was called, not that cleanup behavior is correct. This is a tautological test - it tests that the test called the function, not that the function works correctly.

**Evidence:**
```python
# tests/test_upload_api.py:644-669
mock_cleanup = mocker.patch(
    "mkobi.services.file_cleanup.cleanup_task_files",
    wraps=file_cleanup.cleanup_task_files,
)
# ... later ...
file_cleanup.cleanup_task_files(task_id=UUID(task_id))
mock_cleanup.assert_called()  # Only proves the function was called
```

**Recommendation:** Remove the tautological assertion or verify actual cleanup occurred (which test_temp_file_deleted_after_successful_upload does better at line 600-611).

---

### TST-006: Critical path: Token refresh flow incomplete test coverage

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | tests/test_auth.py |

**Description:** The token refresh test at line 176-217 tests the happy path but does not test refresh token expiration, revoked tokens, or concurrent refresh attempts. Additionally, the test at line 198-217 creates a valid refresh token but doesn't verify that the old access token is actually invalidated or that the refresh token itself has proper expiration handling.

**Evidence:**
```python
# tests/test_auth.py:176-217
async def test_refresh_valid_token(
    self, async_client: AsyncClient, test_user: dict
) -> None:
    """Test refresh with valid token returns new access token."""
    # Creates token, calls endpoint, checks success
    # Missing: test expiring refresh tokens, revoked tokens
```

**Recommendation:** Add tests for:
- Refresh token with expired token
- Refresh token with invalid signature
- Multiple concurrent refresh attempts (rate limiting)
- Token rotation verification

---

### TST-007: Mock Redis in conftest.py has empty method bodies (potential silent failures)

| Field | Value |
|-------|-------|
| **ID** | TST-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py |
| **Classification** | advisory |

**Description:** The MockRedis and MockPipeline classes in conftest.py have empty method bodies for `expire`, `execute`, and `close` methods (lines 130-137, 163-165). These are called by the real Redis client but do nothing in tests. If code depends on TTL behavior or explicit execution, tests would silently pass while production behavior differs.

**Evidence:**
```python
# tests/conftest.py:130-137
async def expire(self, key, ttl):
    pass  # TTL is not enforced in tests

async def execute(self):
    pass  # Pipeline execution not simulated

async def close(self):
    pass  # Connection cleanup not simulated
```

**Recommendation:** Either implement proper TTL tracking in MockRedis or document that these methods are intentionally no-ops. Consider adding warnings if these methods are called unexpectedly.

---

### TST-008: Missing test for data transformer edge cases

| Field | Value |
|-------|-------|
| **ID** | TST-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_data_transformations.py |
| **Classification** | advisory |

**Description:** The test_data_transformations.py tests cover basic aggregation and filter cases but miss critical edge cases in data processing:
- Empty DataFrame handling
- Null value propagation in aggregations
- Division by zero in YoY calculations (partially covered but not explicitly)
- Date parsing failures
- Large file memory considerations

**Evidence:**
```python
# test_data_transformations.py:388-385 - tests transformations_invalid_config_raises
# But no test for empty DataFrame, all nulls, or extreme values
```

**Recommendation:** Add tests for:
- Transformations on empty DataFrame
- Aggregations with all-null columns
- YoY calculation with missing year values
- Share calculation with negative values

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 2 |

**Total Findings:** 8

---

## Mandatory Fixes

- TST-002: Global graph endpoints lack dashboard access verification in tests
- TST-003: Frontend has critically low test coverage (3 test files for entire React app)

---

## Advisory Recommendations

- TST-001: Heavy mocking patches obscure actual business logic testing
- TST-004: No coverage threshold enforcement in CI config (frontend)
- TST-005: Tautological mock assertion in cleanup test
- TST-006: Token refresh flow incomplete test coverage
- TST-007: Mock Redis has empty method bodies (potential silent failures)
- TST-008: Missing test for data transformer edge cases