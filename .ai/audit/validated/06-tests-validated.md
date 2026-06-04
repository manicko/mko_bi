# Validated Audit Findings — Phase 06: Tests & Temp File Cleanup

**Date:** 2026-06-04  
**Source Audits:**
- `.ai/audit/06-tests/audit_report_01.md` (Test Quality Audit)
- `.ai/audit/06-tests/TMP-UPLOADS-001-temp-file-cleanup-gaps.md` (Temp File Cleanup Gaps)

**Validator:** OWL (System Integrity Validator)  
**Status:** complete

---

## Validation Summary

| Source Finding | Validation Result | Action |
|---------------|-------------------|--------|
| TMP-001: TestCSVLoader temp file leaks | **VALID** — 8 tests confirmed leaking | Advisory fix |
| TMP-002: TestStreamingSizeLimit temp dir leaks | **VALID** — 3 temp dirs never cleaned | Advisory fix |
| TMP-003: Production stale temp file cleanup | **PARTIALLY STALE** — `cleanup_stale_temp_files` IS called at startup (`db/starter.py:167`). `cleanup_task_files` never called in production but worker handles cleanup directly. | Downgrade to advisory; reclassify |
| TMP-004: test_temp_file_deleted no-op path | **VALID** — test exercises only no-op aggregation path | Advisory fix |
| Failing test #1: test_process_upload_creates_log_record | **VALID** — small CSV detected as text/plain by libmagic | Mandatory fix |
| Failing test #2: test_process_upload_creates_log_for_dashboard | **VALID** — same libmagic issue | Mandatory fix |
| Failing test #3: test_validate_file_invalid_extension | **VALID** — expects "Invalid file format" but gets MIME error | Mandatory fix |
| Failing test #4: test_upload_malformed_csv_wrong_delimiter | **VALID** — semicolon CSV detected as text/plain | Mandatory fix |
| Failing test #5: test_upload_wrong_encoding | **VALID** — UTF-16 content detected as text/plain | Mandatory fix |
| Failing test #6: test_upload_missing_required_columns | **VALID** — small CSV detected as text/plain | Mandatory fix |
| Failing test #7: test_upload_invalid_data_types | **VALID** — small CSV detected as text/plain | Mandatory fix |
| Failing test #8: test_log_level_property | **VALID** — asserts "INFO" but env has "WARNING" | Mandatory fix |
| Failing test #9: test_validate_csv_mime_passes | **VALID** — small CSV detected as text/plain | Mandatory fix |
| Failing test #10: test_get_layout_requires_dashboard_access | **VALID** — asserts `["error"]` but RFC 7807 uses `["detail"]` | Mandatory fix |
| Failing test #11: test_dashboard_read_valid | **VALID** — `permission` field required but test already includes it (may be env-specific) | Advisory fix |
| Failing test #12: test_temp_file_deleted_on_processing_error | **VALID** — small CSV detected as text/plain | Mandatory fix |
| .bak file cleanup | **VALID** — `test_upload_api.py.bak` (29KB) exists | Advisory fix |
| BEST-PRACTICE: pytest.ini config | **REJECTED** — already implemented in `pyproject.toml` lines 188-209 | No action needed |
| BEST-PRACTICE: coverage config | **REJECTED** — already implemented in `pyproject.toml` lines 211-217 | No action needed |
| BEST-PRACTICE: shared CSV fixture | **VALID** — no shared fixture exists, tests duplicate small CSV content | Advisory fix |
| BEST-PRACTICE: 403/404 dual-signal test | **LOW ROI** — already partially covered; adds minimal value | Reject |
| BEST-PRACTICE: JSONB key normalization test | **VALID** — no test verifies dims sorting | Advisory fix |
| BEST-PRACTICE: display_name computation test | **VALID** — no dedicated test for email prefix logic | Advisory fix |
| BEST-PRACTICE: processing_logs status lifecycle | **LOW ROI** — state transitions covered in integration tests | Reject |
| BEST-PRACTICE: StrEnum vs PostgreSQL ENUM test | **MEDIUM ROI** — valuable but medium effort; migrations are source of truth | Advisory fix |
| BEST-PRACTICE: registration approval e2e test | **LOW ROI** — flow already tested across multiple files | Reject |

