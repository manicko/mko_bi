# Implementation Audit Report — Stage 3 Batch (TASK_001 through TASK_015)

**Date:** 2026-05-30
**Auditor:** OWL — Validation Agent
**Scope:** 15 completed implementation tasks from `.ai/tasks/done/`
**Report ID:** `implementation_audit_001`

---

## Executive Summary

Overall implementation quality for this batch is **below acceptable standards**. Of 15 tasks, only 7 are correctly implemented to specification, 2 have partial implementation with unresolved ambiguities, and 6 have **critical non-implementations** where the claimed code changes were either not applied or incompletely applied despite being marked as "done".

**Risk Level:** HIGH  
**Production Readiness:** NOT READY  
**Architecture Compliance:** PARTIAL (some cross-layer concerns introduced)  
**Rollout Readiness:** BLOCKED — critical fixes required before deployment  
**Verdict:** REQUIRES FIXES

---

## Verified Correct Implementations

| ID | Task | Status |
|-----|------|--------|
| TASK_004 | INT-006 — Add type and name fields to AggregatedDataResponse | CORRECT |
| TASK_005 | INT-007 — Fix AccessGrant field naming (permission_level → permission) | CORRECT |
| TASK_008 | BUG-004a — LogViewer date format fix | CORRECT |
| TASK_009 | BUG-004c — Add dashboard_name to ProcessingLog response | CORRECT |
| TASK_013 | FE-002 — Fix stale closure in UploadModal polling | CORRECT |
| TASK_014 | FE-004 — ARIA attributes for upload components | CORRECT |
| TASK_015 | Integration alignment verification | CORRECT |

### TASK_004 Detail — AggregatedDataResponse

**Evidence:** `src/mkobi/models/data.py` correctly defines:
- `GraphDataResponse` (lines 420-446) with `graph_id: str`, `type: GraphType`, `name: str`, and `data` fields
- `AggregatedDataResponse` (lines 449-473) wrapping `graphs: list[GraphDataResponse]`

Frontend types `api.types.ts` (lines 143-149) have `GraphDataWithConfig` matching the backend shape.

### TASK_005 Detail — AccessGrant Field Naming

**Evidence:** 
- Backend `src/mkobi/models/access.py` `AccessGrant` model uses `permission: str = "view"` (line 30)
- `src/mkobi/api/routes/dashboards_access.py` line 86: `access_grant.permission`
- Frontend `api.types.ts` `DashboardAccess` and `GrantAccessRequest` use `permission: DashboardPermission`
- No `permission_level` references remain in frontend or backend code

### TASK_008 Detail — LogViewer Date Format

**Evidence:**
- `frontend/src/features/admin/ui/LogViewer.tsx` line 104: `date.toISOString()` (full ISO datetime)
- `frontend/src/features/admin/ui/LogViewer.tsx` line 111: same for date_to
- Lines 48-51: `useQuery` correctly destructures `error`, `isError`
- Lines 67-68: null-safe `started_at` check with ternary
- Lines 122-126: error Alert rendering when `isError`

### TASK_009 Detail — ProcessingLog dashboard_name

**Evidence:**
- `src/mkobi/models/processing_logs.py` `ProcessingLogRead` has `dashboard_name: str | None = None` (line 77)
- `src/mkobi/db/repositories/processing_log_repo.py`: All query methods load dashboard relationship via `selectinload` and populate `log_read.dashboard_name = log.dashboard.name if log.dashboard else None`
- SQLAlchemy model `db/models/processing_logs.py` has `dashboard` relationship with `selectinload` (line 76)
- Frontend `api.types.ts` `ProcessingLog` has optional `dashboard_name?: string | null`

### TASK_013 Detail — Stale Closure Fix

**Evidence:**
- `frontend/src/features/upload/ui/UploadModal.tsx` lines 46-49: `useRef` for `onUploadCompleteRef` with syncing `useEffect`
- Line 57: Status update effect uses `statusData?.status` directly, no `queueMicrotask`
- Line 73: `onUploadCompleteRef.current?.()` — uses ref, no stale closure

### TASK_014 Detail — ARIA Attributes

