# Phase 06 Audit Findings — Test Quality

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: Test expects None JWT secret to be accepted but YAML config provides default value

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/test_config.py |
| **Classification** | mandatory |

**Description:** Test `test_none_jwt_secret_accepted` in `tests/test_config.py` expects that when `JWT__SECRET_KEY` is deleted from environment, the settings should accept `None` as the secret key value. However, the test fails because the conftest.py sets `JWT__SECRET_KEY` as a default environment variable that takes precedence due to pydantic-settings loading order, and additionally the project's `.env` file contains `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`. The base Settings class also defaults JWT secret_key to `None` in the model definition, but the .env override pattern prevents testing the actual "no secret" scenario. This creates a false assumption that None values are properly handled when the production configuration flow actually requires a strong secret.

**Evidence:**
- Test file: `tests/test_config.py:377-381`
- Conftest sets default: `tests/conftest.py:25` `os.environ.setdefault("JWT__SECRET_KEY", "test_secret_key_change_in_production")`
- `.env` file: `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`
- Config model: `src/mkobi/config.py:127` `secret_key: str | None = None`
- Test failure output: `AssertionError: assert 'dev-secret-key-for-security-testing-do-not-use-in-prod-32chars' is None`

**Recommendation:** Either remove the default JWT__SECRET_KEY from `.env` (since it should be required in all non-test environments) or update the test to use `pytest.mark.skip` with a clear explanation that None JWT secret is only relevant for specific edge configuration scenarios. The current test structure conflicts with the project's security requirements where JWT secret should always be set.

---

### TST-002: Test assertion mismatch - MIME type error message differs from expected pattern

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/test_data_service.py |
| **Classification** | mandatory |

**Description:** Test `test_validate_file_invalid_extension` expects the error message to match `"Detected MIME type text/plain not allowed"`, but the actual error raised is `"Invalid file format: 'test.txt'. Allowed formats: csv.gz, csv"`. This indicates the test comment is outdated - the validation now checks file extension BEFORE MIME type validation (or in a different order than the test assumes), causing the wrong error to be raised. The test is verifying implementation details that don't match the actual code flow.

**Evidence:**
- Test file: `tests/test_data_service.py:552-576`
- Production code: `src/mkobi/services/file_processing.py:127-141`
- Test error expectation: `match="Detected MIME type text/plain not allowed"`
- Actual error raised: `"Invalid file format: 'test.txt'. Allowed formats: csv.gz, csv"`

**Recommendation:** Update the test to match the actual behavior. The file extension check happens before or instead of the MIME type check for files with `.txt` extension. Either update the test expectation to match the actual error message, or restructure the code to perform MIME validation first and update the test accordingly.

---

### TST-003: Tautological test - test_store_fail_open_on_error asserts only that no exception was raised

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/core/test_temp_password_store.py |
| **Classification** | advisory |

**Description:** Test `test_store_fail_open_on_error` at line 177 only asserts `assert True` after the store operation completes without raising an exception. This test cannot actually fail - it only verifies that code didn't crash, not that the failure mode is correct. A proper test should verify that the mock was called, that the error was logged appropriately, or that the system state reflects graceful degradation.

**Evidence:**
- File: `tests/core/test_temp_password_store.py:163-177`
- Test calls `store.store("token", "password")` with a failing Redis mock
- Only assertion: `assert True` (line 177) - tautological assertion that always passes

**Recommendation:** Replace `assert True` with meaningful assertions such as:
- Verify that the failing Redis `set` method was actually called (to confirm the code path)
- Verify that the error was logged (if logging is testable)
- Verify that internal state reflects the attempt was made

---

### TST-004: Mock-heavy unit tests verify mock calls instead of outcomes (test_graph_service.py)

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_graph_service.py |
| **Classification** | advisory |

