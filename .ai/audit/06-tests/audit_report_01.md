# Test Quality Audit Report — mkobi BI Dashboard

**Date:** 2026-06-04  
**Scope:** All 34 test files (673 tests total)  
**Result:** 661 passed, 12 failed  
**Auditor:** OWL (Senior Architecture Auditor)

---

## Executive Summary

The mkobi test suite is **well-structured and largely high-quality**. The codebase follows modern async testing patterns with httpx AsyncClient, uses real database sessions with SAVEPOINT isolation, and covers all major business domains. 661 of 673 tests pass (98.2%).

The 12 failures fall into two categories:
1. **7 tests** fail because they were written for an older MIME validation approach (extension-based) that was replaced by server-side content detection (python-magic). The tests need updating to match the current architecture.
2. **5 tests** fail due to environment/config drift or minor contract mismatches.

No tests need to be deleted. No tests are harmful. The `.bak` file should be removed.

---

## Failing Tests — Detailed Analysis

### Group 1: MIME Validation Contract Mismatch (7 tests)

These tests were written for the old extension-based MIME validation. The production code now uses `python-magic` to detect MIME type from file content. The tests create small CSV files that `libmagic` detects as `text/plain` instead of `text/csv`, or expect error messages that have changed.

| # | File | Test | Root Cause | Type |
|---|------|------|------------|------|
| 1 | test_data_service.py:79 | test_process_upload_creates_log_record | Small CSV detected as text/plain by libmagic | [TEST-UPDATE] |
| 2 | test_data_service.py:119 | test_process_upload_creates_log_for_dashboard | Same — small CSV detected as text/plain | [TEST-UPDATE] |
| 3 | test_data_service.py:552 | test_validate_file_invalid_extension | Expects "Invalid file format" but gets "Detected MIME type text/plain not allowed" | [TEST-UPDATE] |
| 4 | test_upload_api.py:393 | test_upload_malformed_csv_wrong_delimiter | Semicolon CSV detected as text/plain (not enough CSV structure for libmagic) | [TEST-UPDATE] |
| 5 | test_upload_api.py:465 | test_upload_wrong_encoding | UTF-16 content detected as text/plain | [TEST-UPDATE] |
| 6 | test_upload_api.py:504 | test_upload_missing_required_columns | Small CSV detected as text/plain | [TEST-UPDATE] |
| 7 | test_upload_api.py:548 | test_upload_invalid_data_types | Small CSV detected as text/plain | [TEST-UPDATE] |

**Pattern:** All 7 tests create small/trivial CSV content that `libmagic` classifies as `text/plain` rather than `text/csv`. The production code correctly rejects this. The tests need to either:
- Use larger, more realistic CSV content that libmagic correctly identifies as `text/csv`
- Or mock `detect_mime_type_from_content` to return the expected value

**Recommendation:** Update these tests to use CSV files with enough rows/structure for libmagic to detect them as `text/csv` (typically 4+ rows with consistent column structure). This is a trivial fix — increase the CSV content size in test fixtures.

### Group 2: Config/Environment Drift (2 tests)

| # | File | Test | Root Cause | Type |
|---|------|------|------------|------|
| 8 | test_config.py:222 | test_log_level_property | Asserts `log_level == "INFO"` but env has `WARNING` set | [TEST-UPDATE] |
| 9 | test_mime_validation.py:318 | test_validate_csv_mime_passes | Small CSV detected as text/plain (same libmagic issue) | [TEST-UPDATE] |

**Note on #8:** The test assumes default `INFO` log level, but the Docker test environment has `WARNING` set. The test should either explicitly set `LOGGING__LEVEL` in the test or use `monkeypatch`.

### Group 3: Response Format Mismatch (1 test)

| # | File | Test | Root Cause | Type |
|---|------|------|------------|------|
| 10 | test_layouts.py:233 | test_get_layout_requires_dashboard_access | Asserts `response.json()["error"]` but response uses `detail` (RFC 7807) | [TEST-UPDATE] |

**Recommendation:** Change assertion from `["error"]` to `["detail"]` to match RFC 7807 format.

### Group 4: Pydantic Model Contract Mismatch (1 test)

| # | File | Test | Root Cause | Type |
|---|------|------|------------|------|
| 11 | test_pydantic_models.py:185 | test_dashboard_read_valid | `DashboardRead.permission` is now required but test doesn't provide it | [TEST-UPDATE] |

**Recommendation:** Add `permission=DashboardPermission.VIEW` to the test's `DashboardRead` constructor.

### Group 5: Temp File Cleanup Test (1 test)

| # | File | Test | Root Cause | Type |
|---|------|------|------------|------|
| 12 | test_upload_api.py:764 | test_temp_file_deleted_on_processing_error | Small CSV detected as text/plain (same libmagic issue) | [TEST-UPDATE] |

Same root cause as Group 1 — the upload is rejected before processing because libmagic detects the small CSV as `text/plain`.

---

## Full Findings Table

| FilePath | TestName | Type | Problem | Recommendation |
|----------|----------|------|---------|----------------|
| tests/test_data_service.py | test_process_upload_creates_log_record | [TEST-UPDATE] | Small CSV content detected as text/plain by libmagic | Use larger CSV with 4+ rows for libmagic detection |
| tests/test_data_service.py | test_process_upload_creates_log_for_dashboard | [TEST-UPDATE] | Same libmagic text/plain detection issue | Use larger CSV content |
| tests/test_data_service.py | test_validate_file_invalid_extension | [TEST-UPDATE] | Expects "Invalid file format" but gets "Detected MIME type text/plain not allowed" | Update expected error message to match current validate_mime_type behavior |
| tests/test_upload_api.py | test_upload_malformed_csv_wrong_delimiter | [TEST-UPDATE] | Semicolon CSV detected as text/plain by libmagic | Use larger CSV or mock MIME detection |
| tests/test_upload_api.py | test_upload_wrong_encoding | [TEST-UPDATE] | UTF-16 content detected as text/plain | Test already expects 201 but gets 415 — update to expect 415 or use valid UTF-8 |
| tests/test_upload_api.py | test_upload_missing_required_columns | [TEST-UPDATE] | Small CSV detected as text/plain | Use larger CSV content |
| tests/test_upload_api.py | test_upload_invalid_data_types | [TEST-UPDATE] | Small CSV detected as text/plain | Use larger CSV content |
| tests/test_upload_api.py | test_temp_file_deleted_on_processing_error | [TEST-UPDATE] | Upload rejected at MIME check, never reaches processing | Use larger CSV or mock MIME detection |
| tests/test_config.py | test_log_level_property | [TEST-UPDATE] | Asserts "INFO" but env has "WARNING" | Set LOGGING__LEVEL explicitly in test via monkeypatch |
| tests/test_mime_validation.py | test_validate_csv_mime_passes | [TEST-UPDATE] | Small CSV detected as text/plain | Use larger CSV with proper structure |
| tests/test_layouts.py | test_get_layout_requires_dashboard_access | [TEST-UPDATE] | Asserts response.json()["error"] but RFC 7807 uses "detail" | Change to response.json()["detail"] |
| tests/test_pydantic_models.py | test_dashboard_read_valid | [TEST-UPDATE] | DashboardRead.permission is required but not provided | Add permission=DashboardPermission.VIEW |
| tests/test_upload_api.py.bak | (entire file) | [TEST-DELETE] | Backup file with 757 lines of outdated test code | Delete — superseded by current test_upload_api.py |

---

## Positive Findings

### Architecture Compliance
- **All async tests use `async def`** — no sync tests mixed in
- **httpx AsyncClient with ASGITransport** — correct modern FastAPI testing pattern
- **Real database with SAVEPOINT isolation** — proper test isolation without TRUNCATE
- **Dependency overrides** — clean separation of test/production dependencies
- **No pandas imports** — all data tests use polars correctly
- **No `print()` statements** — all tests use proper assertions
- **No `unittest.TestCase`** — all tests use pytest style

### Coverage Quality
- **Auth flow:** Complete coverage of login, logout, refresh, rate limiting, deactivation, cookie-based tokens
- **Dashboard CRUD:** Full role-based access control testing including admin bypass, 403/404 dual-signal
- **Resource-level access control:** Dedicated test file for PUT/DELETE permission checks
- **Token revocation:** Comprehensive blacklist testing with multi-user isolation
- **Upload pipeline:** MIME validation, size limits, streaming, temp file cleanup
- **Service layer:** All 8 services have integration tests with real database
- **Repository layer:** Full CRUD tests for all repositories
- **Pydantic models:** Validation tests for all model types
- **Security:** Password hashing, JWT creation/decode, token validation

### Test Organization
- **conftest.py** properly structured with session-scoped engine and function-scoped sessions
- **MockRedis** with pipeline support for rate limiter testing
- **strict_redis** fixture for tests that need real rate limiting behavior
- **Subdirectories** (api/, core/) for domain-specific tests
- **Clear test class names** that describe the feature under test

---

## Best Practice Recommendations

### [BEST-PEST-PRACTICE] Add pytest.ini / pyproject.toml test configuration

**Current state:** No `pytest.ini` or `[tool.pytest.ini_options]` section found. Tests rely on pyproject.toml defaults.