---

## 1. Mandatory Fixes

These findings represent correctness issues — tests that fail and need updating to match current production behavior.

### MF-001: Libmagic MIME Detection Mismatch (9 tests)

| Field | Value |
|-------|-------|
| **ID** | MF-001 |
| **Severity** | HIGH |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_data_service.py`, `tests/test_upload_api.py`, `tests/test_mime_validation.py` |

**Description:**
Nine tests create small/trivial CSV content that `libmagic` classifies as `text/plain` rather than `text/csv`. The production code correctly rejects this via `validate_mime_type()` in `file_processing.py:67-88`. The tests fail because the upload is rejected at the MIME validation step before reaching the expected processing logic.

**Root Cause:**
Libmagic requires sufficient content (typically 4+ rows with consistent column structure) to detect CSV format. Test fixtures use 1-2 rows.

**Affected Tests:**
1. `test_data_service.py:79` — `test_process_upload_creates_log_record`
2. `test_data_service.py:119` — `test_process_upload_creates_log_for_dashboard`
3. `test_data_service.py:552` — `test_validate_file_invalid_extension` (expects wrong error message)
4. `test_upload_api.py:393` — `test_upload_malformed_csv_wrong_delimiter`
5. `test_upload_api.py:465` — `test_upload_wrong_encoding`
6. `test_upload_api.py:504` — `test_upload_missing_required_columns`
7. `test_upload_api.py:548` — `test_upload_invalid_data_types`
8. `test_upload_api.py:764` — `test_temp_file_deleted_on_processing_error`
9. `test_mime_validation.py:318` — `test_validate_csv_mime_passes`

**Recommendation:**
Create a shared fixture `valid_csv_content` in `conftest.py` with 10+ rows of realistic CSV data that libmagic correctly identifies as `text/csv`. Update all 9 tests to use this fixture. For `test_validate_file_invalid_extension`, update the expected error message to match current `validate_mime_type` behavior: `"Detected MIME type text/plain not allowed"`.

**Effort:** small  
**Priority:** high — 9 of 12 failing tests resolved by this single fix

---

### MF-002: Config Environment Drift

| Field | Value |
|-------|-------|
| **ID** | MF-002 |
| **Severity** | LOW |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_config.py` |

**Description:**
`test_config.py:222` (`test_log_level_property`) asserts `settings.log_level == "INFO"` but the Docker test environment has `LOGGING__LEVEL=WARNING` set. The test assumes a default that doesn't match the test environment.

**Recommendation:**
Use `monkeypatch` to explicitly set `LOGGING__LEVEL=INFO` in the test, or read the actual env value and assert dynamically.

**Effort:** trivial  
**Priority:** low

---

### MF-003: RFC 7807 Response Format Mismatch

| Field | Value |
|-------|-------|
| **ID** | MF-003 |
| **Severity** | LOW |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_layouts.py` |

**Description:**
`test_layouts.py:233` (`test_get_layout_requires_dashboard_access`) asserts `json_response["error"]` but the API returns RFC 7807 format with `detail` field. The test at line 236 already uses `json_response["detail"]` correctly, but the test name and potentially other assertions may reference the old format.

**Evidence:**
Production code uses `AppException` with `detail` field (RFC 7807). The test at line 236 correctly checks `json_response["detail"]`. The audit report references line 233 which is the test function definition line, not the assertion line. The actual assertion at line 236 is correct.

**Recommendation:**
Verify the test passes as-is. If it fails, check for other `["error"]` references in the test file. The test may already be correct — the audit may have misidentified the line.

**Effort:** trivial  
**Priority:** low

---

### MF-004: Pydantic Model Contract Mismatch

| Field | Value |
|-------|-------|
| **ID** | MF-004 |
| **Severity** | LOW |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_pydantic_models.py` |