**Description:** Tests in `test_graph_service.py` extensively verify mock calls (`mock_graph_repo.create.assert_called_once()`, `mock_graph_repo.update.assert_called_once()`) rather than actual outcomes. For example, `test_create_graph_success` at line 63 only asserts the mock was called, not that the returned data is correct. These tests are testing the mock framework, not the actual business logic. When mocks ARE the implementation (because tests don't use real database), this creates false confidence.

**Evidence:**
- File: `tests/test_graph_service.py:63, 157`
- Line 63: `mock_graph_repo.create.assert_called_once()`
- Line 157: `mock_graph_repo.update.assert_called_once()`
- These tests use `AsyncMock()` without real repository integration

**Recommendation:** Convert mock-heavy tests to integration tests that verify actual outcomes. Use the existing `async_db_session` fixture to test against a real database. Tests should verify that data is correctly persisted and retrieved, not that mocks were called.

---

### TST-005: Mock-heavy unit tests verify mock calls instead of outcomes (test_auth_service.py)

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/test_auth_service.py |
| **Classification** | advisory |

**Description:** Similar to TST-004, tests in `test_auth_service.py` excessively verify mock calls rather than real outcomes. Tests at lines 60, 446, 447, 464, 482, 516 assert mock invocations but don't verify database state. For example, `test_reset_password_admin_success` only checks that mocks were called, not that the user was actually updated in a real database. This violates the principle that tests should verify behavior, not implementation details.

**Evidence:**
- File: `tests/test_auth_service.py:60, 446-447, 464, 482, 516`
- Line 60: `mock_user_repo.create.assert_called_once()`
- Lines 446-447: Mock assertions for update and commit
- Lines 464, 482: Mock assertions for DB commit and update
- Line 516: `mock_temp_password_store.store.assert_called_once()`

**Recommendation:** Convert to integration tests using real database session, or add meaningful outcome assertions that verify the actual state changes. The existing `test_services_integration.py` provides a good pattern for this.

---

### TST-006: Frontend tests have act() warnings for async state updates

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/features/auth/model/__tests__/useAuth.test.tsx |
| **Classification** | advisory |

**Description:** Multiple frontend tests in `useAuth.test.tsx` emit `act()` warnings indicating that React state updates inside async operations are not properly wrapped. This can lead to tests that pass but don't accurately represent user behavior, or tests that flake due to timing issues. The warnings occur because `waitFor` is used but the state updates happen outside of proper React act() boundaries.

**Evidence:**
- Test file: `frontend/src/features/auth/model/__tests__/useAuth.test.tsx`
- Warnings for: initialization, login, logout, registerRequest, getProfile test cases
- vitest output shows: "An update to TestComponent inside a test was not wrapped in act(...)"

**Recommendation:** Wrap async state updates in `act()` or use proper vitest async utilities. Follow React Testing Library best practices for async hooks. Use `waitFor` with proper callback assertions that ensure state is fully updated before asserting.

---

### TST-007: Critical path - rate limiter tests exist but lack fail-open behavior verification in production config

| Field | Value |
|-------|-------|
| **ID** | TST-007 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_auth.py (TestRateLimiting) |
| **Classification** | advisory |

**Description:** While rate limiter tests exist (TestRateLimiting class), there are no tests that verify the actual API endpoints use rate limiting correctly in scenarios where Redis fails. The tests only verify the rate limiter class itself, not the integration with auth endpoints. The `rate_limiter_fail_closed` configuration exists but isn't tested at the endpoint level.

**Evidence:**
- File: `tests/test_auth.py:263-391` - rate limiter tests test the class only
- No tests in `test_auth_api.py` that verify rate limiting on login endpoint
- Config flag: `rate_limiter_fail_closed: bool = Field(default=False, ...)`

**Recommendation:** Add integration tests that verify rate limiting behavior on actual auth endpoints, including:
- Login rate limiting when credentials are wrong (security critical)
- Fail-open behavior when Redis is unavailable
- Rate limit headers in responses

---

### TST-008: Coverage failure - total coverage 68% below required 80%

| Field | Value |
|-------|-------|
| **ID** | TST-008 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi (entire codebase) |
| **Classification** | advisory |

**Description:** The test suite ran with coverage and reported 68% total coverage, which is below the required 80% threshold defined in `pyproject.toml`. Multiple critical modules have zero or very low coverage including `base_repository.py (0%)`, `registry.py (0%)`, `decorators.py (0%)`, indicating these are either unused code or lack any tests.

**Evidence:**
- Coverage output: `TOTAL ... 68% (fail_under=80)`
- Zero coverage modules:
  - `src/mkobi/core/base_repository.py` - 0%
  - `src/mkobi/data/processing/registry.py` - 0%
  - `src/mkobi/utils/decorators.py` - 0%
  - `src/mkobi/db/repositories/dashboard_filter_repo.py` - 0%
- pyproject.toml: `fail_under = 80` at line 216

**Recommendation:** Either remove unused/dead code (base_repository.py and registry.py appear to be legacy or unused) or add comprehensive tests. Critical paths like `dashboards_access.py` (32% coverage) and `dashboards_filters.py` (26% coverage) need additional test coverage to meet the 80% requirement.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 1 |

## Mandatory Fixes

- TST-001: Test expects None JWT secret to be accepted but YAML config provides default value
- TST-002: Test assertion mismatch - MIME type error message differs from expected pattern

## Advisory Recommendations

- TST-003: Tautological test - test_store_fail_open_on_error asserts only that no exception was raised
- TST-004: Mock-heavy unit tests verify mock calls instead of outcomes (test_graph_service.py)
- TST-005: Mock-heavy unit tests verify mock calls instead of outcomes (test_auth_service.py)
- TST-006: Frontend tests have act() warnings for async state updates
- TST-007: Rate limiter tests exist but lack integration with auth endpoints
- TST-008: Coverage failure - total coverage 68% below required 80%

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `TST-001`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction |
| `classification` | enum | `mandatory` or `advisory` |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements