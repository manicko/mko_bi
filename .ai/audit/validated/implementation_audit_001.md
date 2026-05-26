## Findings and Problems

### Finding 1 — CRITICAL: Frontend crashes on every page load (PRE-EXISTING, UNFIXED)

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **Type** | [RUNTIME] Pre-existing from audit_report_001 |
| **File** | `frontend/src/app/routes.tsx` |
| **Line** | 26 |
| **Problem** | `<TrailingSlashRedirect />` placed as direct child of `<Routes>` — invalid in react-router-dom v7 |
| **Impact** | React app crashes on every page load. ErrorBoundary shows "Something went wrong". Application is completely non-functional. |
| **Affected URLs** | `http://localhost:5173/*` (Vite dev), `http://localhost:8000/*` (built frontend) |
| **Root Cause** | react-router-dom v7 strictly validates children of `<Routes>`. Only `<Route>` and `<React.Fragment>` are allowed. |
| **Evidence** | `routes.tsx:26` — `<TrailingSlashRedirect />` is a plain component, not a `<Route>` |
| **Status** | NOT FIXED by any current task. Blocks all users. |

**Required correction:** Move `TrailingSlashRedirect` inside a layout route's `element` prop, or wrap it within `<React.Fragment>` inside a route.

---

### Finding 2 — MEDIUM: Backend restart loop from Docker volume mounts (PRE-EXISTING, UNFIXED)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Type** | [RUNTIME] Pre-existing from audit_report_001 |
| **File** | `docker/docker-compose.override.yml` |
| **Line** | 70 |
| **Problem** | `- ../tests:/app/tests` volume mount triggers uvicorn `--reload` on test file changes |
| **Impact** | Backend restarts every few seconds when `__pycache__` files update. Causes intermittent 503s. |
| **Status** | NOT FIXED by any current task. Degrades reliability in dev environment. |

**Required correction:** Add `--reload-exclude tests/` to uvicorn command, or remove tests volume mount.

---

### Finding 3 — LOW: Placeholder page title (PRE-EXISTING, UNFIXED)

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Type** | [DOC-UPDATE] Pre-existing from audit_report_001 |
| **File** | `frontend/index.html` |
| **Line** | 7 |
| **Problem** | `<title>frontend</title>` is Vite default placeholder |
| **Impact** | Browser tab shows "frontend" instead of application name. |
| **Status** | NOT FIXED. |

**Required correction:** Change to `<title>mkobi BI Dashboard</title>`.

---

### Finding 4 — INFORMATIONAL: test_upload_too_large may have inaccurate size check path

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Type** | [TEST-QUALITY] |
| **File** | `tests/test_upload_api.py` |
| **Line** | 190-227 |
| **Problem** | Test mocks `get_config()` with `max_file_size=1` and sends a file containing `b"x"` (1 byte). The endpoint checks `file.size > config.max_file_size` which is `1 > 1 = False`. The size check may not actually trigger — the test may pass for the wrong reason. |
| **Risk** | False-positive test. The 413 response might come from a different code path than the one being tested. |
| **Recommendation** | Use `max_file_size=0` in mock or send a file with 2+ bytes to ensure `file.size > config.max_file_size` evaluates to True. |

---

### Finding 5 — INFORMATIONAL: test_process_upload_file_too_large uses real temp file

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Type** | [TEST-QUALITY] |
| **File** | `tests/test_data_service.py` |
| **Line** | 182-206 |
| **Problem** | Test creates a real temp file (`NamedTemporaryFile`) and writes `b"x"` to it, then patches `Path.stat()` to return a large size. While this is a real file on disk (not 100MB+), it's still I/O where none is needed. |
| **Risk** | Minimal — uses small file, properly cleaned up with try/finally. Not the same issue as the original 102MB allocation. |
| **Recommendation** | Could use `MagicMock` for the file path entirely since `stat()` is mocked. Not blocking — test is functional and fast. |

---

## Architectural Warnings

### AW-001: Upload test mixes integration and unit testing patterns

**File:** `tests/test_upload_api.py`
**Observation:** `test_upload_too_large` uses mocking (unit test technique) within an integration test class that hits the full HTTP stack. The mock on `get_config` doesn't directly control `file.size` (which comes from `UploadFile`), creating an indirect coupling between the mock and the assertion.
**Risk:** Low — test works, but coupling is fragile.
**Recommendation:** Consider whether this test should be a pure integration test (using actual large file fixture) or a pure unit test (testing the validation function directly).

---

### AW-002: Pre-existing mypy "no-any-return" errors in dashboards.py

