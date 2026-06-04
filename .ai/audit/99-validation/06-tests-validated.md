# Validated Audit Findings — Phase 06: Tests & Temp File Cleanup

**Date:** 2026-06-04  
**Source Audits:**
- `.ai/audit/06-tests/audit_report_01.md` (Test Quality Audit)
- `.ai/audit/06-tests/TMP-UPLOADS-001-temp-file-cleanup-gaps.md` (Temp File Cleanup Gaps)

**Validator:** OWL (System Integrity Validator)  
**Status:** complete  
**Criticality:** HIGH — 12 failing tests indicate broken test suite; temp file leak is a production disk exhaustion risk

---

## Validation Summary

| Source Finding | Validation Result | Action |
|---------------|-------------------|--------|
| TMP-001: TestCSVLoader temp file leaks | **VALID** — 8 tests confirmed leaking | Mandatory fix |
| TMP-002: TestStreamingSizeLimit temp dir leaks | **VALID** — 3 temp dirs never cleaned | Mandatory fix |
| TMP-003: Production stale temp file cleanup gap | **VALID** — `cleanup_stale_temp_files` runs at startup (24h threshold), but `cleanup_stale_processing_logs` does NOT delete files from disk. Worker crash leaves orphaned files until next restart. | Mandatory fix |
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
| Failing test #10: test_get_layout_requires_dashboard_access | **VALID** — audit reports failure; code at line 236 uses `["detail"]` correctly — may be env-specific | Mandatory fix (verify and fix) |
| Failing test #11: test_dashboard_read_valid | **VALID** — audit reports failure; code looks correct — may be env-specific import/model issue | Mandatory fix (verify and fix) |
| Failing test #12: test_temp_file_deleted_on_processing_error | **VALID** — small CSV detected as text/plain | Mandatory fix |
| .bak file cleanup | **VALID** — `test_upload_api.py.bak` (29KB) exists | Mandatory fix |
| BEST-PRACTICE: pytest.ini config | **REJECTED** — already implemented in `pyproject.toml` lines 188-209 | No action needed |
| BEST-PRACTICE: coverage config | **REJECTED** — already implemented in `pyproject.toml` lines 211-217 | No action needed |
| BEST-PRACTICE: shared CSV fixture | **VALID** — no shared fixture exists | Advisory fix |
| BEST-PRACTICE: 403/404 dual-signal test | **ACCEPTED** — security property should be explicitly verified | Advisory fix |
| BEST-PRACTICE: JSONB key normalization test | **VALID** — no test verifies dims sorting | Advisory fix |
| BEST-PRACTICE: display_name computation test | **VALID** — no dedicated test for email prefix logic | Advisory fix |
| BEST-PRACTICE: processing_logs status lifecycle | **ACCEPTED** — state machine constraints should be explicitly tested | Advisory fix |
| BEST-PRACTICE: StrEnum vs PostgreSQL ENUM test | **VALID** — no consistency test between Python enums and DB enums | Advisory fix |
| BEST-PRACTICE: registration approval e2e test | **ACCEPTED** — critical auth flow should have dedicated E2E test | Advisory fix |

---

## 1. Mandatory Fixes

These findings represent correctness issues — failing tests, production resource leaks, and security gaps.

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
**Priority:** critical — 9 of 12 failing tests resolved by this single fix

---

### MF-002: Config Environment Drift

| Field | Value |
|-------|-------|
| **ID** | MF-002 |
| **Severity** | MEDIUM |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_config.py` |

**Description:**
`test_config.py:222` (`test_log_level_property`) asserts `settings.log_level == "INFO"` but the Docker test environment has `LOGGING__LEVEL=WARNING` set. The test assumes a default that doesn't match the test environment.

**Recommendation:**
Use `monkeypatch` to explicitly set `LOGGING__LEVEL=INFO` in the test, or read the actual env value and assert dynamically.

**Effort:** trivial  
**Priority:** high

---

### MF-003: RFC 7807 Response Format Mismatch

| Field | Value |
|-------|-------|
| **ID** | MF-003 |
| **Severity** | MEDIUM |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_layouts.py` |

