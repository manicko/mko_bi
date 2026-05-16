# Test Quality Audit Report #1

**Date:** 2026-05-16  
**Auditor:** Kilo Architecture Audit  
**Scope:** Complete test suite analysis for mkobi BI Dashboard

---

## 1. Statistics

| Metric | Value |
|--------|-------|
| Total test files | 14 |
| Total test lines | ~4,200 |
| Test types | Unit (heavily mocked), Integration (API with DB) |
| Critical problems | 23 |
| Recommended for deletion | 7 tests |
| Rewrite required | 16 tests |

### Test Distribution by File

| File | Lines | Test Type | Issues |
|------|-------|-----------|--------|
| test_auth_service.py | 379 | Unit (mocked) | High |
| test_graph_service.py | 241 | Unit (mocked) | High |
| test_data_service.py | 528 | Unit (mocked) | High |
| test_repositories.py | 255 | Integration | Medium |
| test_upload_api.py | 494 | Integration | Low |
| test_auth.py | 123 | Integration | Low |
| test_users_api.py | 142 | Integration | Medium |
| test_graphs.py | 157 | Integration | Medium |
| test_dashboards_api.py | 314 | Integration | Medium |
| test_filters.py | 205 | Integration | Medium |
| test_layouts.py | 189 | Integration | Medium |
| test_security.py | 309 | Unit (pure) | Low |
| test_pydantic_models.py | 371 | Unit (pure) | Low |
| test_processing_logs.py | 230 | Integration | Low |
| test_config.py | 294 | Unit (pure) | Low |
| test_storage_manager.py | 179 | Integration | Medium |

---

## 2. Problematic Tests Table

| File | Test | Category | Problem | Action | Priority |
|------|------|----------|---------|--------|----------|
| test_auth_service.py | All tests | Overmocking | Uses `MagicMock` for user objects, mocks all repository methods, tests implementation details not behavior | **Rewrite** | Critical |
| test_auth_service.py | `test_register_user_empty_password` | Tautological | Tests empty password handling but production uses bcrypt hashing which allows empty passwords | **Delete** | Medium |
| test_auth_service.py | `_make_graph_obj` helper | Wrong abstraction | Private method `_validate_graph_data` tested directly - tests internal implementation | **Delete** | High |
| test_graph_service.py | All tests | Overmocking | 100% mocked repositories, MagicMock objects, testing mock assertions not real behavior | **Rewrite** | Critical |
| test_graph_service.py | `test_service_implements_IGraphService` | Wrong abstraction | Tests Python interface compliance, not business logic | **Delete** | High |
| test_data_service.py | All tests | Overmocking | Heavy use of `patch()` for dependencies, mocks entire processing pipeline | **Rewrite** | Critical |
| test_data_service.py | `test_process_upload_empty_password` | Tautological | Tests mocked password with non-existent `password_hash` attribute on UserRead | **Delete** | High |
| test_storage_manager.py | All tests | Wrong abstraction | Tests repository method delegation (clear_graph_data_compat) | **Delete** | High |
| test_users_api.py | `test_admin_cannot_delete_self` | Fragile | Creates state dependencies, relies on test order, uses shared DB state | **Rewrite** | Medium |
| test_config.py | Multiple CORS tests | Tautological | Tests JSON parsing mechanics rather than business rules | **Delete** | Low |
| test_pydantic_models.py | All model tests | Low value | Tests Pydantic validation that is self-evident from model definitions | **Delete** | Medium |
| test_processing_logs.py | `test_create_started_log` | Architecture mismatch | Tests with `dashboard_id=None` which is not a valid production scenario | **Rewrite** | Medium |

---

## 3. Coverage Assessment

### Well-Covered Areas
- ✅ Authentication API endpoints (login, register, get_me)
- ✅ Dashboard CRUD operations with access control
- ✅ Upload validation (MIME, extension, size limits)
- ✅ Security module (password hashing, JWT)
- ✅ Configuration loading (YAML, env, Docker secrets)

### Gaps in Coverage

| Area | Gap | Risk Level |
|------|-----|------------|
| **Token Refresh** | Only tested in mocked `test_auth_service.py` | High |
| **Rate Limiting** | Only mocked via `conftest.py` | High |
| **Data Processing Pipeline** | No integration tests with real Polars processing | Critical |
| **Permission Boundary Cases** | Missing tests for editor/viewer role restrictions | Medium |
| **Concurrent Access** | No race condition tests for DB operations | Medium |
| **Error Recovery** | No tests for failed processing rollback | Medium |
| **Aggregation Logic** | No tests verifying actual data aggregation | High |
| **External API Errors** | No tests for third-party service failures | Low |
| **Large File Processing** | Tests use actual 101MB file creation (slow) | Medium |

---

## 4. Key Findings

### 4.1 Architecture/Contract Mismatch (Critical)

**Finding:** `test_auth_service.py` and `test_graph_service.py` test private methods and internal implementation details rather than public contracts.

```python
# test_graph_service.py line 82-84 - PROBLEMATIC
with pytest.raises(ValueError, match="Invalid graph type"):
    await graph_service._validate_graph_data(
        MagicMock(name="Test", type="invalid_type", dashboard_id=uuid4())
    )
```

**Impact:** These tests will break on refactoring without behavioral changes, blocking development velocity.

**Reference:** Production code at `src/mkobi/services/auth_service.py:57-76` shows `register_user` is the public interface, not `_validate_role`.