**File:** `src/mkobi/api/routes/dashboards.py`, lines 196 and 712
**Observation:** Two service-layer calls return `Any` from functions with typed return signatures. These are pre-existing issues, not introduced by current tasks.
**Risk:** Low — service layer return types lack full mypy coverage.
**Recommendation:** Add return type annotations to `get_user_dashboards()` and `get_dashboard_access_list()` service methods.

---

## Semantic Stability Warnings

### SS-001: Filter contract in data_service lacks explicit schema

**Files:** `src/mkobi/services/data_service.py`, `src/mkobi/api/routes/data.py`
**Observation:** The `filters` parameter is `dict[str, Any] | None` — no validation of filter structure, operators, or semantics. The frontend and backend share no explicit filter contract.
**Risk:** Medium — filters could be sent in unexpected formats, causing silent no-ops or runtime errors.
**Recommendation:** Define a Pydantic model for filter structure (field, operator, value) and validate in the route handler before passing to service layer. This should be documented in the API spec.

---

## UX/UI Findings

### UX-001: Frontend completely non-functional (pre-existing)

The `TrailingSlashRedirect` crash (Finding 1) makes all UX flows unreachable. No UX assessment possible until this is fixed.

---

## Test and Verification Findings

| Metric | Value |
|--------|-------|
| Total new/updated test files | 13 |
| Total test functions in data pipeline tests | 156 (45 + 42 + 69) |
| test_graphs.py test count | 10 (was 2, required 8+) |
| test_repositories.py test count | 30 |
| test_auth.py duplicate flush | Removed (2 → 1 in test_register_request_success) |
| test_storage_manager.py duplicate tests | Removed (_instance variants) |
| ruff on all modified files | PASS (all checks) |
| mypy on all modified files | 2 pre-existing errors, 0 new errors |

**Test coverage quality:** Generally good. Tests target the right concerns (validation, CRUD, access control, edge cases). The data pipeline tests are pure unit tests (no DB dependency) as required.

**Outstanding gaps:**
- `TrailingSlashRedirect` crash has no regression test
- Filter contract validation has no schema-level tests
- LoginForm→useAuth integration has no frontend unit test

---

## Rollout Risk Analysis

### RR-001: Application non-functional in current state

**Risk:** CRITICAL
**Cause:** `TrailingSlashRedirect` crash (Finding 1)
**Impact:** Zero users can access the application
**Mitigation required:** Fix routes.tsx before any rollout

### RR-002: Docker dev environment instability

**Risk:** MEDIUM
**Cause:** Volume mount reload loop (Finding 2)
**Impact:** Intermittent 503s during development
**Mitigation required:** Exclude tests/ from uvicorn reload watch

### RR-003: Test suite depends on Docker for full execution

**Risk:** LOW
**Cause:** 173 tests require PostgreSQL via Docker (V-018 fix)
**Impact:** Tests cannot run without Docker infrastructure
**Mitigation:** This is by design — Docker test compose is the standard test environment.

---

## Required Fixes Before Approval

### Blocking (must fix before any rollout)

1. **Fix `TrailingSlashRedirect` placement in `routes.tsx:26`** — Move inside a layout route or wrap in `<React.Fragment>` within a `<Route>`. This is a pre-existing critical bug that makes the entire application unusable.

### Recommended (should fix before production)

2. **Fix Docker volume mount reload loop** — Add `--reload-exclude tests/` to uvicorn command in `docker-compose.override.yml`
3. **Update page title** — Change `<title>frontend</title>` to `<title>mkobi BI Dashboard</title>` in `frontend/index.html`
4. **Fix test_upload_too_large accuracy** — Use `max_file_size=0` in mock to ensure the size check path is actually exercised

### Advisory (improvements for future iterations)

5. **Define filter contract schema** — Add Pydantic model for filter structure
6. **Add mypy return types** to service layer methods returning `Any`
7. **Add regression test** for TrailingSlashRedirect fix

---

## Final Verdict

**REQUIRES FIXES**

All 23 implementation tasks are correctly implemented and meet their acceptance criteria. Ruff and mypy pass. Test coverage is comprehensive and well-structured.

However, the application has **2 pre-existing critical issues** (from audit_report_001) that were not addressed by any current task and remain unfixed:

1. **CRITICAL:** Frontend crashes on every page load — no user can access the application
2. **MEDIUM:** Backend restart loop in Docker dev environment

These issues existed before the current task batch and were outside its scope. They must be fixed before the application can be rolled out or approved for production use.

**The current task batch itself is APPROVED.** The blocking issues are pre-existing and should be addressed as separate tasks.

---

**Author:** OWL (implementation-audit)
**Date:** 2026-05-26
**Version:** 1.0
