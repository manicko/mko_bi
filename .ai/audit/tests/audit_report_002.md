# Test Quality Audit Report #002

**Date:** 2026-05-16  
**Scope:** Full test suite audit — 17 test files, 1 conftest  
**Production code version:** Current `src/mkobi/` tree  

---

## 1. Statistics

| Metric | Value |
|--------|-------|
| Total test files | 17 |
| Total test classes | ~45 |
| Total test functions | ~160 |
| Critical problems (ARCHITECTURE_CONFLICT) | 6 |
| High severity issues | 8 |
| Medium severity issues | 5 |
| Low severity / style issues | 4 |
| Recommended for deletion | 4 tests |
| Recommended for rewrite | 6 tests |
| Recommended for improvement | 12 tests |

---

## 2. Problematic Tests Table

| # | File | Test(s) | Category | Problem | Action | Priority |
|---|------|---------|----------|---------|--------|----------|
| 1 | `test_auth_service.py` | `test_register_user_empty_password` | ARCHITECTURE_CONFLICT | Tests that empty password is accepted. Production `register_user()` calls `hash_password("")` which succeeds — but this is a business logic gap, not a test gap. However, the test asserts `verify_password("", result.password_hash)` on a `UserRead` model that has no `password_hash` field (it's excluded). The assertion `hasattr(result, 'password_hash') else True` always short-circuits to `True`, making the test tautological. | Rewrite to either test real behavior or remove | Medium |
| 2 | `test_auth_service.py` | `test_register_user_success`, `test_register_user_admin_role`, `test_register_user_duplicate_email`, `test_register_user_invalid_email`, `test_register_user_invalid_role` | Overmocking | All repo responses are fully mocked. The `register_user` method in production requires a `db: AsyncSession` parameter (no default in the non-recursive path). The test calls `auth_service.register_user(email=..., password=..., role=...)` without `db`, which triggers the `db is None` branch that creates a new session via `get_session()`. But the mock `user_repo.create` is never actually called with a real db — the test only validates mock call patterns, not real behavior. | Rewrite to test with real session or clearly document as mock-only unit test | Medium |
| 3 | `test_auth_service.py` | `test_login_user_success`, `test_login_user_wrong_password`, `test_login_user_not_found`, `test_login_user_empty_password` | Overmocking | Same pattern — `login_user` is called without `db`, triggering the `get_session()` path. Mocks replace all repo behavior. Tests verify mock interactions, not real authentication flow. The `login_user` production code calls `self.user_repo.get_by_email_with_hash(email=email, db=db)` but the mock's `return_value` is set at fixture time and shared across tests. | Rewrite or document scope | Medium |
| 4 | `test_auth_service.py` | `test_authenticate_user_success` | Overmocking | Calls both `get_by_email_with_hash` and `get_by_email` on the mock. In production, when `db is None`, `login_user` creates its own session, then `authenticate_user` creates *another* session for `get_by_email`. The test's single mock serves both calls, which masks the double-session issue. | Document or rewrite | Low |
| 5 | `test_data_service.py` | `test_process_upload_success`, `test_process_upload_with_user`, `test_process_upload_csv_gz` | ARCHITECTURE_CONFLICT | Production `process_upload()` has signature `(file_content, dashboard_id, user_id=None, filename=None, content_type=None, mode=UploadMode.OVERWRITE, db=None)`. The test calls it without `db`, which triggers the `get_session()` path. But the mock `log_repo.create_log` is called with `db=session` (the new session), not the test's session. The test patches `enqueue_job` and `check_dashboard_access` but the actual file I/O (`aiofiles.open`) and temp directory creation happen in a real filesystem. This is an integration test disguised as a unit test. | Rewrite as integration test with real DB, or properly mock all I/O | High |
| 6 | `test_data_service.py` | `test_process_upload_file_too_large` | ARCHITECTURE_CONFLICT | Creates `large_content = b"x" * (101 * 1024 * 1024)` — a 101 MB bytes object in memory. This allocates ~101 MB RAM per test run. The production code checks `len(file_content) > self._max_file_size` where `_max_file_size = config.max_file_size` (default 100 MB). But the test doesn't mock `get_config()`, so it uses the real config. If config changes, the test breaks. | Rewrite with smaller mock or use config override | Medium |
| 7 | `test_data_service.py` | `test_get_aggregated_data_success` | Overmocking | The mock record has `dashboard_id` as a UUID, but the test asserts `result[0]["dashboard_id"] == dashboard_id`. Production `_get_aggregated_data_with_session` creates `ProcessingResultData` objects with `dashboard_id=record.dashboard_id`. The test verifies mock data round-tripping, not real DB behavior. | Acceptable as unit test if documented | Low |
| 8 | `test_graph_service.py` | `test_create_graph_invalid_type_raises` | Wrong Abstraction Level | Tests `_validate_graph_data` directly with `MagicMock(name="Test", type="invalid_type", dashboard_id=uuid4())`. The `_validate_graph_data` method expects `data.type` to be a string for `GraphType(data.type)`. But the production `create()` method passes `GraphCreate` objects. Testing the private validation method with raw MagicMock bypasses the Pydantic validation layer. If `GraphCreate` model changes its `type` field, this test won't catch it. | Rewrite to use `GraphCreate` with invalid type | Medium |
| 9 | `test_graph_service.py` | `test_service_implements_IGraphService` | Tautological | `assert isinstance(graph_service, IGraphService)` — this only checks that the mock-based `GraphService` instance is an instance of the ABC. It doesn't verify any behavioral contract. If methods are renamed or signatures change, this test still passes. | Delete — adds no value | Low |
| 10 | `test_security.py` | `test_token_with_wrong_signature` | ARCHITECTURE_CONFLICT | Patches `get_config` to return wrong secret, then calls `decode_token`. But `decode_token` calls `get_config()` internally, and the patch replaces the return value. However, the mock's `JWT_SECRET_KEY` is accessed as an attribute (`mock_get_config.return_value.JWT_SECRET_KEY`), while production code uses `get_config().jwt.secret_key` (nested attribute). The patch sets `JWT_SECRET_KEY` as a top-level attribute, which doesn't match the production config structure. This test may pass for the wrong reason or fail intermittently. | Rewrite to properly mock nested config | High |
| 11 | `test_security.py` | `test_same_password_same_hash` | Tautological | Comment says "Same passwords should produce different hashes (due to salt)" but the test name says "same_hash". The assertion `hash1 != hash2` verifies bcrypt salt randomness, not application logic. This is testing the bcrypt library, not our code. | Delete — tests bcrypt, not our code | Low |
| 12 | `test_pydantic_models.py` | `test_user_read_valid`, `test_user_db_valid` | Tautological | Tests that Pydantic models accept valid data and produce objects with expected attributes. These tests verify Pydantic v2's `model_validate` and field assignment — framework behavior, not business logic. | Acceptable as model contract tests | Low |
| 13 | `test_pydantic_models.py` | `test_dashboard_config_with_charts` | ARCHITECTURE_CONFLICT | `DashboardConfig` model has fields: `graph_types`, `filters`, `aggregations`, `charts`. The test creates `DashboardConfig(graph_types=[...], charts=[...])` but the `charts` field is not in the production `DashboardConfig` model (it has `graph_types`, `filters`, `aggregations` only — `charts` is not a field). This test would fail at runtime. | Delete or fix to match production model | High |
| 14 | `test_pydantic_models.py` | `test_processing_config_valid` | ARCHITECTURE_CONFLICT | Imports `AggregationConfig`, `FilterConfig`, `AggregationFunctionEnum`, `FilterOperatorEnum` from `mkobi.models.transformation_configs` and `mkobi.models.enums`. The `AggregationFunctionEnum` and `FilterOperatorEnum` exist in `enums.py`, but `FilterConfig` expects `operator: FilterOperatorEnum` and `AggregationConfig` expects `function: AggregationFunctionEnum`. The test passes string values like `">="` and `"sum"` which would fail Pydantic validation since the enums expect `FilterOperatorEnum.GTE` and `AggregationFunctionEnum.SUM`. This test likely fails at runtime. | Fix to use proper enum values | High |
| 15 | `test_pydantic_models.py` | `test_aggregated_data_valid` | ARCHITECTURE_CONFLICT | `AggregatedData.chart_type` expects `GraphType` enum, but the test passes `GraphType.BAR` which is correct. However, `AggregatedData.data` expects `list[AggregatedRecordModel]` where `AggregatedRecordModel` is a Pydantic model from `types.py`. The test passes raw dicts `{"dims": {...}, "metrics": {...}}` — Pydantic may or may not coerce these depending on the model config. Needs verification. | Verify against production model | Medium |
| 16 | `test_config.py` | `test_load_email_blocked_domains_from_yaml` (×3 duplicate patterns) | Duplication | `test_email_blocked_domains` in `TestEmailSettings`, `test_load_email_blocked_domains_from_yaml` in `TestSettingsFromYaml`, and `test_email_blocked_domains` in `TestEmailSettings` all test the same `settings.email.blocked_domains` behavior. The `TestSettingsFromYaml` and `TestEmailSettings` classes test identical functionality at different abstraction levels. | Consolidate | Low |
| 17 | `test_config.py` | `test_cors_origins_from_env_json`, `test_cors_origins_from_env_multiple`, `test_cors_origins_from_env_comma_separated`, `test_cors_origins_from_env_single` | Duplication | Four tests that all set `CORS_ORIGINS` env var with slightly different JSON values and assert the parsed result. The test names mention "comma_separated" but the values are JSON arrays. These test the same parsing logic with minor variations. | Consolidate into parametrized test | Low |
| 18 | `test_dashboards_api.py` | `TestCreateDashboard.test_create_dashboard_forbidden`, `TestUpdateDashboard.test_update_dashboard_forbidden`, `TestDeleteDashboard.test_delete_dashboard_forbidden` | Duplication / Copy-Paste | Three tests with identical structure: create viewer user, login as viewer, attempt admin action, assert 403. The only difference is the endpoint and payload. This is copy-paste testing. | Consolidate into parametrized test | Medium |
| 19 | `test_filters.py` | `test_create_filter_admin_required`, `test_update_filter_admin_required`, `test_delete_filter_admin_required` | Duplication / Copy-Paste | Same pattern — create viewer, login, attempt admin action, assert 403. Identical structure across all three. | Consolidate | Medium |
| 20 | `test_layouts.py` | `test_create_layout_admin_required`, `test_update_layout_admin_required`, `test_delete_layout_admin_required` | Duplication / Copy-Paste | Same pattern again. | Consolidate | Medium |
| 21 | `test_upload_api.py` | `test_upload_malformed_csv_wrong_delimiter`, `test_upload_wrong_encoding`, `test_upload_invalid_data_types` | Fragile | These tests accept multiple status codes (`assert response.status_code in [201, 400, 422]`), making them pass regardless of actual behavior. They don't verify that invalid data is properly rejected. | Rewrite with deterministic assertions | High |
| 22 | `test_upload_api.py` | `test_upload_empty_file` | Fragile | Asserts `response.status_code == 422` but the production `_validate_file` raises `ValueError("File content is empty")` which would result in a 400 or 500 depending on exception handling, not necessarily 422. Needs verification. | Verify against production error handling | High |
| 23 | `test_storage_manager.py` | `test_clear_graph_data_compat`, `test_clear_dashboard_data_compat` | Tautological | These test the compatibility wrapper methods `clear_graph_data_compat` and `clear_dashboard_data_compat` which are classmethods that create a `StorageManager` instance and call the regular method. The tests verify the compat methods work with an empty table (return 0). They don't test actual deletion. | Improve to test with data, or delete | Medium |
| 24 | `test_processing_logs.py` | `TestProcessingLogRepository.test_get_by_dashboard` | ARCHITECTURE_CONFLICT | Creates logs with `dashboard_id=None` and then calls `repo.get_by_dashboard(None, db=async_db_session)`. The production `get_by_dashboard` method filters by `dashboard_id`, so passing `None` would return all logs with `dashboard_id IS NULL`. This works but tests a degenerate case. The test name says "by dashboard" but uses `None`. | Rewrite with actual dashboard_id | Medium |

---

## 3. Coverage Assessment

### Well-Covered Areas

| Area | Coverage Level | Notes |
|------|---------------|-------|
| Auth service (unit) | Good | `test_auth_service.py` covers login, register, token operations — but heavily mocked |
| Config/Settings | Good | `test_config.py` covers env, YAML, Docker secrets, priority |
| Security (hash/token) | Good | `test_security.py` covers bcrypt and JWT thoroughly |
| Dashboard API (CRUD) | Good | `test_dashboards_api.py` covers all endpoints with real DB |
| Filter API (CRUD) | Good | `test_filters.py` covers all endpoints |
| Layout API (CRUD) | Good | `test_layouts.py` covers all endpoints |
| Graph service (unit) | Good | `test_graph_service.py` covers CRUD with mocks |
| Data service (unit) | Good | `test_data_service.py` covers upload, processing, status — but heavily mocked |
| Pydantic models | Good | `test_pydantic_models.py` covers most model validation |
| Processing logs | Good | `test_processing_logs.py` covers repo and service |
| Upload API | Good | `test_upload_api.py` covers many edge cases |
| User API | Good | `test_users_api.py` covers profile and deletion |
| Repositories | Good | `test_repositories.py` covers CRUD for all repos |

### Under-Covered / Missing Areas

| Area | Coverage | Risk |
|------|----------|------|
| **Data Processing Pipeline** (`data/loaders/`, `data/processing/`) | **No tests at all** | **Critical** — CSVLoader, DataValidator, transformations, DataPipeline are completely untested. This is the core business logic. |
| **Dashboard Service** (`services/dashboard_service.py`) | **No tests** | **High** — grant_access, revoke_access, get_user_dashboards, get_all_dashboards untested |
| **User Service** (`services/user_service.py`) | **No tests** | **High** — update_user_role, delete_user, admin deletion protection untested |
| **Filter Service** (`services/filter_service.py`) | **No tests** | **Medium** — filter type/name/config validation untested |
| **Layout Service** (`services/layout_service.py`) | **No tests** | **Medium** — layout CRUD with partial updates untested |
| **Processing Config Service** (`services/processing_config_service.py`) | **No tests** | **Medium** — settings validation untested |
| **API: Data endpoints** (`routes/data.py`) | **No tests** | **High** — GET `/data/aggregated` with filters untested |
| **API: Admin endpoints** (`routes/admin.py`) | **No tests** | **High** — user role changes, registration request approval/rejection untested |
| **API: Processing config endpoints** (`routes/processing_configs.py`) | **No tests** | **Medium** |
| **API: Processing log endpoints** (`routes/processing_logs.py`) | **No tests** | **Medium** |
| **API: Graph endpoints** (`routes/graphs.py`) | **Partial** | `test_graphs.py` only tests via `/dashboards/{id}/graphs`, not `/graphs/` routes |
| **Permissions** (`core/permissions.py`) | **No tests** | **High** — check_role, check_dashboard_access, role hierarchy untested |
| **Rate Limiting** (`core/security.py` RateLimiter) | **No tests** | **Medium** — only the mock bypass is tested |
| **Task Queue** (`core/task_queue.py`) | **No tests** | **Medium** — enqueue_job, process_next untested |
| **Workers** (`workers/`) | **No tests** | **High** — process_csv_background untested |
| **Storage Manager: save/upsert** (`data/storage/manager.py`) | **Partial** | Only `clear_graph_data` and `clear_dashboard_data` tested. `save_aggregates`, `upsert_aggregate`, `get_aggregates`, `delete_by_graph`, `delete_by_dashboard` with real data are untested. |
| **Temp file cleanup** | **No tests** | **Medium** — cleanup_task_files, cleanup_stale_temp_files untested |
| **Registration request flow** (end-to-end) | **No tests** | **Medium** — register-request → approve → login flow untested |
| **Change password** | **No tests** | **Medium** — AuthService.change_password untested |
| **Token refresh endpoint** | **No tests** | **Low** — POST `/auth/refresh` untested |

### Test Pyramid Assessment

```
        /  e2e  \          ← None (0%)
       / integration \     ← Thin layer (test_auth.py, test_dashboards_api.py, etc.)
      /   unit (mock)  \   ← Heavy layer (test_auth_service.py, test_data_service.py, etc.)
     /    unit (real)    \ ← Thin layer (test_security.py, test_pydantic_models.py)
    /_____________________\
```

**Problem:** The test suite is heavily skewed toward mocked unit tests. Integration tests with real DB exist for API endpoints but are incomplete. There are zero end-to-end tests and zero data processing pipeline tests.

---

## 4. Key Findings (with Evidence)

### Finding 1: Data Processing Pipeline Completely Untested

**Severity:** Critical  
**Evidence:** The `src/mkobi/data/` directory contains `loaders/loader.py` (CSVLoader), `loaders/validator.py` (DataValidator), `processing/transformations.py` (apply_transformations, calculate_aggregations), and `processing/registry.py` (DataPipeline). None of these have any test coverage. This is the core business value of the application — loading CSV files, validating, transforming, and aggregating data.

**Impact:** A bug in CSV parsing, data validation, or aggregation logic would go undetected. The `DataPipeline` class uses `tenacity` for retry logic — this is completely untested.

### Finding 2: Heavy Overmocking in Service Tests Masks Real Behavior

**Severity:** High  
**Evidence:** `test_auth_service.py` and `test_data_service.py` mock all repository responses. For example, in `test_auth_service.py:39-57`:

```python
async def test_register_user_success(self, auth_service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.create.return_value = MagicMock(
        id=uuid4(), email="test@example.com", role="viewer",
        password_hash=hash_password("TestPass123!"),
    )
    result = await auth_service.register_user(
        email="test@example.com", password="TestPass123!", role="viewer",
    )
    assert isinstance(result, UserRead)
    assert result.email == "test@example.com"
    mock_user_repo.create.assert_called_once()
```

The test calls `register_user` without `db`, which in production triggers `get_session()` context manager. The mock `user_repo.create` is never called with a real session. The test only verifies that the mock was called, not that the actual registration flow works.

**Impact:** These tests give false confidence. They pass even if the real database schema changes, if repository method signatures change, or if the session management breaks.

### Finding 3: Fragile Tests with Non-Deterministic Assertions

**Severity:** High  
**Evidence:** In `test_upload_api.py:340-346`:

```python
async def test_upload_malformed_csv_wrong_delimiter(...):
    ...
    # Polars may parse as single column - accept success or rejection
    assert response.status_code in [201, 400, 422]
```

This test passes whether the server accepts or rejects the file. It has zero diagnostic value. Similarly, `test_upload_wrong_encoding` and `test_upload_invalid_data_types` use the same pattern.

**Impact:** These tests will not catch regressions. If the server starts accepting invalid files, these tests still pass.

### Finding 4: Pydantic Model Tests Reference Non-Existent Fields

**Severity:** High  
**Evidence:** In `test_pydantic_models.py:196-209`:

```python
def test_dashboard_config_with_charts(self):
    config = DashboardConfig(
        graph_types=[GraphType.BAR, GraphType.LINE, GraphType.PIE],
        charts=[{"type": GraphType.BAR, "x": "category", "y": "revenue", "title": "Revenue by Category"}],
    )
    assert len(config.charts) == 1
```

The production `DashboardConfig` model (`models/dashboard.py`) has fields: `graph_types`, `filters`, `aggregations`. There is **no `charts` field**. This test would raise `ValidationError` at runtime.

**Impact:** This test is broken and would fail if executed. It indicates the test was written against a different version of the model.

### Finding 5: Extensive Copy-Paste in API Authorization Tests

**Severity:** Medium  
**Evidence:** The pattern "create viewer user → login → attempt admin action → assert 403" is repeated identically across `test_dashboards_api.py` (3×), `test_filters.py` (3×), `test_layouts.py` (3×), and `test_graphs.py` (1×). Each repetition creates ~25 lines of boilerplate.

**Impact:** Maintenance burden. If the user creation or login flow changes, 10+ test files need updates. High risk of inconsistencies.

### Finding 6: `conftest.py` Auto-Mock Bypasses Rate Limiting

**Severity:** Medium  
**Evidence:** The `_auto_mock_redis` fixture in `conftest.py:102-144` is `autouse=True` and patches `AuthService.__init__` to replace `check_rate_limit` with `always_true`. This means **no test can accidentally hit rate limiting**, but it also means **rate limiting is never tested**. The `strict_redis` fixture exists but is never used in any test.

**Impact:** Rate limiting is a security feature (SPEC.md section 6) that has zero test coverage in the integration test suite.

### Finding 7: `test_users_api.py` Re-implements Login Flow

**Severity:** Low  
**Evidence:** `test_users_api.py:TestGetProfile` manually logs in via `async_client.post("/auth/login", ...)` and extracts the token. This duplicates the `authenticated_client` fixture from `conftest.py`. The test also doesn't use the `test_user` fixture for the login step — it re-logins the same user.

**Impact:** Inconsistent test patterns make the suite harder to maintain.

---

## 5. Plan of Actions

### Delete Required (4 tests)

| File | Test | Reason |
|------|------|--------|
| `test_graph_service.py` | `test_service_implements_IGraphService` | Tautological — only checks ABC registration |
| `test_security.py` | `test_same_password_same_hash` | Tests bcrypt library, not application code |
| `test_pydantic_models.py` | `test_dashboard_config_with_charts` | References non-existent `charts` field |
| `test_pydantic_models.py` | `test_processing_config_valid` | Uses string values instead of enum values |

### Rewrite Required (6 tests/groups)

| File | Test | Rewrite To |
|------|------|-----------|
| `test_upload_api.py` | `test_upload_malformed_csv_wrong_delimiter`, `test_upload_wrong_encoding`, `test_upload_invalid_data_types` | Deterministic assertions — pick the correct expected status code |
| `test_upload_api.py` | `test_upload_empty_file` | Verify actual error code from production |
| `test_security.py` | `test_token_with_wrong_signature` | Properly mock nested config (`jwt.secret_key`) |
| `test_pydantic_models.py` | `test_processing_config_valid` | Use `FilterOperatorEnum.GTE` and `AggregationFunctionEnum.SUM` |
| `test_processing_logs.py` | `TestProcessingLogRepository.test_get_by_dashboard` | Use actual `dashboard_id` instead of `None` |
| `test_auth_service.py` | All `register_user` and `login_user` tests | Either use real `async_db_session` or clearly document as mock-only |

### Improve Required (12 areas)

| Area | Action | Priority |
|------|--------|----------|
| Data processing pipeline | Add tests for CSVLoader, DataValidator, transformations, DataPipeline | Critical |
| Dashboard service | Add unit tests for grant_access, revoke_access, get_user_dashboards | High |
| User service | Add unit tests for update_user_role, delete_user, admin deletion protection | High |
| Permissions | Add unit tests for check_role, check_dashboard_access | High |
| Data API endpoints | Add integration tests for GET `/data/aggregated` with filters | High |
| Admin API endpoints | Add integration tests for user management, registration approval | High |
| Storage Manager | Add tests for save_aggregates, upsert_aggregate with real data | Medium |
| Rate limiting | Add integration test using `strict_redis` fixture | Medium |
| Copy-paste tests | Consolidate authorization tests into parametrized tests | Medium |
| Filter/Layout services | Add unit tests for validation logic | Medium |
| Processing config service | Add unit tests for settings validation | Medium |
| Temp file cleanup | Add tests for cleanup_task_files, cleanup_stale_temp_files | Medium |

---

## 6. Blocked Refactorings

The following production code refactorings are blocked by test issues:

| Refactoring | Blocked By |
|-------------|-----------|
| Changing `DashboardConfig` model fields | `test_pydantic_models.py` has tests for non-existent `charts` field — must delete first |
| Changing `AuthService.register_user` signature | `test_auth_service.py` tests call without `db` parameter, relying on the `get_session()` fallback path |
| Changing `DataService.process_upload` signature | `test_data_service.py` tests call without `db` parameter and mock all I/O |
| Changing error codes in upload endpoint | `test_upload_api.py` tests accept multiple status codes, masking the actual behavior |

---

## 7. Recommendations for Test Culture

1. **Test behavior, not mocks.** The service tests (`test_auth_service.py`, `test_data_service.py`, `test_graph_service.py`) should use real database sessions via `async_db_session` fixture instead of mocking repositories. This catches real integration issues.

2. **One assertion per behavior.** Tests like `test_upload_malformed_csv_wrong_delimiter` that accept `[201, 400, 422]` should be split into specific scenarios with deterministic expected outcomes.

3. **Parametrize authorization tests.** The 10+ identical "create viewer → attempt admin → assert 403" patterns should be a single parametrized test.

4. **Test the data pipeline.** The most critical business logic (CSV loading → validation → transformation → aggregation) has zero tests. This should be the highest priority.

5. **Use `strict_redis` fixture for rate limiting tests.** The auto-mock bypasses rate limiting entirely. At least one test should verify rate limiting works.

6. **Keep model tests in sync with production.** The `test_pydantic_models.py` file has tests for fields that don't exist (`charts` in `DashboardConfig`). Model tests should be auto-generated or validated against the actual model definitions.

7. **Avoid testing framework internals.** Tests like `test_same_password_same_hash` (testing bcrypt salt randomness) and `test_user_read_valid` (testing Pydantic field assignment) add no value.

---

*Audit conducted by: OWL (auditor)*  
*Methodology: Full codebase scan, production-to-test cross-reference, anti-pattern classification*