### 4.2 Overmocking Problem (Critical)

**Finding:** Most service tests use nearly 100% mocks, making tests verify mock behavior instead of real system behavior.

```python
# test_auth_service.py lines 17-25 - PROBLEMATIC
@pytest.fixture
def mock_user_repo(self):
    mock = AsyncMock()
    mock.get_by_email.return_value = None
    mock.get_by_email_with_hash.return_value = None
    mock.get.return_value = None
    mock.get_all.return_value = []
    return mock
```

**Impact:** Tests pass even when real code is broken because the mock returns expected values. No actual database interaction occurs.

### 4.3 Tautological Tests (Medium)

**Finding:** `test_auth_service.py:107-123` tests empty password handling that doesn't represent real-world behavior.

```python
# test_auth_service.py lines 107-123 - PROBLEMATIC
async def test_register_user_empty_password(...):
    mock_user_repo.create.return_value = MagicMock(
        id=uuid4(),
        email="empty@example.com",
        role="viewer",
        password_hash=hash_password(""),  # Empty password IS hashed in production
    )
    result = await auth_service.register_user(...)
    assert isinstance(result, UserRead)
    assert verify_password("", result.password_hash) if hasattr(result, 'password_hash') else True
```

**Impact:** UserRead model doesn't have password_hash attribute. Test passes due to `hasattr` check, not actual verification.

### 4.4 Wrong Abstraction Level (High)

**Finding:** `test_storage_manager.py` tests repository delegation methods rather than actual data storage behavior.

```python
# test_storage_manager.py lines 159-167 - PROBLEMATIC
async def test_clear_graph_data_compat(async_db_session: AsyncSession):
    graph_id = uuid4()
    deleted = await StorageManager.clear_graph_data_compat(
        graph_id=graph_id, db=async_db_session
    )
    assert deleted == 0
```

**Impact:** Tests a static method that wraps instance method - adds no value, creates maintenance burden.

### 4.5 Missing Integration for Core Functionality (Critical Gap)

**Finding:** No integration tests for actual data processing with Polars - the core business value of the system.

```python
# test_data_service.py - MISSING
# No tests verify that:
# - CSV files are correctly parsed into aggregated data
# - Metrics are correctly calculated
# - Dimension grouping works
# - Large files are processed without memory issues
```

**Impact:** Core data processing pipeline has zero real test coverage. Bugs in aggregation logic would go undetected.

---

## 5. Action Plan

### Delete Required (7 tests)

| Test | Reason |
|------|--------|
| `test_auth_service.py:test_register_user_empty_password` | Tests non-representative edge case with flawed assertions |
| `test_graph_service.py:test_service_implements_IGraphService` | Tests Python machinery, not business logic |
| `test_graph_service.py:test_create_graph_invalid_type_raises` | Tests private `_validate_graph_data` method |
| `test_storage_manager.py: test_clear_graph_data_compat` | Tests delegation method, no behavior value |
| `test_storage_manager.py: test_clear_dashboard_data_compat` | Tests delegation method, no behavior value |
| `test_pydantic_models.py:all model validation tests` | Tests Pydantic framework behavior, not business rules |
| `test_config.py:CORS JSON parsing tests` | Tests JSON parsing, not configuration business rules |

### Rewrite Required (16 tests)

| Test | Issue | Approach |
|------|-------|----------|
| `test_auth_service.py:all tests` | Overmocking | Use real repositories with test DB |
| `test_graph_service.py:all tests` | Overmocking | Use real repositories with test DB |
| `test_data_service.py:all tests` | Overmocking + patching | Use real async test with actual file processing |
| `test_users_api.py:test_admin_cannot_delete_self` | Fragile state | Use test-isolated setup |
| `test_processing_logs.py:test_create_started_log` | Invalid scenario | Test with real dashboard |

### Improve Required (Coverage)

| Area | Tests to Add |
|------|--------------|
| Token refresh with real DB | Integration test for `/auth/refresh` |
| Rate limiting behavior | Test actual rate limit enforcement |
| Data processing pipeline | End-to-end test with CSV → aggregation |
| Editor permission boundaries | Tests for VIEW vs EDIT vs ADMIN permissions |
| Concurrent upload handling | Race condition tests |
| Failed processing recovery | Test rollback after processing error |

---

## 6. Blocked Refactorings

The following production code improvements are blocked by test issues:

| Production Change | Blocked By | Impact |
|-------------------|------------|--------|
| Refactor AuthService to use dependency injection container | `test_auth_service.py` mock-heavy patterns | Cannot verify refactored service without test rewrite |
| Optimize data processing pipeline | No real integration tests | Risk of breaking core functionality |
| Add new graph types | Overmocked graph service tests | Tests will break without business reason |
| Change token payload structure | Mocked auth tests don't verify real tokens | Deployment risk |

---

## Recommendations

1. **Adopt Test Pyramid:** Current suite has too many unit tests with mocks. Add integration tests for critical paths.

2. **Use Real Dependencies:** Service tests should use real repositories with the test database (`async_db_session`) rather than mocks.

3. **Test Business Outcomes:** Focus on what the system does, not how it does it. For data service: verify aggregated data is correct, not that methods were called.

4. **Remove Boilerplate:** Pydantic model tests can be removed - the framework validates correctly. Configuration JSON parsing tests add no value.

5. **Add E2E Tests:** A few end-to-end tests covering upload → process → aggregate → display would validate core business flow.