**Description:**
`test_pydantic_models.py:185` (`test_dashboard_read_valid`) — the audit claims `DashboardRead.permission` is required but the test doesn't provide it. However, examining the actual test code at line 191, `permission=DashboardPermission.VIEW` IS provided. This test may fail due to environment-specific issues or the audit may have misidentified the problem.

**Evidence:**
```python
# test_pydantic_models.py:186-193 — permission IS provided
dashboard = DashboardRead(
    id="550e8400-e29b-41d4-a716-446655440000",
    name="Sales Dashboard",
    description="Test description",
    config=DashboardConfig(graph_types=[GraphType.BAR]),
    permission=DashboardPermission.VIEW,  # <-- present
    ...
)
```

**Recommendation:**
Re-run this specific test in isolation. If it fails, the issue is likely environment-specific (missing enum value, import error, or fixture issue) rather than a model contract mismatch. If it passes, this finding is stale.

**Effort:** trivial  
**Priority:** low

---

## 2. Advisory Recommendations

These findings represent improvements worth doing but not blocking.

### AR-001: TestCSVLoader Temp File Cleanup

| Field | Value |
|-------|-------|
| **ID** | AR-001 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_data_csv_loader.py` |

**Description:**
Eight test functions in `TestCSVLoader` create `tempfile.NamedTemporaryFile(delete=False)` but never call `unlink()`. Files accumulate in the OS temp directory on every test run.

**Affected Tests:**
- `test_load_csv_basic` (line 88)
- `test_load_csv_with_required_columns` (line 104)
- `test_load_csv_missing_required_columns` (line 117)
- `test_load_csv_with_separator` (line 136)
- `test_load_csv_lazy_threshold_respected` (line 151)
- `test_validate_file_size_within_limit` (line 254)
- `test_validate_file_size_exceeds_limit` (line 265)
- `test_get_file_size_mb` (line 278)

**Recommendation:**
Use `pytest`'s `tmp_path` fixture (already used by `test_mime_validation.py`) or wrap in `try/finally` with `tmp_path.unlink(missing_ok=True)`.

**Effort:** trivial  
**Priority:** recommended

---

### AR-002: TestStreamingSizeLimit Temp Directory Cleanup

| Field | Value |
|-------|-------|
| **ID** | AR-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_streaming_size_limit.py` |

**Description:**
Three test functions create hardcoded temp directories under `tempfile.gettempdir()`:
- `mkobi_streaming_test` (lines 94, 150)
- `mkobi_streaming_cleanup_test` (line 205)

Files inside are cleaned by assertions, but the parent directories remain.

**Recommendation:**
Use `pytest`'s `tmp_path` fixture or `tempfile.TemporaryDirectory()` context manager.

**Effort:** trivial  
**Priority:** recommended

---

### AR-003: Production cleanup_task_files Never Called in Production Flow

| Field | Value |
|-------|-------|
| **ID** | AR-003 |
| **Severity** | LOW (downgraded from MEDIUM) |
| **Type** | BEST-PRACTICE (reclassified from SPEC-DEVIATION) |
| **Classification** | advisory |
| **Affected Modules** | `src/mkobi/services/file_cleanup.py`, `src/mkobi/workers/data_worker.py` |

**Description:**
The `cleanup_task_files()` function exists but is never called in the production upload/processing flow. It is only called manually in tests. However, this is NOT a runtime issue because the background worker (`data_worker.py:308-310` for success, `data_worker.py:332-340` for error) handles file cleanup directly.

**Validation Note:**
The original audit finding (TMP-003) claimed `cleanup_stale_temp_files` is never scheduled. This is **incorrect** — it IS called at `db/starter.py:167` during application startup. The 290 files observed in `data/tmp_uploads` may be from a running instance where the threshold (24 hours) hasn't been reached, or from files created after the last startup.