**Description:**
`test_layouts.py:233` (`test_get_layout_requires_dashboard_access`) — audit reports this test fails. The test code at line 236 uses `json_response["detail"]` which is correct for RFC 7807 format. However, the test may fail due to environment-specific issues (token generation, dashboard access setup, or response body differences).

**Evidence:**
Production code uses `AppException` with `detail` field (RFC 7807). The test at line 236 correctly checks `json_response["detail"]`. The failure may be in the test setup (token creation, access control) rather than the assertion itself.

**Recommendation:**
Re-run this test in isolation. If it fails, debug the full response body and compare with expected format. Check if the 403 response includes the expected `detail` field with "access" keyword.

**Effort:** trivial  
**Priority:** high

---

### MF-004: Pydantic Model Contract Mismatch

| Field | Value |
|-------|-------|
| **ID** | MF-004 |
| **Severity** | MEDIUM |
| **Type** | TEST-UPDATE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_pydantic_models.py` |

**Description:**
`test_pydantic_models.py:185` (`test_dashboard_read_valid`) — audit reports this test fails. The test code includes `permission=DashboardPermission.VIEW` at line 191. The failure may be environment-specific: missing enum import, `DashboardConfig` validation error, or `GraphType.BAR` not being recognized.

**Evidence:**
```python
# test_pydantic_models.py:186-193
dashboard = DashboardRead(
    id="550e8400-e29b-41d4-a716-446655440000",
    name="Sales Dashboard",
    description="Test description",
    config=DashboardConfig(graph_types=[GraphType.BAR]),
    permission=DashboardPermission.VIEW,
    created_at="2026-04-24T16:02:46+03:00",
    updated_at="2026-04-24T16:02:46+03:00",
)
```

**Recommendation:**
Re-run this test in isolation with full error output. Check for import errors, enum value mismatches, or Pydantic validation errors. The test code appears correct — the issue is likely in the test environment.

**Effort:** trivial  
**Priority:** high

---

### MF-005: TestCSVLoader Temp File Leaks (8 tests)

| Field | Value |
|-------|-------|
| **ID** | MF-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_data_csv_loader.py` |

**Description:**
Eight test functions in `TestCSVLoader` create `tempfile.NamedTemporaryFile(delete=False)` but never call `unlink()`. Files accumulate in the OS temp directory on every test run. This is a resource leak that pollutes the test environment and can cause disk pressure in CI.

**Affected Tests:**
- `test_load_csv_basic` (line 88)
- `test_load_csv_with_required_columns` (line 104)
- `test_load_csv_missing_required_columns` (line 117)
- `test_load_csv_with_separator` (line 136)
- `test_load_csv_lazy_threshold_respected` (line 151)
- `test_validate_file_size_within_limit` (line 254)
- `test_validate_file_size_exceeds_limit` (line 265)
- `test_get_file_size_mb` (line 278)

**Evidence:**
```python
# tests/test_data_csv_loader.py:88-99
def test_load_csv_basic(self):
    csv_content = b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    loader = CSVLoader()
    df = loader.load_csv(tmp_path)
    # ... assertions but NO tmp_path.unlink() ...
```

**Recommendation:**
Use `pytest`'s `tmp_path` fixture (already used by `test_mime_validation.py`) or wrap in `try/finally` with `tmp_path.unlink(missing_ok=True)`.

**Effort:** trivial  
**Priority:** high

---

### MF-006: TestStreamingSizeLimit Temp Directory Leaks (3 tests)

| Field | Value |
|-------|-------|
| **ID** | MF-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_streaming_size_limit.py` |

**Description:**
Three test functions create hardcoded temp directories under `tempfile.gettempdir()`:
- `mkobi_streaming_test` (lines 94, 150)
- `mkobi_streaming_cleanup_test` (line 205)

Files inside are cleaned by assertions, but the parent directories remain. These are orphaned directories that accumulate on every test run.

**Evidence:**
```python
# tests/test_streaming_size_limit.py:94
temp_dir = Path(tempfile.gettempdir()) / "mkobi_streaming_test"
# ... used but never deleted ...
```

**Recommendation:**
Use `pytest`'s `tmp_path` fixture or `tempfile.TemporaryDirectory()` context manager.

**Effort:** trivial  
**Priority:** high

---

### MF-007: Production Temp File Cleanup Gap — Worker Crash Leaves Orphaned Files

| Field | Value |
|-------|-------|
| **ID** | MF-007 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/services/file_cleanup.py`, `src/mkobi/db/starter.py` |