**Evidence:**
- `frontend/src/features/upload/ui/FileDropzone.tsx` Paper element: `role="button"`, `aria-label="Drop files here or click to upload"`, `tabIndex={0}`, `aria-describedby="dropzone-instructions"`
- Line 108: `aria-live="polite"` span for drag state announcements
- Lines 125-128: `IconButton` with `aria-label={`Remove file ${file.name}`}`
- `UploadModal.tsx` line 187: `aria-label="Upload mode selection"` on ToggleButtonGroup

---

## Findings and Problems

### CRITICAL — C001: TASK_001 — Password Validation NOT Implemented

**Severity:** CRITICAL
**Type:** SPEC-DEVIATION (Missing Required Implementation)
**Task:** TASK_001_sec001_password_validation
**Affected Files:**
- `src/mkobi/models/auth.py` — `RegisterRequest` class
- `src/mkobi/services/auth_service.py` — `register_user` method

**Problem:** The task required adding `@field_validator('password')` to `RegisterRequest` calling `validate_password()` from `mkobi.utils.validators`, and adding explicit `validate_password()` call in `register_user()` as defense-in-depth. **Neither change was made.**

**Evidence:**
- `src/mkobi/models/auth.py` lines 95-111: `RegisterRequest` class has no `@field_validator` decorator on any field, no import of `validate_password` from `mkobi.utils.validators`
- `src/mkobi/services/auth_service.py` line 144: `hash_password(password)` called without any prior password validation. The `_validate_role()` and `_validate_email_format()` checks are present, but `_validate_password()` or equivalent is completely absent.
- `src/mkobi/utils/validators.py` lines 145-180: `validate_password()` function exists and works correctly, but is never called during registration.

**Architectural Impact:** Security gap. Weak passwords are accepted at the API trust boundary. The SEC-001 audit finding remains unresolved.

**Execution Risk:** HIGH — any user can register with a 1-character password.

**Rollback Risk:** None (only additive).

**Required Correction:** Add `@field_validator('password')` to `RegisterRequest` that calls `validate_password()`. Also add explicit `validate_password()` call before `hash_password()` in `register_user()` as defense-in-depth per the task specification.

---

### CRITICAL — C002: TASK_002 — MIME Validation Bypass NOT Fixed

**Severity:** CRITICAL
**Type:** SPEC-DEVIATION (Missing Required Implementation)
**Task:** TASK_002_sec003_mime_validation
**Affected File:** `src/mkobi/services/file_processing.py`

**Problem:** The task required changing `validate_mime_type()` to raise `ValueError` when `content_type` is None instead of silently returning. **The fix was NOT applied.**

**Evidence:**
- `src/mkobi/services/file_processing.py` lines 31-33:
  ```python
  if content_type is None:
      logger.warning("MIME-type not specified, skipping check")
      return
  ```
  This is exactly the vulnerable code that was supposed to be changed. It still logs a warning and returns, allowing MIME validation bypass when Content-Type is missing.

**Architectural Impact:** Security gap. The SEC-003 audit finding remains unresolved. An attacker can upload arbitrary file types by omitting the Content-Type header.

**Execution Risk:** HIGH — file type validation is a core security control.

**Required Correction:** Change lines 31-33 to raise `ValueError("Content-Type header is required")` as specified in the task.

---

### CRITICAL — C003: TASK_003 — Circular Import NOT Broken

**Severity:** CRITICAL
**Type:** SPEC-DEVIATION (Missing Required Implementation)
**Task:** TASK_003_fe001_circular_import
**Affected Files:**
- `frontend/src/shared/api/axiosInstance.ts`
- `frontend/src/features/auth/api/authApi.ts`

**Problem:** The task required breaking the circular dependency between `axiosInstance.ts` and `authApi.ts` using a callback registration pattern (`registerRefreshHandler`). **The circular import is fully intact — the fix was never implemented.**

**Evidence:**
- `frontend/src/shared/api/axiosInstance.ts` line 4: `import { refreshToken } from '../../features/auth/api/authApi'` — shared layer imports from feature module
- `frontend/src/features/auth/api/authApi.ts` line 1: `import { axiosInstance } from '../../../shared/api/axiosInstance'` — feature module imports from shared layer
- The `registerRefreshHandler` callback pattern described in the task does not exist anywhere in the codebase.

