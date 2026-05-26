# Test Quality Audit Report — mkobi BI Dashboard

**Date:** 2026-05-26
**Scope:** All 24 test files in `tests/` (excluding `__pycache__`)
**Total test files:** 24
**Total test classes:** ~85
**Total test methods:** ~310

---

## Summary

| Category | Count |
|----------|-------|
| `[TEST-DELETE]` — harmful or worthless | 3 |
| `[TEST-REWRITE]` — right intent, wrong implementation | 5 |
| `[TEST-UPDATE]` — needs minor updates to match code | 4 |
| `[BEST-PRACTICE]` — missing coverage or quality improvement | 12 |
| `[DOC-UPDATE]` — docs/spec should be updated | 0 |

---

## Findings

### `[TEST-DELETE]` — Tests That Are Harmful or Worthless

| # | FilePath | TestName | Type | Problem | Recommendation |
|---|----------|----------|------|---------|----------------|
| 1 | `tests/test_data_csv_loader.py` | `TestLoadCSVAsync::test_load_csv_wrapper` | [TEST-DELETE] | Tests synchronous `CSVLoader.load_csv()` and calls it "async load_csv wrapper". The comment says "Full async testing would require event loop" — then doesn't use one. The test doesn't actually test any async behavior; it duplicates `test_load_csv_basic` with different wording. | Delete. The function `load_csv` is synchronous by nature (Polars reads). If an async wrapper exists, test it properly with `pytest.mark.asyncio`. |
| 2 | `tests/test_data_service.py` | `TestDataService::test_process_upload_no_user_skips_permission` | [TEST-DELETE] | The test patches `enqueue_job` but never asserts it was called. It also doesn't verify that `check_dashboard_access` was NOT called (the core assertion of the test name). The test only asserts `result.task_id == log_id`, which would pass even if permission check ran. | Delete or rewrite to actually assert `check_dashboard_access` was not called (use `assert_not_called` on a mock). |
| 3 | `tests/test_data_service.py` | `TestDataService::test_process_upload_file_too_large` | [TEST-DELETE] | Wraps `Path.stat` with a mock inside a `try/finally` block, but the `try/finally` is unnecessary complexity. More importantly, the test creates a real temp file, mocks its size, but the `process_upload` method validates file size via `file_path.stat().st_size` which is mocked — however the test also creates the file on disk, making it fragile. The mock approach is convoluted and tests an implementation detail rather than behavior. | Rewrite to use a simpler approach: either test via the API layer with a real large file, or directly test `validate_file` with a mocked size. |

---

### `[TEST-REWRITE]` — Right Intent, Wrong Implementation

| # | FilePath | TestName | Type | Problem | Recommendation |
|---|----------|----------|------|---------|----------------|
| 4 | `tests/test_auth_service.py` | `TestAuthService::test_register_user_empty_password` | [TEST-REWRITE] | Creates a user with empty password and asserts `isinstance(result, UserRead)` — but doesn't verify the password was actually hashed or that the user can authenticate. The assertion `verify_password("", result.password_hash) if hasattr(result, 'password_hash') else True` is a no-op because `UserRead` doesn't have `password_hash` — it always evaluates to `True`. This test provides a false sense of security. | Rewrite to verify that registration with empty password either (a) raises a validation error (preferred), or (b) the created user can actually authenticate with an empty password. |
| 5 | `tests/test_auth_service.py` | `TestAuthService::test_login_user_success` | [TEST-REWRITE] | Asserts `hasattr(result["user"], "display_name")` — but `result["user"]` is a `UserRead` Pydantic model returned from the service layer. The test constructs `mock_user` with `MagicMock()` which means `result["user"]` is built from a MagicMock, not a real DB object. The `display_name` check works by accident because Pydantic computes it from email. However, the test doesn't verify the actual `display_name` value (should be `"test"` from `test@example.com`). | Add `assert result["user"].display_name == "test"` to verify the computed field value. |
| 6 | `tests/test_dashboards_api.py` | `TestUpdateDashboard::test_update_dashboard_admin` | [TEST-REWRITE] | The test grants `DashboardPermission.EDIT` to the test user, but the PUT endpoint requires `require_admin_role` (global admin role), not dashboard-level edit permission. The test passes because `test_user` has the `admin` role — but the test name and setup are misleading. The `grant_access` with `EDIT` permission is irrelevant; any admin can update any dashboard. | Rewrite to clarify: either test that admin can update without explicit dashboard access, or test that a non-admin editor with dashboard EDIT permission gets 403 (which is the actual behavior). |
| 7 | `tests/test_dashboards_api.py` | `TestDeleteDashboard::test_delete_dashboard_admin` | [TEST-REWRITE] | Same issue as #6: grants `DashboardPermission.EDIT` but the DELETE endpoint requires `require_admin_role`. The grant is unnecessary and misleading. | Remove the `grant_access` call. Admin can delete any dashboard without explicit access. Add a comment explaining admin bypass. |
| 8 | `tests/test_data_service.py` | `TestDataService::test_trigger_processing_success` | [TEST-REWRITE] | The test patches `find_task_file` to return `"/tmp/test.csv"` but never verifies the file is cleaned up after processing. Per SPEC.md, temp files must be deleted after processing. The test also doesn't verify the processing log status transition from UPLOADED → PROCESSING. | Add assertions for: (1) log status was updated to PROCESSING, (2) temp file cleanup was triggered (if applicable in the code path). |

---

### `[TEST-UPDATE]` — Needs Minor Updates to Match Current Code

| # | FilePath | TestName | Type | Problem | Recommendation |
|---|----------|----------|------|---------|----------------|
| 9 | `tests/test_auth_api.py` | `TestCookieAuthFlow::test_login_sets_refresh_cookie` | [TEST-UPDATE] | Asserts `"secure" in set_cookie.lower()` — but in test environment (HTTP, not HTTPS), the `secure` cookie attribute may not be set. The test uses `httpx.AsyncClient` with `base_url="http://testserver"` which is not HTTPS. This may cause intermittent failures depending on cookie configuration. | Verify the actual cookie behavior in test env. If `secure` is not set in test, update the assertion or configure the test to expect the correct behavior. |
| 10 | `tests/test_deps.py` | `TestDashboardAccessDependencies::test_write_access_with_edit_permission` | [TEST-UPDATE] | The test expects `403` when an editor with dashboard `edit` permission tries to PUT a dashboard. The comment says "Editor should get 403 because update endpoint requires admin role" — this is correct, but the test name `test_write_access_with_edit_permission` is misleading since it tests the opposite (write is denied). | Rename to `test_write_access_with_edit_permission_denied` or similar. The test is correct but the name implies success. |
| 11 | `tests/test_upload_api.py` | `TestUploadCSV::test_upload_too_large` | [TEST-UPDATE] | Uses a complex mock structure (`type("MockConfig", ...)`) to simulate a small file size limit. The mock doesn't match the actual config structure used by the upload endpoint. The `upload.max_file_size_mb` attribute is set but the endpoint likely checks `max_file_size` (in bytes). | Inspect the actual upload endpoint to find the correct config attribute and mock it properly. Consider using `monkeypatch` on `get_config()` instead of `patch`. |
| 12 | `tests/test_processing_logs.py` | `TestStaleProcessingCleanup::test_cleanup_stale_processing_logs` | [TEST-UPDATE] | The test asserts `"Worker timeout" in updated_stale.message or updated_stale.message is not None` — the `or` clause makes the first check meaningless (any non-None message passes). The actual message in production code is `"Worker timeout - marked as failed by cleanup job"`. | Change to `assert "Worker timeout" in updated_stale.message` without the `or` fallback. |

---

### `[BEST-PRACTICE]` — Missing Coverage or Quality Improvements

