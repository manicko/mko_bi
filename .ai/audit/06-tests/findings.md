---
name: 06-tests
description: Test quality audit findings
agent: audit-executor
---

# Phase 06 Audit Findings — Test Quality

**Executor:** audit-executor  
**Template:** .ai/audit/templates/audit-findings.md  
**Status:** complete  
**Validated:** no  

---

## Findings

### TST-001: Test Authentication Flow Coverage

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_auth.py, tests/test_auth_api.py |
| **Classification** | mandatory |

**Description:** The authentication flow tests cover both success and failure paths comprehensively. The test_auth_api.py file tests cookie-based authentication (login sets refresh cookie, refresh reads from cookie, logout clears cookie), while test_auth.py covers login success, wrong password, non-existent user, registration request flows, and rate limiting. However, the tests use hard-coded test credentials with a test secret key that is also used in other contexts, potentially creating security concerns for test isolation.

**Evidence:** 
- `tests/test_auth.py` lines 17-63: Login success/failure tests exist for wrong password and non-existent user
- `tests/test_auth_api.py` lines 35-140: Cookie-based auth flow tests for login/refresh/logout
- `tests/test_auth.py` lines 220-348: Rate limiting tests with strict_redis fixture
- `conftest.py` line 24: Hard-coded JWT secret "test_secret_key_change_in_production"

**Recommendation:** Consider using dynamically generated test secrets or environment-specific test configurations to avoid potential credential leakage. The test secret key should be unique per test run and not reusable across different test contexts.

---

### TST-002: Authorization Boundary Tests Present

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_permissions.py, tests/test_deps.py |
| **Classification** | mandatory |

**Description:** Authorization boundary tests verify different roles (viewer, editor, admin) against various dashboard permissions (view, edit, admin). Tests confirm that: (1) admins bypass dashboard access checks, (2) viewers cannot edit, (3) editors with edit permission cannot perform admin-only actions. However, the tests rely on async_db_session fixture which creates real database entries without proper cleanup, potentially causing test pollution.

**Evidence:**
- `tests/test_permissions.py` lines 58-283: Role hierarchy tests and dashboard access tests
- `tests/test_deps.py` lines 130-360: Role requirement tests and dashboard access tests
- Tests create users with real database commits but don't consistently clean up after assertion failures
- Some tests add users to database without cleanup in finally blocks (e.g., test_users_api.py lines 94-98)

**Recommendation:** Add explicit cleanup in finally blocks to ensure test data doesn't persist after test failures. Consider using pytest fixtures that automatically clean up test data.

---

### TST-003: File Upload and Processing Flow Tests

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_upload_api.py |
| **Classification** | mandatory |

**Description:** File upload tests cover success cases, MIME-type validation, file size limits, permission checks, and different upload modes (overwrite, append). Tests also verify temp file cleanup on success and failure. However, the test for wrong delimiter (`test_upload_malformed_csv_wrong_delimiter`) accepts multiple status codes (201, 400, 422) without clear expectations, and the temp file cleanup test manually creates task files rather than testing actual endpoint behavior.

**Evidence:**
- `tests/test_upload_api.py` lines 86-114: Successful CSV upload test
- `tests/test_upload_api.py` lines 175-189: Wrong extension/MIME type tests
- `tests/test_upload_api.py` lines 324-357: Wrong delimiter test accepts ambiguous status codes ("accept success or rejection")
- `tests/test_upload_api.py` lines 667-748: Cleanup test manually creates files instead of testing actual endpoint flow

**Recommendation:** Clarify expected behavior for malformed CSV files and either fix the endpoint or update tests to expect specific status codes. The cleanup test should be refactored to test the actual upload endpoint flow rather than manually creating files.

---

### TST-004: Data Transformation and Aggregation Tests

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_data_transformations.py, tests/test_data_csv_loader.py |
| **Classification** | mandatory |

**Description:** Data transformation tests cover aggregations (sum, mean, count, min, max), YoY calculations, share calculations, formula parsing, and type transformations. However, the tests use hardcoded expected values (e.g., `pytest.approx(16.67)`) which may be fragile, and some tests for unknown functions/columns silently skip without explicit validation.