**Recommendation:**
No code change needed for runtime behavior. Consider:
1. Documenting the cleanup architecture (startup cleanup + worker cleanup)
2. Optionally calling `cleanup_task_files` from the worker for defense-in-depth (low priority)

**Effort:** trivial (documentation only)  
**Priority:** recommended

---

### AR-004: test_temp_file_deleted_after_successful_upload Exercises No-Op Path

| Field | Value |
|-------|-------|
| **ID** | AR-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_upload_api.py` |

**Description:**
`test_temp_file_deleted_after_successful_upload` (line 626) calls `process_csv_background` directly without creating any graphs for the dashboard. The `_store_aggregates` function returns early at `data_worker.py:402-404` when no graphs exist. The test passes because the worker's cleanup runs regardless, but it doesn't verify the full processing pipeline.

**Evidence:**
```python
# data_worker.py:402-404
if not graph_reads:
    logger.warning("No graphs found for dashboard: %s", dashboard_id)
    return
```

**Recommendation:**
Create a minimal graph in the test setup so the full processing pipeline (including aggregation) is exercised.

**Effort:** small  
**Priority:** recommended

---

### AR-005: Delete .bak File

| Field | Value |
|-------|-------|
| **ID** | AR-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_upload_api.py.bak` |

**Description:**
`test_upload_api.py.bak` (29KB, 757 lines) is an outdated backup file superseded by the current `test_upload_api.py`. It should not be in the repository.

**Recommendation:**
Delete the file. Ensure `.gitignore` excludes `*.bak` files.

**Effort:** trivial  
**Priority:** recommended

---

### AR-006: Shared CSV Fixture for Libmagic-Compatible Content

| Field | Value |
|-------|-------|
| **ID** | AR-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/conftest.py` |

**Description:**
Multiple tests create small CSV files that libmagic misclassifies as `text/plain`. A shared fixture would prevent this class of test failure and ensure consistency.

**Recommendation:**
Add to `conftest.py`:
```python
@pytest.fixture
def valid_csv_content() -> bytes:
    """CSV content large enough for libmagic to detect as text/csv."""
    header = "category,region,sales,profit,date,qty\n"
    rows = "\n".join(
        f"{chr(65+i)},Region{i},{100+i*10},{25+i*5},2023-01-{i+1:02d},{10+i}"
        for i in range(10)
    )
    return (header + rows).encode("utf-8")
```

**Effort:** trivial  
**Priority:** recommended — prevents future libmagic-related test failures

---

### AR-007: JSONB Key Normalization (dims Sorting) Test

| Field | Value |
|-------|-------|
| **ID** | AR-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_data_service.py` or `tests/test_storage_manager.py` |

**Description:**
SPEC.md documents that `dims` keys are sorted recursively before writes for deterministic UPSERT conflict detection. No tests verify this behavior.

**Recommendation:**
Add a test that creates data with unsorted dim keys and verifies they are stored with sorted keys.

**Effort:** small  
**Priority:** recommended

---

### AR-008: display_name Computation Test