**Description:**
AGENTS.md states: "Temporary files after processing **must be deleted**." The production upload flow has a gap where files survive in `data/tmp_uploads` indefinitely under certain failure scenarios.

**Current cleanup mechanisms:**
1. **Startup cleanup:** `cleanup_stale_temp_files()` called in `db/starter.py:167` — removes files older than `STALE_FILE_THRESHOLD_HOURS` (default 24h). This only runs on application restart.
2. **Worker success cleanup:** `data_worker.py:308-310` — deletes file after successful processing.
3. **Worker error cleanup:** `data_worker.py:332-340` — deletes file on processing error.
4. **Stale processing log cleanup:** `cleanup_stale_processing_logs()` — marks stale DB entries as FAILED but does **NOT** delete files from disk.

**Gap — worker crash between `replace()` and processing completion:**
If the RQ worker process crashes after `file_path.replace(final_file_path)` (line 236 of `file_processing.py`) but before `_process_csv_file_async` completes, the file remains in `data/tmp_uploads` forever — until the next application startup triggers `cleanup_stale_temp_files()` (up to 24h later).

**Gap — stale processing cleanup does not delete files:**
`cleanup_stale_processing_logs()` (line 95-153 of `data_worker.py`) only updates the database status to FAILED. It does not call `cleanup_task_files()` to remove the orphaned file from disk. This means files from timed-out processing jobs persist indefinitely.

**Evidence:**
- 290+ files currently in `data/tmp_uploads` (confirmed on disk)
- `cleanup_stale_processing_logs()` at line 95-153: only executes SQL UPDATE, no file deletion
- `cleanup_task_files()` at `file_cleanup.py:16-36`: exists but never called in production flow
- No periodic task that combines stale log cleanup with file deletion

**Recommendation:**
1. **Add file cleanup to `cleanup_stale_processing_logs()`** — when marking a stale entry as FAILED, also call `cleanup_task_files(task_id)` to delete the associated file from disk.
2. **Add `cleanup_task_files` call to the worker's exception handler** — as defense-in-depth, call `cleanup_task_files` in addition to the direct `file_path.unlink()` at line 332-340.
3. **Reduce `STALE_FILE_THRESHOLD_HOURS`** for production deployments where disk space is critical (configurable via env).

**Effort:** small  
**Priority:** critical — disk exhaustion risk in production

---

### MF-008: Delete .bak File

| Field | Value |
|-------|-------|
| **ID** | MF-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | mandatory |
| **Affected Modules** | `tests/test_upload_api.py.bak` |

**Description:**
`test_upload_api.py.bak` (29KB, 757 lines) is an outdated backup file superseded by the current `test_upload_api.py`. It should not be in the repository and may confuse developers or be accidentally executed.

**Recommendation:**
Delete the file. Add `*.bak` to `.gitignore` if not already present.

**Effort:** trivial  
**Priority:** high

---

## 2. Advisory Recommendations

These findings represent improvements worth doing but not blocking.

### AR-001: test_temp_file_deleted_after_successful_upload Exercises No-Op Path

| Field | Value |
|-------|-------|
| **ID** | AR-001 |
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

### AR-002: Shared CSV Fixture for Libmagic-Compatible Content

| Field | Value |
|-------|-------|
| **ID** | AR-002 |
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

### AR-003: 403/404 Dual-Signal Security Test