| # | FilePath | Area | Type | Problem | Recommendation |
|---|----------|------|------|---------|----------------|
| 13 | `tests/test_auth.py` | Rate limiting | [BEST-PRACTICE] | No tests for login rate limiting behavior. The `_auto_mock_redis` fixture in conftest.py patches `check_rate_limit` to always return `True`, effectively disabling rate limiting in all tests. The `strict_redis` fixture exists but is never used. | Add a test class that uses `strict_redis` to verify: (1) login allowed under limit, (2) login blocked after exceeding limit, (3) fail-open behavior when Redis is unavailable. |
| 14 | `tests/test_auth_api.py` | Cookie security | [BEST-PRACTICE] | Tests verify `httponly`, `secure`, `samesite=strict` in cookies, but don't test the `path` attribute or `max-age`/`expires` for refresh token TTL (7 days per SPEC). | Add assertions for cookie `path` and `max-age` to verify 7-day refresh token lifetime. |
| 15 | `tests/test_dashboards_api.py` | 403/404 dual-signal | [BEST-PRACTICE] | Tests verify 403 (no access) and 404 (not found) separately, but don't test the combined scenario: a non-admin user requesting a dashboard that exists but they don't have access to (should be 403), vs. a dashboard that doesn't exist (should be 404). The current tests use different users for each case. | Add a single test that uses the same non-admin user to request both an existing dashboard (no access → 403) and a non-existent dashboard (→ 404) to verify dual-signal behavior. |
| 16 | `tests/test_upload_api.py` | Temp file cleanup | [BEST-PRACTICE] | No tests verify that temp files are cleaned up after upload processing. The production code has `cleanup_task_files()` in `file_cleanup.py`, but no test asserts it's called. | Add a test that uploads a file and verifies the temp file is deleted from `upload_temp_dir` after processing completes. |
| 17 | `tests/test_upload_api.py` | Processing log creation | [BEST-PRACTICE] | Upload tests verify `processing_log_id` is in the response but don't verify the processing log was actually created in the database with the correct status (`UPLOADED`). | After upload, query the processing log via `GET /admin/logs` and verify the log entry exists with correct status and dashboard_id. |
| 18 | `tests/test_data_service.py` | Processing status lifecycle | [BEST-PRACTICE] | Tests verify individual status queries but don't test the full lifecycle: UPLOADED → PROCESSING → SUCCESS/FAILED. No test verifies that an invalid status transition is rejected. | Add an integration test that creates a log, transitions it through the full lifecycle, and verifies each state. Also test that transitioning from SUCCESS to PROCESSING is handled. |
| 19 | `tests/test_permissions.py` | Token cache (LRU) | [BEST-PRACTICE] | No tests for the LRU token cache behavior (`functools.lru_cache(maxsize=1000)` in `permissions.py`). SPEC.md mentions this as a memory leak prevention measure. | Add tests verifying: (1) repeated token validation uses cache, (2) cache eviction works correctly, (3) cache can be cleared. |
| 20 | `tests/test_processing_logs.py` | Date filtering | [BEST-PRACTICE] | The `ProcessingLogFilter` model supports `date_from` and `date_to` filters (per SPEC.md v2.5), but no tests verify date range filtering works. | Add tests that create logs with different `started_at` timestamps and verify `date_from`/`date_to` filtering returns correct subsets. |
| 21 | `tests/test_repositories.py` | Access repository pagination | [BEST-PRACTICE] | No tests for paginated access queries. The admin logs endpoint uses `skip/limit` pagination (per SPEC.md v2.9, changed from `page/page_size`). | Add tests verifying `skip` and `limit` parameters work correctly in `get_filtered` repository methods. |
| 22 | `tests/test_services_integration.py` | Registration approval flow | [BEST-PRACTICE] | No integration tests for the registration approval flow (`POST /admin/registration-requests/:id/approve`). SPEC.md v2.9 mentions `temp_password` security requirements. | Add integration tests for: (1) approve registration → user created with temp password, (2) user can login with temp password, (3) reject registration → user not created. |
| 23 | `tests/test_config.py` | Weak credential detection | [BEST-PRACTICE] | No tests for `validate_admin_credentials()` which checks against known-weak values (`{"admin", "administrator", "root", "test", "user"}` for usernames, `{"password", "123456", "admin", "secret", "test"}` for passwords). SPEC.md v2.6 mentions this. | Add tests verifying weak credentials are rejected and strong credentials pass validation. |
| 24 | `tests/conftest.py` | Fixture scope mismatch | [BEST-PRACTICE] | The `async_client` fixture depends on `async_db_session` (function scope) but `auth_headers` depends on `test_user` (function scope). The `authenticated_client` depends on both. This creates a chain where all must be function-scoped, which is correct, but the `test_user` fixture commits to the DB (`await async_db_session.commit()`) which can cause issues with the SAVEPOINT rollback pattern. | Verify that `test_user`'s commit doesn't break test isolation. Consider using `flush()` instead of `commit()` for test data setup, or document why commit is necessary. |

---

## Conftest.py Infrastructure Assessment

### Strengths
- Proper async engine setup with `NullPool` to avoid connection pooling issues
- SAVEPOINT-based rollback pattern for test isolation
- `MockRedis` with `MockPipeline` for rate limiter testing
- `strict_redis` fixture available for real rate limiting tests
- Environment variable setup with `setdefault` for Docker Compose compatibility
- Session-scoped database setup fixture

### Issues