**Evidence:**
- `tests/test_data_transformations.py` lines 391-403: Aggregation tests with sum/mean
- `tests/test_data_transformations.py` lines 457-511: YoY calculation tests
- `tests/test_data_transformations.py` lines 436-440: Unknown function "skips" without explicit verification
- `tests/test_data_csv_loader.py` lines 386-395: Unknown operator test returns all rows (no filtering applied) without explicit assertion about expected behavior

**Recommendation:** Add explicit assertions for unknown functions/columns behavior and use relative tolerance instead of absolute values for floating-point comparisons to improve test robustness.

---

### TST-005: Test Anti-Patterns - Mock Verification

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_data_service.py |
| **Classification** | mandatory |

**Description:** Unit tests in test_data_service.py verify mock calls (e.g., `log_repo.create_log.assert_called_once()`) rather than asserting actual outcomes. This is a classic test anti-pattern that tests implementation details rather than behavior. The tests mock the entire repository tree but then verify that mocks were called, which provides no value for correctness validation.

**Evidence:**
- `tests/test_data_service.py` line 69: `log_repo.create_log.assert_called_once()` - verifying mock call, not outcome
- `tests/test_data_service.py` line 68: Asserts `result.message` contains "File uploaded successfully" but this is mocked data
- `tests/test_data_service.py` lines 490-495: Tests verify `mock_log.status` was set, but mock_log is a MagicMock with arbitrary attributes
- The fixture `mock_repos` creates AsyncMock objects that return other MagicMock objects without real behavior

**Recommendation:** Refactor unit tests to use integration-style testing with real database sessions (following test_services_integration.py pattern) or focus on testing public interfaces without mocking internal implementation details. Remove assertions that verify mock calls and instead test actual outcomes.

---

### TST-006: Async Tests Properly Configured

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py |
| **Classification** | advisory |

**Description:** Async tests are properly configured with `@pytest.mark.asyncio` decorator and `asyncio_mode = "auto"` in pyproject.toml. However, some tests use `@pytest.mark.asyncio` class decorator (e.g., TestDataServiceIntegration at line 18) while others rely on auto mode. The mix of approaches is inconsistent.

**Evidence:**
- `pyproject.toml` line 204: `asyncio_mode = "auto"` configured
- `tests/conftest.py`: No async-specific configuration issues
- `tests/test_data_service.py` line 18: Uses `@pytest.mark.asyncio` on class (unnecessary with auto mode)
- `tests/test_services_integration.py` line 35: Uses `@pytest.mark.asyncio` on class (unnecessary with auto mode)

**Recommendation:** Remove redundant `@pytest.mark.asyncio` class decorators since `asyncio_mode = "auto"` already handles this. Maintain consistency by either using auto mode exclusively or explicit markers.

---

### TST-007: Test Database Isolation

| Field | Value |
|-------|-------|
| **ID** | TST-007 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/conftest.py |
| **Classification** | mandatory |

**Description:** Test database isolation uses SAVEPOINT pattern with `async_db_session` fixture (function-scoped). The fixture uses `session.begin_nested()` with event listeners to restart savepoints after commits, which is a good pattern. However, the `setup_test_database` fixture has session scope and recreates the entire database, which can cause issues in CI environments where database recreation might fail.

**Evidence:**
- `conftest.py` lines 356-385: Uses SAVEPOINT pattern with `begin_nested()` and event listener for proper rollback
- `conftest.py` lines 327-344: Uses `NullPool` to prevent connection pooling issues
- `conftest.py` lines 302-324: `setup_test_database` runs once per session with database recreation
- Environment variable `RECREATE_TEST_DB` set to "true" in conftest.py line 27

**Recommendation:** Consider adding transactional DDL support or alembic migrations for test database setup instead of full database recreation. This would be more reliable in CI environments. Also, ensure the cleanup in `async_db_session` runs even on test failure by using try-finally pattern (already present at line 382-384).

---

### TST-008: Error Handling Path Tests

| Field | Value |
|-------|-------|
| **ID** | TST-008 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_data_csv_loader.py, tests/test_data_validator.py |
| **Classification** | mandatory |

**Description:** Error handling paths are tested for various scenarios: empty files, invalid MIME types, oversized files, malformed formulas, null values, etc. However, some error handling tests are inconsistent - for example, `test_upload_malformed_csv_wrong_delimiter` accepts multiple status codes without clear validation of expected behavior, and `test_upload_invalid_data_types` similarly accepts multiple outcomes without clear expectations.