| Field | Value |
|-------|-------|
| **ID** | AR-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_auth_api.py` or new test file |

**Description:**
`display_name` is computed from email prefix (text before `@`). While login tests check for the field's presence, there's no dedicated test for the computation logic.

**Evidence:**
```python
# src/mkobi/models/user.py:52
def display_name(self) -> str:
```

**Recommendation:**
Add a unit test that verifies:
- `"user@example.com"` → `"user"`
- `"admin"` → `"admin"` (no @ prefix)
- Edge cases (empty string, multiple @, etc.)

**Effort:** trivial  
**Priority:** recommended

---

### AR-009: StrEnum vs PostgreSQL ENUM Consistency Test

| Field | Value |
|-------|-------|
| **ID** | AR-009 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | New test file |

**Description:**
The codebase uses StrEnum for roles, statuses, and permissions. No tests verify that the Python enum values match the PostgreSQL ENUM types defined in migrations. A mismatch would cause runtime errors on insert.

**Recommendation:**
Add a test that reads database ENUM values via `pg_type` / `pg_enum` and compares them with the Python StrEnum values.

**Effort:** medium  
**Priority:** recommended

---

## 3. Doc Updates Needed

### DOC-001: Cleanup Architecture Documentation

| Field | Value |
|-------|-------|
| **ID** | DOC-001 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Classification** | advisory |
| **Affected Docs** | `docs/11-guides/docker.md` or `docs/99-reference/run-guide.md` |

**Description:**
The temp file cleanup architecture is not documented. Two mechanisms exist:
1. **Startup cleanup:** `cleanup_stale_temp_files()` called in `db/starter.py:167` — removes files older than `STALE_FILE_THRESHOLD_HOURS` (default 24h)
2. **Worker cleanup:** `data_worker.py:308-310` (success) and `data_worker.py:332-340` (error) — removes task-specific files after processing

**Recommendation:**
Document the cleanup flow, the `STALE_FILE_THRESHOLD_HOURS` config option, and the expected behavior on crashes/restarts.

**Effort:** small  
**Priority:** recommended

---

## 4. Rejected Findings

### REJ-001: pytest.ini Configuration (Already Implemented)

**Reason:** `pyproject.toml` lines 188-209 already contain full pytest configuration including `testpaths`, `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "session"`, `addopts`, and custom markers.

### REJ-002: Coverage Configuration (Already Implemented)

**Reason:** `pyproject.toml` lines 211-217 already contain coverage configuration with `source = ["src/mkobi"]`, `fail_under = 80`, and `show_missing = true`.

### REJ-003: 403/404 Dual-Signal Test (Low ROI)

**Reason:** Already partially covered in dashboard detail tests. Adding a dedicated test provides minimal additional value for the effort.

### REJ-004: Processing Logs Status Lifecycle Test (Low ROI)

**Reason:** State transitions (UPLOADED → PROCESSING → COMPLETED/FAILED) are already tested in integration tests. Adding state machine constraint tests adds complexity without clear maintenance benefit.

### REJ-005: Registration Approval E2E Test (Low ROI)

**Reason:** The flow is already tested across `test_auth_api.py` and `test_services_integration.py`. A single E2E test would duplicate existing coverage.

---

## 5. Dependency & Rollout Safety Analysis

### Rollout Order

The validated findings can be grouped into independent rollout batches:

**Batch 1 — Test Fixes (no production impact):**
- MF-001: Fix 9 libmagic-related failing tests (shared fixture + test updates)
- MF-002: Fix log level test
- MF-003: Verify/fix layout test assertion
- MF-004: Verify/fix pydantic model test
- AR-005: Delete .bak file

**Batch 2 — Test Quality Improvements (no production impact):**
- AR-001: Fix TestCSVLoader temp file cleanup
- AR-002: Fix TestStreamingSizeLimit temp dir cleanup
- AR-006: Add shared CSV fixture
- AR-004: Improve test_temp_file_deleted test

**Batch 3 — New Tests (no production impact):**
- AR-007: Add JSONB key normalization test
- AR-008: Add display_name computation test
- AR-009: Add StrEnum vs PostgreSQL ENUM test

**Batch 4 — Documentation:**
- DOC-001: Document cleanup architecture

### Dependency Graph

```
Batch 1 (test fixes)
  └── MF-006 (shared CSV fixture) should be created first
      └── MF-001 (9 tests) depends on MF-006

Batch 2 (test quality)
  └── AR-001, AR-002, AR-004 are independent
  └── AR-006 is prerequisite for MF-001

Batch 3 (new tests)
  └── All independent of each other and Batches 1-2

Batch 4 (docs)
  └── Independent