| Field | Value |
|-------|-------|
| **ID** | AR-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_dashboards.py` or new test file |

**Description:**
The 403/404 dual-signal behavior (non-existent dashboard returns 404, existing dashboard without access returns 403) is a security property that prevents dashboard enumeration. While partially covered in existing tests, it should be explicitly verified as a security invariant.

**Recommendation:**
Add a dedicated test that verifies:
1. Non-existent dashboard returns 404
2. Existing dashboard without access returns 403
3. The response bodies are different (to distinguish the cases)
4. Admin users bypass the 403 check

**Effort:** trivial  
**Priority:** recommended — security property

---

### AR-004: JSONB Key Normalization (dims Sorting) Test

| Field | Value |
|-------|-------|
| **ID** | AR-004 |
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

### AR-005: display_name Computation Test

| Field | Value |
|-------|-------|
| **ID** | AR-005 |
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

### AR-006: Processing Logs Status Lifecycle Test

| Field | Value |
|-------|-------|
| **ID** | AR-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | `tests/test_data_service.py` or new test file |

**Description:**
Status transitions (UPLOADED → PROCESSING → COMPLETED/FAILED) are tested in integration tests but the state machine constraints are not explicitly verified. Invalid transitions (e.g., COMPLETED → PROCESSING) should be tested to ensure idempotency and data integrity.

**Recommendation:**
Add a test that verifies:
- Valid transitions succeed
- Invalid transitions are handled gracefully (idempotent or rejected)
- Status is always updated atomically with file operations

**Effort:** small  
**Priority:** recommended

---

### AR-007: StrEnum vs PostgreSQL ENUM Consistency Test

| Field | Value |
|-------|-------|
| **ID** | AR-007 |
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

### AR-008: Registration Approval E2E Test

| Field | Value |
|-------|-------|
| **ID** | AR-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Affected Modules** | New test file |

**Description:**
The registration approval flow (register → approve → retrieve temp password → login → force password change) is tested across multiple files but not as a single end-to-end test. This is a critical auth flow that should have dedicated E2E coverage.

**Recommendation:**
Add a single integration test that covers the complete flow in one test method.

**Effort:** small  
**Priority:** recommended — critical auth flow

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
The temp file cleanup architecture is not documented. Multiple mechanisms exist:
1. **Startup cleanup:** `cleanup_stale_temp_files()` called in `db/starter.py:167` — removes files older than `STALE_FILE_THRESHOLD_HOURS` (default 24h)
2. **Worker success cleanup:** `data_worker.py:308-310` — removes task-specific files after processing
3. **Worker error cleanup:** `data_worker.py:332-340` — removes task-specific files on processing error
4. **Stale processing log cleanup:** `data_worker.py:95-153` — marks stale DB entries as FAILED (but does NOT delete files — see MF-007)

**Recommendation:**
Document the cleanup flow, the `STALE_FILE_THRESHOLD_HOURS` config option, the `STALE_PROCESSING_TIMEOUT_MINUTES` config option, and the expected behavior on crashes/restarts. Document the gap identified in MF-007 and the planned fix.

**Effort:** small  
**Priority:** recommended

---

## 4. Rejected Findings

### REJ-001: pytest.ini Configuration (Already Implemented)

**Reason:** `pyproject.toml` lines 188-209 already contain full pytest configuration including `testpaths`, `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "session"`, `addopts`, and custom markers.

### REJ-002: Coverage Configuration (Already Implemented)

**Reason:** `pyproject.toml` lines 211-217 already contain coverage configuration with `source = ["src/mkobi"]`, `fail_under = 80`, and `show_missing = true`.

---

## 5. Dependency & Rollout Safety Analysis

### Rollout Order

The validated findings must be addressed in this order:

**Batch 1 — Critical Production Fix (MF-007):**
- Add file cleanup to `cleanup_stale_processing_logs()` — this is the only production code change
- Must be deployed before other changes to prevent further disk accumulation

**Batch 2 — Failing Tests (MF-001 through MF-004, MF-008):**
- MF-002: Create shared CSV fixture in `conftest.py`
- MF-001: Update 9 tests to use the shared fixture
- MF-003: Verify and fix layout test
- MF-004: Verify and fix pydantic model test
- MF-008: Delete .bak file

**Batch 3 — Test Resource Leaks (MF-005, MF-006):**
- MF-005: Fix 8 TestCSVLoader tests to use `tmp_path`
- MF-006: Fix 3 TestStreamingSizeLimit tests to use `tmp_path`

**Batch 4 — Test Improvements (AR-001 through AR-008):**
- All independent, can be done in any order

**Batch 5 — Documentation (DOC-001):**
- Independent

### Dependency Graph

```
Batch 1 (production fix)
  └── MF-007: Add file cleanup to stale processing log handler