| # | Issue | Severity | Recommendation |
|---|-------|----------|----------------|
| C1 | `_auto_mock_redis` is `autouse=True` and patches `AuthService.__init__` to always allow login. This means **no test can accidentally test rate limiting** unless they explicitly use `strict_redis`. This is a safety net but also a blind spot. | Medium | Document this behavior prominently. Consider adding a warning log when the mock is active. |
| C2 | `test_user` fixture calls `await async_db_session.commit()` which breaks the SAVEPOINT rollback pattern. Other tests that depend on `test_user` may see committed data that won't be rolled back. | Medium | Investigate whether `flush()` is sufficient. If commit is needed, document the reason and ensure cleanup. |
| C3 | `mock_db` fixture creates `AsyncMock(spec=AsyncSession)` but doesn't set up common methods like `commit`, `rollback`, `flush`, `execute`, `get`, etc. Tests using `mock_db` may get unexpected `AttributeError` or silent `AsyncMock` returns. | Low | Consider using a more complete mock or a test database session instead. |
| C4 | Duplicate env var setup: `pytest_load_initial_conftests` hook duplicates the env var settings already at module level. The module-level settings run first, making the hook redundant for most cases. | Low | Remove duplication or document why both are needed. |

---

## Test Coverage Gaps — Critical Business Flows

| # | Business Flow | Risk | Priority |
|---|--------------|------|----------|
| 1 | **Registration approval flow** — admin approves/rejects registration request, temp password generation | High — security-critical, no tests at all | Critical |
| 2 | **Rate limiting** — login rate limiting (per-IP), upload rate limiting | High — security feature completely untested | Critical |
| 3 | **Temp file cleanup** — files deleted from `upload_temp_dir` after processing | Medium — disk space leak if broken | High |
| 4 | **JSONB key normalization** — dims keys sorted recursively before UPSERT | Medium — data integrity issue if broken | High |
| 5 | **403/404 dual-signal** — distinguishing "no access" from "not found" | Medium — information leakage if broken | High |
| 6 | **Processing log status lifecycle** — full state machine validation | Medium — stuck PROCESSING states | Medium |
| 7 | **Weak admin credential detection** — production startup rejection | Medium — security hardening | Medium |
| 8 | **Cookie-based refresh token** — full lifecycle (login → refresh → logout → silent refresh) | Medium — auth flow completeness | Medium |
| 9 | **Upload mode behavior** — overwrite vs. append data handling | Medium — data correctness | Medium |
| 10 | **Admin user atomic UPSERT** — concurrent startup race condition | Low — edge case in production | Low |

---

## Architecture Compliance Notes

### Tests That Correctly Follow Architecture
- **Layer separation**: API tests use `async_client` (HTTP layer), service tests use `mock_db` with mocked repositories, repository tests use `async_db_session` (DB layer). No test crosses layer boundaries improperly.
- **StrEnum usage**: All tests use `UserRole.ADMIN`, `GraphType.BAR`, `ProcessingStatus.SUCCESS` etc. — no raw strings for enum values in assertions.
- **Polars usage**: Data processing tests (`test_data_csv_loader.py`, `test_data_transformations.py`) correctly use Polars, not pandas.
- **Async patterns**: All async tests use `pytest.mark.asyncio` and `await` correctly.
- **No `print()` statements**: No tests check for `print()` output.
- **English only**: All test names, assertions, and comments are in English.

### Anti-Patterns NOT Found (Good)
- No `pandas` imports in any test
- No `unittest.TestCase` usage — all tests use pytest style
- No `print()` output testing
- No raw SQL via f-strings
- No tests checking for deprecated response shapes (all check `TokenWithUser` with `display_name`)
- No tests using sync SQLAlchemy patterns

---

## Recommendations by Priority

### Immediate (Critical)
1. Add rate limiting tests using `strict_redis` fixture
2. Add registration approval flow integration tests
3. Add temp file cleanup verification tests

### Short-term (High)
4. Rewrite `test_register_user_empty_password` to actually verify behavior
5. Add 403/404 dual-signal combined test
6. Add processing log status lifecycle integration test
7. Fix `test_upload_too_large` mock structure

### Medium-term (Medium)
8. Add JSONB key normalization tests
9. Add weak credential detection tests
10. Fix misleading test names in `test_deps.py` and `test_dashboards_api.py`
11. Add processing log date filtering tests
12. Investigate `test_user` fixture commit vs. SAVEPOINT interaction

### Low-priority (Cleanup)
13. Delete `test_load_csv_wrapper` (duplicate, not actually async)
14. Remove duplicate env var setup in conftest.py
15. Improve `mock_db` fixture completeness