**Architectural Impact:** Dependency direction violation (shared → feature). While it works due to JS module hoisting, this creates a fragile pattern that can break during HMR, violates clean architecture dependency direction, and contradicts the implemented feature documentation (SPEC.md describes working architecture).

**Execution Risk:** MEDIUM — currently functional but fragile. Will break unpredictably during frontend development.

**Required Correction:** Either (a) implement the `registerRefreshHandler` callback pattern as specified in the task, or (b) extract the refresh token logic into a third module that both can import from without circular dependency.

---

### CRITICAL — C004: TASK_007 — Error Sanitization Incomplete (upload.py Still Leaks)

**Severity:** MAJOR (downgraded from CRITICAL because some routes were fixed)
**Type:** SPEC-DEVIATION (Partial Implementation)
**Task:** TASK_007_be016_error_message_sanitization
**Affected File:** `src/mkobi/api/routes/upload.py`

**Problem:** The task required replacing ALL `detail=f"...{str(e)}"` patterns across all route modules with generic messages. While `layouts.py`, `processing_logs.py`, and `dashboards_crud.py` had their generic `except Exception` handlers fixed, **`upload.py` still extensively leaks internal error details through `detail=str(e)` in 13 locations.**

**Evidence:**
- `src/mkobi/api/routes/upload.py`:
  - Lines 76, 85, 90, 95, 100: `_handle_value_error()` helper maps ValueError strings directly to HTTP response detail via `detail=str(e)`
  - Lines 203, 258, 264: `detail=str(e)` in generic exception handlers
  - Lines 314, 320, 370, 376: `detail=str(e)` in processing/status/result endpoints

The `_handle_value_error()` function at lines 69-101 is particularly problematic: it catches internal service exceptions and forwards the exception message directly to the API response via `detail=str(e)`.

**Contrast with correctly fixed files:**
- `layouts.py` lines 99, 139, 268, 331: generic `except Exception` → `detail="Error creating layout"` etc. (correct)
- `dashboards_crud.py` lines 74, 147, 343, 396: generic messages (correct)
- `processing_logs.py` lines 91, 125: generic messages (correct)

**Architectural Impact:** Information disclosure vulnerability. Internal exception messages (database errors, file system paths, service names) can leak to API consumers.

**Execution Risk:** MEDIUM-HIGH — the `_handle_value_error` pattern leaks validation error strings which may contain internal implementation details.

**Required Correction:** Replace `detail=str(e)` with generic error messages in `upload.py` and add `logger.error(..., exc_info=True)` before each response. The `_handle_value_error` helper needs to use generic messages for each error type category rather than forwarding exception strings.

---

### CRITICAL — C005: TASK_010 — Temp File Cleanup Logging NOT Implemented