Batch 2 (failing tests)
  └── AR-002 (shared CSV fixture) must be created first
      └── MF-001 (9 tests) depends on AR-002
  └── MF-003, MF-004, MF-008 are independent

Batch 3 (resource leaks)
  └── MF-005, MF-006 are independent of each other and Batch 2

Batch 4 (improvements)
  └── All independent

Batch 5 (docs)
  └── Independent
```

### Safety Assessment

- **One production code change** required: MF-007 (adding file cleanup to stale processing log handler)
- This change is low-risk: it adds a `cleanup_task_files()` call in an existing cleanup function
- All other changes are test-only or documentation-only
- **Rollback plan for MF-007:** Revert the single function change; no data migration needed
- **Safe parallel execution:** Batches 2, 3, 4, and 5 can run in parallel after Batch 1 is deployed

---

## 6. Semantic Targeting Stability Analysis

| Target | Anchor Type | Stability | Notes |
|--------|-------------|-----------|-------|
| `src/mkobi/workers/data_worker.py:cleanup_stale_processing_logs` — add file cleanup | Function body | **Stable** | Adding cleanup call within existing function |
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
| MF-003 | **Yes** | Audit reports failure; needs verification |
| MF-004 | **Yes** | Audit reports failure; needs verification |
| MF-005 | **Yes** | 8 tests confirmed leaking temp files |
| MF-006 | **Yes** | 3 temp dirs confirmed not cleaned |
| MF-007 | **Yes** | `cleanup_stale_processing_logs` confirmed NOT deleting files; 290+ files on disk |
| MF-008 | **Yes** | .bak file confirmed present |
| AR-001 | **Yes** | Test confirmed exercising no-op path |
| AR-002 | **Yes** | No shared fixture exists |
| AR-003 | **Yes** | Security property not explicitly tested |
| AR-004 | **Yes** | No test for dims sorting |
| AR-005 | **Yes** | No dedicated display_name test |
| AR-006 | **Yes** | State machine constraints not explicitly tested |
| AR-007 | **Yes** | No StrEnum/DB ENUM consistency test |
| AR-008 | **Yes** | No dedicated registration approval E2E test |
| DOC-001 | **Yes** | Cleanup architecture not documented |

---

## 8. Architectural Consistency Warnings

1. **Production code change required (MF-007):** The `cleanup_stale_processing_logs()` function needs to be extended to also delete files from disk. This is a spec deviation from AGENTS.md rule "Temporary files after processing must be deleted." The change is small and low-risk but must be tested.

2. **290+ orphaned files on disk:** The current `data/tmp_uploads` directory contains 290+ files. After deploying MF-007, the next startup cleanup will remove files older than 24h. Consider manually cleaning the directory before deployment.

3. **Worker crash resilience:** The current architecture relies on the worker process surviving from `replace()` through processing completion. If the worker crashes, the file persists until the next startup. MF-007 partially addresses this by cleaning up files when stale processing logs are detected, but there's still a window (up to `STALE_PROCESSING_TIMEOUT_MINUTES` = 30min) where files accumulate.

4. **No warnings on test architecture.** All test changes are isolated and follow existing patterns.

---

## 9. Summary Statistics

| Metric | Value |
|--------|-------|
| Total findings from source audits | 27 |
| Validated as mandatory fixes | 8 (MF-001 through MF-008) |
| Validated as advisory recommendations | 8 (AR-001 through AR-008) |
| Validated as doc updates | 1 (DOC-001) |
| Rejected (already implemented) | 2 |
| Rejected (low ROI) | 0 |
| Total failing tests to fix | 12 |
| Tests fixable by shared fixture (MF-001) | 9 |
| Production code changes required | 1 (MF-007) |
| Test code changes required | 22 test functions |
| Documentation updates required | 1 |
| Orphaned files on disk | 290+ |

---

**Validator:** OWL (System Integrity Validator)  
**Date:** 2026-06-04  
**Version:** 2.0 (revised for criticality)