**Evidence:**
- `tests/test_data_csv_loader.py` lines 127-160: File not found and separator tests
- `tests/test_data_validator.py` lines 118-122: Empty dataframe error handling
- `tests/test_upload_api.py` lines 342-357: Wrong delimiter test accepts 201, 400, or 422 without asserting expected behavior
- `tests/test_upload_api.py` lines 488-506: Invalid data types test accepts 201, 400, or 422

**Recommendation:** Define clear expected behavior for malformed/invalid data inputs and update tests to assert specific outcomes. This ensures the API contract is well-defined and tested consistently.

---

### TST-009: Input Validation Rejection Cases

| Field | Value |
|-------|-------|
| **ID** | TST-009 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_data_validator.py, tests/test_data_csv_loader.py |
| **Classification** | mandatory |

**Description:** Input validation tests cover required columns, file extensions, MIME types, file size limits, and schema validation. Tests for strict schema mode validate rejection of extra columns. However, there are no tests for SQL injection or malicious input patterns, and the validation tests don't cover edge cases like null bytes in file content or extremely long column names.

**Evidence:**
- `tests/test_data_validator.py` lines 31-37: File extension validation tests
- `tests/test_data_validator.py` lines 66-292: Schema validation tests including strict mode
- `tests/test_data_csv_loader.py` lines 127-160: File validation tests
- No tests for malicious inputs, path traversal, or injection attacks in upload validation

**Recommendation:** Add security-focused input validation tests for malicious patterns (path traversal, null bytes, extremely long strings, etc.) to ensure the validation layer is robust against attack vectors.

---

### TST-010: Frontend Test Coverage Gap

| Field | Value |
|-------|-------|
| **ID** | TST-010 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/features/auth/model/__tests__/, frontend/src/shared/types/__tests__/ |
| **Classification** | mandatory |

**Description:** Frontend tests are minimal and only cover token management utility functions. There are no tests for: (1) authentication hooks/queries, (2) protected route components, (3) API service error handling, (4) form validation schemas, (5) graph rendering components, or (6) dashboard feature components. The coverage gap is significant for a production application.

**Evidence:**
- `frontend/src/features/auth/model/__tests__/authToken.test.ts`: Only 165 lines testing token storage/retrieval
- `frontend/src/shared/types/__tests__/formSchemas.test.ts` and `enums.test.ts`: Type tests
- No tests under `frontend/src/features/dashboards/`, `frontend/src/features/upload/`, or other key features
- No component tests for Plotly graph rendering or TanStack Query integration

**Recommendation:** Expand frontend test coverage to include authentication flows, protected routes, API service error handling, form validation, and graph rendering components. Consider adding integration tests for critical user workflows.

---

### TST-011: Missing Type Safety in Some Test Files

| Field | Value |
|-------|-------|
| **ID** | TST-011 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_deps.py, tests/test_auth.py, tests/test_users_api.py |
| **Classification** | advisory |

**Description:** Some test files have inconsistent return type hints on test methods. While mypy is configured to ignore errors in the tests directory (`pyproject.toml` line 195), adding type hints would improve code maintainability and catch potential issues early.

**Evidence:**
- `tests/test_deps.py` lines 46-50: Test methods lack return type hints
- `tests/test_users_api.py` lines 49-50: Type hints present but inconsistent across test methods
- `pyproject.toml` lines 189-195: Tests are configured to ignore mypy errors

**Recommendation:** Add consistent type hints to all test methods for better documentation and maintainability, even if mypy is not enforcing them.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 5 |
| LOW | 2 |

## Mandatory Fixes

- **TST-001**: Improve test authentication security by using unique test secrets
- **TST-002**: Add explicit test data cleanup in finally blocks for authorization tests
- **TST-003**: Clarify expected behavior for malformed CSV uploads and refactor cleanup tests
- **TST-004**: Add explicit assertions for unknown function/column behavior in data transformation tests
- **TST-005**: Refactor unit tests to focus on outcomes rather than mock call verification
- **TST-007**: Improve database isolation reliability in CI environments
- **TST-008**: Define clear expected outcomes for invalid data type tests
- **TST-009**: Add security-focused input validation tests
- **TST-010**: Expand frontend test coverage significantly

## Advisory Recommendations

- **TST-006**: Remove redundant `@pytest.mark.asyncio` decorators with auto mode
- **TST-011**: Add consistent type hints to all test methods

## Doc Updates Needed

None