**Severity:** MAJOR (downgraded from task's MEDIUM — actual bug severity is higher)
**Type:** SPEC-DEVIATION (Claimed Fix Not Applied)
**Task:** TASK_010_dp002_temp_file_cleanup_logging
**Affected File:** `src/mkobi/workers/data_worker.py`

**Problem:** The task completion notes claim "Changed `except Exception: pass` to `logger.warning("Failed to clean up temp file %s", file_path, exc_info=True)`" — but **the actual code still has `except Exception: pass`**.

**Evidence:**
- `src/mkobi/workers/data_worker.py` lines 261-266:
  ```python
  # Clean up temp file on error
  if file_path.exists():
      try:
          await asyncio.to_thread(file_path.unlink)
      except Exception:
          pass
  ```
  This is the exact original code. No logging was added. The `pass` silently swallows all cleanup exceptions.

**Architectural Impact:** Silently ignored exceptions in production mean: (1) orphaned temp files accumulate on disk, (2) no monitoring signal when cleanup fails, (3) impossible to debug file system issues.

**Execution Risk:** MEDIUM — temp files will accumulate if cleanup fails (e.g., permission errors, locked files, full disk).

**Required Correction:** Replace `except Exception: pass` at line 265-266 with `logger.warning("Failed to clean up temp file %s", file_path, exc_info=True)`.

---

### MAJOR — M001: TASK_011 — Mock Antipattern Already Clean (False Positive Task)

**Severity:** MINOR (task was unnecessary)
**Type:** DOC-UPDATE (Informational)
**Affected File:** `tests/test_data_service.py`

**Evidence:** The test file `tests/test_data_service.py` shows the class named `TestDataServiceIntegration` with docstring "Integration tests for DataService with real database." No `assert_called_once` patterns were found in the file (grep returned zero matches). The existing tests already verify actual database state through repository queries.

**Conclusion:** The mock antipattern described in TST-005 appears to have been fixed in a prior work session or never existed in the current form. The task should be marked as verified-clean rather than implemented. No architectural impact.

---

### MAJOR — M002: TASK_012 — Ambiguous Status Code Assertions Still Present

**Severity:** MAJOR
**Type:** SPEC-DEVIATION (Task Not Implemented)
**Task:** TASK_012_tst003_ambiguous_status_codes
**Affected File:** `tests/test_upload_api.py`

**Problem:** The task required replacing `assert response.status_code in [201, 400, 422]` with specific expected status codes. **The ambiguous assertions are still present at 3 locations.**

**Evidence:**
- `tests/test_upload_api.py` line 357: `assert response.status_code in [201, 400, 422]` (test_upload_malformed_csv_wrong_delimiter)
- `tests/test_upload_api.py` line 428: `assert response.status_code in [201, 400, 422]` (test_upload_wrong_encoding)
- `tests/test_upload_api.py` line 504: `assert response.status_code in [201, 400, 422]` (test_upload_invalid_data_types)

Additionally, the `test_upload_invalid_data_types` test description and assertion comment still says "Should either reject or accept with error logged" — indicating no clear expected behavior was defined.

**Impact:** Tests are non-deterministic and pass regardless of the actual API behavior. They provide zero validation value and create a false sense of coverage.

**Required Correction:** Define the expected behavior for each test case:
- Malformed CSV with semicolons: Polars typically parses this as single column → should be 201 (accepted, then may fail in processing)
- Wrong encoding (UTF-16): Should be 400 or 422 (parse failure)
- Invalid data types: Depends on Polars coercion behavior — must verify and assert specific code

Then replace `[201, 400, 422]` with the specific expected code and add a comment explaining the expected behavior.

---

## Architectural Warnings

### AW-001: Circular Import Remains in Frontend (FE-001 — Unresolved)

**Type:** Architecture Drift
**Severity:** MEDIUM

The circular dependency between `shared/api/axiosInstance.ts` and `features/auth/api/authApi.ts` remains. While functional in production builds, it violates clean architecture dependency direction and creates fragility during HMR development. The `shared` layer must never import from `feature` modules.

**Affected Files:** `frontend/src/shared/api/axiosInstance.ts`, `frontend/src/features/auth/api/authApi.ts`

---

### AW-002: Upload Route Error Handling Pattern Inconsistency

**Type:** Consistency Warning
**Severity:** LOW

After TASK_007, three of four targeted route modules (`layouts.py`, `processing_logs.py`, `dashboards_crud.py`) use generic error messages in their generic `except Exception` handlers. However, `upload.py` has a custom `_handle_value_error()` function that forwards `str(e)` directly to clients. This creates an inconsistent error handling pattern across the API surface.

---

## Semantic Stability Warnings

### SS-001: Password Validation Gap at API Boundary

**Type:** Security — Fragile Trust Boundary
**Severity:** CRITICAL

The `RegisterRequest` Pydantic model in `src/mkobi/models/auth.py` accepts password strings without any validation. The `validate_password()` function exists in `src/mkobi/utils/validators.py` but is never wired in. This means:
- The API trust boundary provides zero password strength enforcement
- Even if the service layer adds validation later, the Pydantic layer (first line of defense) is unprotected
- Direct service calls (bypassing the API layer) also skip validation

---

### SS-002: MIME Type Optional Enforcement

**Type:** Security — Validation Bypass Path
**Severity:** CRITICAL

The `validate_mime_type()` function returns silently when `content_type` is None. The `validate_file()` function calls `validate_mime_type()` but proceeds with file processing regardless. This creates a bypass path where the HTTP Content-Type header is optional for file type validation.

---

## UX/UI Findings

### UX-001: LogViewer Status Filter Not Mapped to Backend Parameter

**Severity:** MINOR (functional via fallback)
**Affected Files:** `frontend/src/features/admin/api/adminApi.ts`, `frontend/src/features/admin/ui/LogViewer.tsx`

The `LogViewer` component sends `status_filter` as a query parameter (matching the backend's expected `status_filter` name). However, the `getLogs()` function in `adminApi.ts` (line 88-90) just passes the entire `filters` object directly to axios `params`:
```typescript
const response = await axiosInstance.get<ProcessingLog[]>('/admin/logs', { params: filters })
```

The `LogFilters` interface defines `status_filter?` while the backend query parameter is `status_filter`. This mapping happens to work, but there's no explicit parameter renaming. If the frontend field name ever diverges from the backend name, this would silently break.

---

## Test and Verification Findings

### TV-001: Ambiguous Test Assertions (TST-003)

**Severity:** MAJOR
**Affected File:** `tests/test_upload_api.py`

Three tests accept `[201, 400, 422]` as valid status codes, making them pass for any outcome. These tests provide no real coverage:
- `test_upload_malformed_csv_wrong_delimiter` (line 357)
- `test_upload_wrong_encoding` (line 428)
- `test_upload_invalid_data_types` (line 504)

### TV-002: Temp File Cleanup Tests Depend on Database State

**Severity:** MINOR
**Affected File:** `tests/test_upload_api.py`

`TestTempFileCleanup` tests require the users table to exist and the `test_user` fixture to resolve correctly. TASK_010 completion notes acknowledge one test fails due to missing database table in fresh state — this is a test infrastructure concern, not a code concern.

---

## Rollout Risk Analysis

| Risk | Severity | Description |
|------|----------|-------------|
| Password validation gap | CRITICAL | Weak passwords accepted; SEC-001 unresolved |
| MIME validation bypass | CRITICAL | Arbitrary file upload possible; SEC-003 unresolved |
| Internal error leakage | MAHOR | `detail=str(e)` in upload.py leaks implementation details |
| Silent temp file accumulation | MEDIUM | `except Exception: pass` in data_worker.py cleanup |
| Circular import fragility | MEDIUM | Frontend shared→feature dependency unresolved |
| Non-deterministic tests | LOW | Three upload tests accept any of 3 status codes |

---

## Required Fixes Before Approval

| Priority | ID | Fix Description |
|----------|-----|-----------------|
| P0 | C001 | Wire `validate_password()` into `RegisterRequest` @field_validator and `register_user()` service method |
| P0 | C002 | Change `validate_mime_type()` to raise ValueError when content_type is None |
| P1 | C003 | Break circular import: implement `registerRefreshHandler` callback pattern or extract shared refresh module |
| P1 | C004 | Sanitize `upload.py` error responses: replace `detail=str(e)` with generic messages + exc_info logging |
| P1 | C005 | Add `logger.warning` to data_worker.py temp file cleanup `except` block |
| P2 | M002 | Replace ambiguous `[201, 400, 422]` assertions with specific expected codes |

---

## Mandatory Fixes vs Advisory Recommendations

### Mandatory (blocking approval):
1. **C001** — Password validation must be wired in. Security-critical.
2. **C002** — MIME validation must reject None Content-Type. Security-critical.
3. **C004** — Upload.py error sanitization must be completed. Partially implemented task.
4. **C005** — data_worker.py cleanup logging must be added. Completion claim is false.
5. **M002** — Ambiguous test assertions must be resolved to provide deterministic coverage.

### Advisory (recommended but not blocking):
1. **C003** — Circular import is a code quality issue, not a runtime defect.
2. **AW-001** — Architectural inconsistency in route error handling patterns.
3. **UX-001** — Add explicit parameter mapping in adminApi.getLogs for clarity.
4. **AW-002** — Standardize error handling pattern across all route modules.