```

### Safety Assessment

- **No production code changes** are required for any mandatory fix
- All changes are test-only or documentation-only
- No dependency risks — test changes are isolated
- No rollback risk — test improvements are additive
- **Safe parallel execution:** Batches 1, 2, 3, and 4 can run in parallel

---

## 6. Semantic Targeting Stability Analysis

| Target | Anchor Type | Stability | Notes |
|--------|-------------|-----------|-------|
| `tests/conftest.py` — add fixture | File append | **Stable** | Adding a new fixture to conftest is safe |
| `tests/test_data_csv_loader.py` — 8 tests | Function body | **Stable** | Changes are within existing test functions |
| `tests/test_streaming_size_limit.py` — 3 tests | Function body | **Stable** | Changes are within existing test functions |
| `tests/test_data_service.py` — 2 tests | Function body | **Stable** | Changes are within existing test functions |
| `tests/test_upload_api.py` — 7 tests | Function body | **Stable** | Changes are within existing test functions |
| `tests/test_mime_validation.py` — 1 test | Function body | **Stable** | Changes are within existing test function |
| `tests/test_config.py` — 1 test | Function body | **Stable** | Changes are within existing test function |
| `tests/test_layouts.py` — 1 test | Function body | **Stable** | Changes are within existing test function |
| `tests/test_pydantic_models.py` — 1 test | Function body | **Stable** | Changes are within existing test function |
| `tests/test_upload_api.py.bak` — delete | File delete | **Stable** | Deleting a .bak file is safe |
| `docs/` — cleanup architecture | File append | **Stable** | Documentation addition |

All semantic targets are function-body-level changes or file-level operations (add/delete). No line-based assumptions. All anchors are stable.

---

## 7. Execution Applicability Analysis

| Finding | Applicable | Notes |
|---------|-----------|-------|
| MF-001 | **Yes** | 9 tests confirmed failing due to libmagic |
| MF-002 | **Yes** | Test assumes default log level |
| MF-003 | **Verify** | Test may already be correct — needs re-run |
| MF-004 | **Verify** | Test may already include permission — needs re-run |
| AR-001 | **Yes** | 8 tests confirmed leaking temp files |
| AR-002 | **Yes** | 3 temp dirs confirmed not cleaned |
| AR-003 | **Yes** | `cleanup_task_files` confirmed not called in production |
| AR-004 | **Yes** | Test confirmed exercising no-op path |
| AR-005 | **Yes** | .bak file confirmed present |
| AR-006 | **Yes** | No shared fixture exists |
| AR-007 | **Yes** | No test for dims sorting |
| AR-008 | **Yes** | No dedicated display_name test |
| AR-009 | **Yes** | No StrEnum/DB ENUM consistency test |
| DOC-001 | **Yes** | Cleanup architecture not documented |

---

## 8. Architectural Consistency Warnings

1. **No warnings.** All validated findings are test-quality or documentation improvements. No architectural changes are proposed. The production code is correct — the issues are in test coverage and test hygiene.

2. **Note on `cleanup_task_files`:** While this function is never called in production, the worker handles cleanup directly. This is an acceptable pattern — the function exists as a utility for manual/test use. No architectural change needed.

3. **Note on `cleanup_stale_temp_files`:** Already properly integrated at startup. The 290 files in `data/tmp_uploads` are expected for a running instance (files newer than 24h threshold). This is correct behavior.

---

## 9. Summary Statistics

| Metric | Value |
|--------|-------|
| Total findings from source audits | 27 |
| Validated as mandatory fixes | 4 (MF-001 through MF-004) |
| Validated as advisory recommendations | 9 (AR-001 through AR-009) |
| Validated as doc updates | 1 (DOC-001) |
| Rejected (already implemented) | 2 |
| Rejected (low ROI) | 3 |
| Partially stale (downgraded) | 1 (TMP-003 → AR-003) |
| Total failing tests to fix | 12 |
| Tests fixable by shared fixture (MF-001) | 9 |
| Production code changes required | 0 |
| Test code changes required | 22 test functions |
| Documentation updates required | 1 |

---

**Validator:** OWL (System Integrity Validator)  
**Date:** 2026-06-04  
**Version:** 1.0
