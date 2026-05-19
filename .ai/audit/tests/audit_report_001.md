# Test Quality Audit Report — mkobi BI Dashboard

**Date:** 2026-05-19
**Auditor:** Architecture Audit Agent

---

## 1. Statistics

| Metric | Value |
|--------|-------|
| Total test files | 20 |
| Estimated total test functions | ~180 |
| Tests with `@pytest.mark.asyncio` | ~120 |
| Integration tests (API) | ~90 |
| Unit tests (services) | ~30 |
| Model/validation tests | ~20 |
| Repository tests | ~15 |
| Security tests | ~30 |

### Coverage by Module

| Module | File | Tests Count | Issues Found |
|--------|------|-------------|--------------|
| Auth API | test_auth.py | 6 | 0 critical |
| Auth Service | test_auth_service.py | 33 | 12 critical |
| Data Service | test_data_service.py | 30 | 10 critical |
| Graph Service | test_graph_service.py | 14 | 8 critical |
| Processing Logs | test_processing_logs.py | 11 | 2 critical |
| Repositories | test_repositories.py | 10 | 0 critical |
| Dashboards API | test_dashboards_api.py | 15 | 0 critical |
| Filters API | test_filters.py | 11 | 0 critical |
| Graphs API | test_graphs.py | 2 | 0 critical |
| Layouts API | test_layouts.py | 11 | 0 critical |
| Upload API | test_upload_api.py | 18 | 0 critical |
| Users API | test_users_api.py | 5 | 0 critical |
| Storage Manager | test_storage_manager.py | 5 | 0 critical |
| Security | test_security.py | 30 | 0 critical |
| Pydantic Models | test_pydantic_models.py | 35 | 2 critical |
| Config | test_config.py | 17 | 0 critical |

---

## 2. Problematic Tests Table

| File | Test | Category | Problem | Action | Priority |
|------|------|----------|---------|--------|----------|
| test_auth_service.py | multiple tests | OVERMOCKING | Uses `AsyncMock`, `MagicMock` extensively; tests mock behavior instead of real integrations | Rewrite | High |
| test_auth_service.py | test_login_user_success | ARCHITECTURE_CONFLICT | Mock `get_by_email_with_hash` returns dict-like object, actual code expects UserDB with relationship attributes | Rewrite | Critical |
| test_auth_service.py | test_login_user_empty_password | TAUTOLOGY | Tests mock setup, not real password verification logic | Delete | Medium |
| test_data_service.py | multiple tests | OVERMOCKING | Heavy use of `patch` for `check_dashboard_access`, `enqueue_processing_job`, `find_task_file` | Rewrite | High |
| test_data_service.py | test_process_upload_success | ARCHITECTURE_CONFLICT | Mock setup doesn't match actual `process_upload_with_session` signature; missing real validation | Rewrite | Critical |
| test_data_service.py | test_validate_file_* | TAUTOLOGY | Tests call internal function directly without DB integration | Rewrite | Medium |
| test_graph_service.py | test_create_graph_invalid_type_raises | ARCHITECTURE_CONFLICT | Tests private `_validate_graph_data` method directly; actual flow uses GraphCreate validator | Rewrite | High |
| test_graph_service.py | multiple tests | OVERMOCKING | Mock repository returns MagicMock objects, not validation of real service behavior | Rewrite | High |
| test_pydantic_models.py | test_user_create_invalid_role | ARCHITECTURE_CONFLICT | Uses raw string `"invalid_role"` but Pydantic validates against StrEnum, should use `RoleEnum` | Rewrite | Medium |
| test_pydantic_models.py | test_user_base_config | TAUTOLOGY | Tests `model_config` dict directly, doesn't verify behavior | Delete | Low |
| test_processing_logs.py | test_get_by_dashboard | TAUTOLOGY | Creates logs with `dashboard_id=None`, no real dashboard context | Rewrite | Medium |
| test_upload_api.py | test_upload_malformed_csv_wrong_delimiter | WEAK_COVERAGE | Accepts multiple status codes, doesn't verify actual behavior | Rewrite | Medium |
| test_storage_manager.py | test_clear_graph_data | INCOMPLETE | No database session isolation in fixture | Rewrite | Medium |

---

## 3. Coverage Assessment

### Well-Covered Areas ✅
- **Authentication API** - Login, register-request, token refresh (test_auth.py)
- **Security utilities** - Password hashing, JWT operations (test_security.py)
- **Pydantic models** - User, dashboard, auth models (test_pydantic_models.py)
- **Configuration** - Environment, Docker secrets, YAML loading (test_config.py)
- **Repository CRUD** - Basic operations for all entities (test_repositories.py)
- **Dashboard access control** - Admin bypass, 403/404 cases (test_dashboards_api.py)

### Weakly Covered Areas ⚠️
- **Token refresh endpoint** - No tests in test_auth.py
- **Password change endpoint** - Missing from test_auth.py
- **Admin registration approval flow** - Not tested (temp password generation with `secrets.token_urlsafe(16)`)
- **Rate limiting behavior** - Uses auto-mock `MockRedis`, doesn't test rate limit rejection
- **Data processing pipeline** - Tests are heavily mocked, don't verify actual CSV → Polars → aggregation flow
- **File cleanup** - Temp file deletion on success/failure paths not tested
- **Custom metrics formula parser** - Not covered
- **403/404 dual-signal for dashboard access** - Partially covered, needs negative cases
- **Processing log lifecycle** - Missing `started → uploaded → processing → success/failed` state transitions