**Recommendation:** Add explicit pytest configuration:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
addopts = "-v --tb=short"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
]
```

**Effort:** Trivial  
**Priority:** Recommended

### [BEST-PRACTICE] Add test coverage reporting

**Current state:** pytest-cov is installed but no coverage configuration or thresholds are set.

**Recommendation:** Add coverage configuration:
```toml
[tool.coverage.run]
source = ["src/mkobi"]
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

**Effort:** Small  
**Priority:** Recommended

### [BEST-PRACTICE] Standardize MIME validation test approach

**Current state:** Multiple tests create small CSV files that libmagic misclassifies as text/plain. This is a known libmagic behavior — it needs sufficient content to detect CSV structure.

**Recommendation:** Create a shared fixture in conftest.py:
```python
@pytest.fixture
def valid_csv_content() -> bytes:
    """CSV content large enough for libmagic to detect as text/csv."""
    header = "category,region,sales,profit,date,qty\n"
    rows = "\n".join(f"{chr(65+i)},Region{i},{100+i*10},{25+i*5},2023-01-{i+1:02d},{10+i}" for i in range(10))
    return (header + rows).encode("utf-8")
```

**Effort:** Small  
**Priority:** Recommended

### [BEST-PRACTICE] Add negative test for dashboard access — 403 vs 404 dual-signal

**Current state:** The 403/404 dual-signal behavior is tested in dashboard detail tests but not explicitly verified as a security property.

**Recommendation:** Add a dedicated test that verifies:
1. Non-existent dashboard returns 404
2. Existing dashboard without access returns 403
3. The response bodies are different (to distinguish the cases)

This is already partially covered but should be explicit.

**Effort:** Trivial  
**Priority:** Recommended

### [BEST-PRACTICE] Add test for JSONB key normalization (dims sorting)

**Current state:** The SPEC.md documents that `dims` keys are sorted recursively before writes for deterministic UPSERT conflict detection. No tests verify this behavior.

**Recommendation:** Add a test in test_data_service.py or test_storage_manager.py that verifies dims are stored with sorted keys.

**Effort:** Small  
**Priority:** Recommended

### [BEST-PRACTICE] Add test for display_name computation

**Current state:** `display_name` is computed from email prefix (text before `@`). While login tests check for the field's presence, there's no dedicated test for the computation logic.

**Recommendation:** Add a unit test that verifies:
- `"user@example.com"` → `"user"`
- `"admin"` → `"admin"` (no @ prefix)
- Edge cases

**Effort:** Trivial  
**Priority:** Recommended

### [BEST-PRACTICE] Add test for processing_logs status lifecycle

**Current state:** Status transitions (UPLOADED → PROCESSING → COMPLETED/FAILED) are tested in integration tests but the state machine constraints are not explicitly verified.

**Recommendation:** Add a test that verifies invalid transitions are handled (e.g., COMPLETED → PROCESSING should not be allowed, or should be idempotent).

**Effort:** Small  
**Priority:** Recommended

### [BEST-PRACTICE] Add test for StrEnum values matching PostgreSQL ENUM types

**Current state:** The codebase uses StrEnum for roles, statuses, and permissions. No tests verify that the Python enum values match the PostgreSQL ENUM types defined in migrations.

**Recommendation:** Add a test that reads the database ENUM values and compares them with the Python StrEnum values.

**Effort:** Medium  
**Priority:** Recommended

### [BEST-PRACTICE] Add test for registration approval temp password flow end-to-end

**Current state:** The registration approval flow is tested in test_auth_api.py and test_services_integration.py, but the full end-to-end flow (register → approve → retrieve temp password → login → force password change) is split across files.

**Recommendation:** Add a single integration test that covers the complete flow in one test method.

**Effort:** Small  
**Priority:** Recommended

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total test files | 34 (+ 1 .bak) |
| Total tests | 673 |
| Passed | 661 (98.2%) |
| Failed | 12 (1.8%) |
| Tests needing update | 12 |
| Tests to delete | 1 (.bak file) |
| Tests to rewrite | 0 |
| Missing coverage areas | 6 (see recommendations) |

---

## Priority Actions

1. **Fix 12 failing tests** — all are [TEST-UPDATE] with trivial fixes (mostly increase CSV content size for libmagic detection)
2. **Delete test_upload_api.py.bak** — outdated backup file
3. **Add shared CSV fixture** — prevent future libmagic-related test failures
4. **Add pytest.ini configuration** — standardize test runner settings
5. **Add coverage configuration** — enforce minimum coverage thresholds

---

**Author:** OWL (Senior Architecture Auditor)  
**Date:** 2026-06-04  
**Version:** 1.0
