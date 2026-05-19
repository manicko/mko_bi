# Test Audit Report #1 - Architecture/Contract Mismatch

**Date:** 2026-05-19
**Auditor:** Kilo Architecture Audit

## Summary

Analysis of the mkobi test suite identified several categories of problematic tests that violate project conventions, lack meaningful assertions, or use inappropriate testing patterns for the established architecture.

---

## Critical Findings

### 1. Architecture/Contract Mismatch

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_auth_service.py | `test_register_user_empty_password` | Empty password treated as valid input, then wrapped in `try/except` with `hasattr` check - tests implementation detail, not validation | Delete or rewrite to verify validation failure for empty passwords |
| tests/test_data_service.py | All tests using `mock_repos` fixture | Heavy mocking of repositories instead of using test DB; mocks verify mock values, not real business logic; patches internal functions like `check_dashboard_access` | Rewrite to use real test database via `async_db_session` fixture |
| tests/test_graph_service.py | All unit tests with `mock_graph_repo` | Mocks repository instead of testing against real DB; verifies mock method calls rather than business outcomes | Delete and rewrite integration tests with test DB, or keep minimal unit tests in separate file |

### 2. No Business Logic Verification

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_repositories.py | `test_create_user`, `test_get_by_id`, `test_update_user`, `test_delete_user` | Only verify object creation and HTTP status codes; no verification of actual DB state persistence, no side effects checked | Add assertions verifying DB state before/after, or delete as redundant with conftest fixture tests |
| tests/test_processing_logs.py | `test_filter_defaults`, `test_create_model`, `test_read_model` | Only verify Pydantic model field values; no business logic being tested | Consider moving to pure model validation tests or delete |
| tests/test_pydantic_models.py | Multiple model field tests | Superficial tests verifying only field existence; no business rules verification | Consolidate into fewer, more meaningful tests |

### 3. Weak Coverage & Low Value

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_upload_api.py | `test_upload_csv_success` | Only verifies HTTP 201 and `message`/`processing_log_id` in response; no verification of actual file processing, DB state, or temp file cleanup | Add assertions for processing_logs status lifecycle, verify aggregated_data exists, verify temp file cleanup |
| tests/test_upload_api.py | `test_upload_csv_gz_success` | Same as above - superficial status check only | Same as above |
| tests/test_upload_api.py | `test_upload_mode_overwrite`, `test_upload_mode_append` | Only verify HTTP 201 without checking data was actually processed/overwritten/appended | Verify DB state changes reflect the mode |
| tests/test_data_service.py | `test_get_aggregated_data_empty` | Returns empty list assertion only - no business value | Delete as trivial |
| tests/test_graphs.py | `test_get_graphs_for_dashboard` | Only asserts `len(data) >= 2`; no verification of graph content, relationships | Add verification of graph properties match what was created |

### 4. Excessive Mocking Instead of Test Database

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_auth_service.py | All mocked unit tests | Uses `MagicMock` for user objects instead of testing against real database state; mocks bypass actual business logic | Rewrite integration tests with test DB, keep minimal unit tests separate |
| tests/test_graph_service.py | All tests with `mock_graph_repo` | Repository is mocked instead of using test database; verifies mock calls, not real state changes | Delete or convert to integration tests |
| tests/test_data_service.py | All tests using `mock_repos` fixture | Heavy mocking defeats the purpose of testing data processing; internal function patches like `patch("mkobi.services.data_service.check_dashboard_access")` create brittle tests | Delete and rewrite with real test database |

### 5. mkobi-Specific Anti-Patterns Not Tested

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_upload_api.py | All upload tests | No verification of JSONB normalization (dims key sorting), no verification of temp file cleanup, no verification of processing_logs status transitions | Add these critical mkobi-specific assertions |
| tests/test_auth_service.py | `test_login_user_success` | Verifies `display_name` exists but doesn't verify it's computed correctly from email prefix | Add assertion that `display_name == "test"` for `test@example.com` |
| tests/test_auth.py | `test_login_success` | Same issue - verifies `display_name` exists but doesn't verify computation | Add proper display_name computation verification |
| tests/test_dashboards_api.py | `TestAdminBypass` tests | Tests admin bypass but doesn't verify 403/404 dual-signal behavior edge cases | Add tests for non-existent dashboard admin bypass scenarios |

### 6. Quality & Maintenance Problems

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_data_service.py | All mocked service tests | Heavily coupled to internal implementation via `patch()` calls; fragile when internal paths change | Rewrite to test API layer with real DB |
| tests/test_auth_service.py | `test_register_user_empty_password` | Uses `hasattr` check with conditional assertion - unclear test intent | Delete or rewrite with clear validation expectations |
| tests/test_graphs.py | Tests 1-52 lines | Tests don't use shared fixtures from conftest.py for user creation; duplicate user creation logic | Refactor to use shared fixtures |

### 7. Tests That Break After Architecture Refactoring

| FilePath | TestName | Problem | Recommendation |
|----------|----------|---------|----------------|
| tests/test_data_service.py | All tests with `mock_repos` | Will break if service introduces new dependencies or changes method signature | Delete and replace with integration tests |

---

## Statistics

| Category | Count |
|----------|-------|
| Tests with heavy mocking over test DB | 45+ |
| Tests with no business logic verification | 20+ |
| Tests missing mkobi-specific assertions | 15+ |
| Tests with only status code assertions | 10+ |

---

## Recommendations

### High Priority (Delete/Rewrite)
1. **test_data_service.py** - Complete rewrite. Either delete mocked unit tests and keep only API-level integration tests, OR convert to use test database.
2. **test_auth_service.py::test_register_user_empty_password** - Delete or rewrite with clear validation expectations.
3. **test_upload_api.py** tests - Add missing business logic verification (DB state, temp file cleanup, processing_logs lifecycle).

### Medium Priority (Improve)
1. **test_repositories.py** - Add verification of actual DB state changes.
2. **test_graphs.py** - Add verification of graph content relationships.
3. **test_pydantic_models.py** - Consolidate redundant field verification tests.

### Low Priority (Nice to Have)
1. Add missing mkobi-specific test assertions (JSONB normalization, display_name computation, admin bypass edge cases, rate limiting, temp file cleanup).