### Uncovered Areas ❌
- **Health endpoints** - `/health`, `/health/detailed`, `/` not tested
- **Data retrieval endpoints** - `/data/aggregated` and related endpoints missing
- **Task queue** - Background worker execution not tested
- **Registration approval** - Admin approving/rejecting registration requests
- **CORS origin validation** - Edge cases not covered
- **File encoding detection** - UTF-8 vs other encodings
- **Large file handling** - Memory consumption, chunking not tested
- **Polars integration** - No tests verifying Polars is actually used vs pandas
- **GIN index usage** - JSONB containment queries not tested
- **UPSERT operations** - Aggregated data upsert not tested

---

## 4. Key Findings

### 4.1 Overmocking in Service Tests (Critical)

**File:** `test_auth_service.py`, `test_data_service.py`, `test_graph_service.py`

These tests extensively mock repositories and dependencies, testing the mocks rather than real business logic:

```python
# test_auth_service.py - Problematic pattern
@pytest.fixture
def mock_user_repo(self):
    mock = AsyncMock()
    mock.get_by_email.return_value = None
    mock.get_by_email_with_hash.return_value = None
    return mock

async def test_login_user_success(self, auth_service, mock_user_repo):
    mock_user = MagicMock()
    mock_user.password_hash = hash_password(test_password)
    mock_user_repo.get_by_email_with_hash.return_value = mock_user
    # This tests mock setup, not real authentication flow
```

**Why this is problematic:**
- Mocks bypass the actual password verification logic in `verify_password`
- Mock objects don't have proper SQLAlchemy relationship attributes
- Tests pass even if underlying code is broken
- Rate limiting is patched out globally, losing diagnostic value

### 4.2 Architecture Mismatch in Process Upload

**File:** `test_data_service.py`

The tests don't align with the actual async SQLAlchemy architecture:

```python
# test_data_service.py - Problematic pattern
with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
    with patch("mkobi.services.file_processing.enqueue_job") as mock_enqueue:
        result = await data_service.process_upload(...)
```

**Issues:**
- `process_upload_with_session` is the actual implementation, but tests mock around it
- File validation happens in `file_processing.py`, not tested with real CSV data
- Redis rate limiter is globally patched, losing rate limit testing

### 4.3 Missing Negative Coverage

**File:** Multiple test files

- **Rate limit exceeded:** No tests for 429 responses
- **Soft delete cascade:** Entity deletion doesn't verify related data cleanup
- **Concurrent access:** No race condition tests
- **Empty/edge cases:** Null values, whitespace strings not well covered
- **Boundary conditions:** File size exactly at limit, empty files with headers only

### 4.4 Test Pyramid Imbalance

**Observation:** 90%+ of tests are API/integration tests with heavy mocking. No true unit tests exist.

**Issues:**
- Slow test execution due to database setup
- Tests don't fail when business logic is broken (over-mocking)
- No unit tests for pure functions (formula parser, aggregation logic)
- Limited mutation resistance

---

## 5. Action Plan

### Delete Required (Low Value)

| Test | Reason |
|------|--------|
| test_user_base_config | Tests implementation detail (model_config), not behavior |
| test_login_user_empty_password | Duplicate of existing security test flow |
| test_user_create_empty_password | Pydantic validates required fields, redundant |

### Rewrite Required (Medium Value)

| File | Tests | Priority |
|------|-------|----------|
| test_auth_service.py | All tests | High |
| test_data_service.py | All tests | High |
| test_graph_service.py | All tests | Medium |
| test_processing_logs.py | test_get_by_dashboard | Medium |

**Rewrite Approach:**
1. Remove excessive mocking
2. Use real test database with actual data
3. Test public API endpoints instead of service methods directly
4. Verify DB state changes and side effects
5. Use `pytest.mark.asyncio` consistently

### Improve (Add Coverage)

| Area | Recommended Tests |
|------|-------------------|
| test_auth.py | Add token refresh, password change tests |
| test_health.py | New file for /health endpoints |
| test_data_retrieval.py | New file for /data/aggregated endpoint |
| test_rate_limiting.py | New file with strict_redis fixture |
| test_processing_pipeline.py | Integration test with real CSV → Polars → aggregation |
| test_file_cleanup.py | Temp file deletion on success/failure |

---

## 6. Blocked Refactorings

| Refactoring | Blocked By Test | Action |
|-------------|-----------------|--------|
| AuthService refactoring | test_auth_service.py (33 tests) | Rewrite tests first |
| DataService refactoring | test_data_service.py (30 tests) | Rewrite tests first |
| GraphService refactoring | test_graph_service.py (14 tests) | Rewrite tests first |
| Registration flow changes | test_auth_service.py | Tests need real DB verification |

---

## 7. Recommendations

### Immediate Actions

1. **Rewrite service test files** to test public API instead of internal methods
2. **Remove global Redis mocking** from `conftest.py` auto fixture; use opt-in `strict_redis`
3. **Add negative scenario tests** for rate limiting (429), file size limits (413)
4. **Create test_health.py** for health endpoint coverage

### Long-term Improvements

1. **Add property-based testing** for data transformations
2. **Implement contract tests** between API and services
3. **Add snapshot tests** for Pydantic model serialization
4. **Create integration test suite** with real file processing pipeline

---

## 8. Conclusion

The test suite shows good coverage of API endpoints but suffers from:
- **Over-mocking** in service layer tests (blocking refactoring)
- **Missing negative coverage** for rate limiting and edge cases
- **No true unit tests** - all tests are integration-style
- **Architecture mismatch** between test patterns and production code

**Priority actions:**
1. Rewrite `test_auth_service.py`, `test_data_service.py`, `test_graph_service.py`
2. Remove global Redis mock from `conftest.py`
3. Add tests for currently uncovered health, registration approval, and data retrieval endpoints