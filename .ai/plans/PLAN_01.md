# PLAN_01: Error Handling Standardization

> **Phase:** 01 — Error Handling Standardization
> **Branch:** `feat/react`
> **Status:** Planned, ready for execution
> **Date:** 2026-06-03
> **Spec version:** 3.5
>
> **Related documents:**
> - [DECISION_01.md](../problems/decisions/DECISION_01.md) — locked decisions
> - [RESEARCH_01.md](../researches/RESEARCH_01.md) — research findings
> - [SPEC.md](../../docs/SPEC.md) — project specification
> - [AGENTS.md](../../AGENTS.md) — agent guidelines

---

## 1. Goal

Standardize **all** API error responses across the entire backend into a single structured format with machine-readable codes, and build a unified frontend error handling system so users see meaningful, localized, process-specific messages instead of raw HTTP codes (`419`, `undefined`, `Network Error`).

**Target state:** "В файле отсутствует обязательная колонка." instead of "Required column 'TVR' is missing."

### In scope

1. Backend — `ErrorCode(StrEnum)`, `AppException` as the single error path, RFC 7807-inspired response format
2. Frontend — shared error extractor utility, per-feature localized error message maps, toast + inline display strategy
3. Documentation — AGENTS.md, docs/08-security/, docs/99-reference/

### Out of scope

- Adding new validation rules or changing business logic
- Rate limiter redesign
- i18n framework integration (hardcoded Russian strings only)
- Sentry/error tracking
- Automatic retry logic
- User-facing error ID for support
- Batch/multi-error responses

---

## 2. Current State (from Research)

| Metric | Value |
|--------|-------|
| Total `raise HTTPException` sites in `src/mkobi` | **168** |
| Existing `AppException` subclasses | 4 (NotFoundException, PermissionDeniedException, ValidationException, FileUploadException) |
| Centralized `ErrorCode` enum | **Does not exist** — error codes are hardcoded strings |
| Frontend error code parsing | **None** — no structured error handling |
| Frontend error display | Raw `error.message`, no code resolution |

### HTTPException sites per file

| File | Count | Risk |
|------|-------|------|
| `admin.py` | 20 | medium |
| `upload.py` | 16 | medium (ValueError mapping, file cleanup) |
| `auth.py` | 16 | **high** (token refresh, cookies) |
| `deps.py` | 16 | **high** (used by ALL endpoints) |
| `graphs.py` | 16 | low |
| `users.py` | 15 | medium |
| `layouts.py` | 15 | low |
| `dashboards_crud.py` | 14 | medium |
| `dashboards_filters.py` | 9 | low |
| `dashboards_access.py` | 7 | low |
| `processing_configs.py` | 7 | low |
| `data.py` | 6 | low |
| `dashboards_graphs.py` | 4 | low |
| `processing_logs.py` | 3 | low |
| `filter_values.py` | 1 | low |
| `app.py` | 1 | low |

### Key file locations

| Component | File Path |
|-----------|-----------|
| AppException + ErrorResponse + handlers | `src/mkobi/utils/exceptions.py` |
| Enums | `src/mkobi/models/enums.py` |
| Axios instance | `frontend/src/shared/api/axiosInstance.ts` |
| Frontend types | `frontend/src/shared/types/api.types.ts` |

---

## 3. Target Architecture

### 3.1 Error Response Format (RFC 7807 + extensions)

```json
{
  "type": "https://api.mkobi.com/errors/missing-column",
  "title": "Missing required column",
  "status": 400,
  "detail": "Required column 'TVR' is missing",
  "code": "MISSING_COLUMN",
  "details": {
    "column": "TVR"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | URI-style error type for documentation/reference |
| `title` | `str` | Short human-readable summary |
| `status` | `int` | HTTP status code |
| `detail` | `str` | Developer-facing message (English, for logging/debug) |
| `code` | `str` | Machine-readable `ErrorCode(StrEnum)` value — the contract between backend and frontend |
| `details` | `dict \| None` | Optional structured context (column names, max values, allowed types) |

### 3.2 ErrorCode Enum Structure

All codes in `src/mkobi/models/enums.py` as `ErrorCode(StrEnum)`, `UPPER_SNAKE_CASE`:

| Category | Codes |
|----------|-------|
| **General** | `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`, `RATE_LIMIT_EXCEEDED` |
| **Auth** | `AUTHENTICATION_FAILED`, `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `INVALID_TOKEN` |
| **Authorization** | `PERMISSION_DENIED`, `INSUFFICIENT_PERMISSIONS`, `ACCESS_DENIED` |
| **Resource** | `NOT_FOUND`, `DASHBOARD_NOT_FOUND`, `USER_NOT_FOUND`, `GRAPH_NOT_FOUND`, `FILTER_NOT_FOUND`, `LAYOUT_NOT_FOUND`, `PROCESSING_CONFIG_NOT_FOUND` |
| **Validation** | `VALIDATION_ERROR`, `INVALID_EMAIL`, `INVALID_PASSWORD`, `MISSING_REQUIRED_FIELD`, `INVALID_FIELD_VALUE` |
| **File** | `FILE_UPLOAD_ERROR`, `FILE_TOO_LARGE`, `INVALID_FILE_TYPE`, `FILE_PROCESSING_ERROR` |
| **Conflict** | `EMAIL_ALREADY_EXISTS`, `FILTER_ALREADY_BOUND`, `DUPLICATE_RESOURCE` |
| **Processing** | `PROCESSING_FAILED`, `PROCESSING_IN_PROGRESS` |

### 3.3 Status Code Mapping

| ErrorCode pattern | HTTP status |
|-------------------|-------------|
| `*_NOT_FOUND` | 404 |
| `PERMISSION_DENIED`, `ACCESS_DENIED`, `INSUFFICIENT_PERMISSIONS` | 403 |
| `VALIDATION_ERROR`, `INVALID_*`, `MISSING_*` | 422 |
| `FILE_UPLOAD_ERROR` | 400 |
| `FILE_TOO_LARGE` | 413 |
| `INVALID_FILE_TYPE` | 415 |
| `EMAIL_ALREADY_EXISTS`, `DUPLICATE_RESOURCE`, `FILTER_ALREADY_BOUND` | 409 |
| `AUTHENTICATION_FAILED`, `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `INVALID_TOKEN` | 401 |
| `RATE_LIMIT_EXCEEDED` | 429 |
| `INTERNAL_ERROR`, `PROCESSING_FAILED` | 500 |
| `SERVICE_UNAVAILABLE` | 503 |

### 3.4 Error Layers

| Layer | Where | What |
|-------|-------|------|
| **L1** — Client-side pre-validation | React components | File size, extension, required fields — no network request |
| **L2** — API transport errors | Axios interceptor | HTTP status codes, network failures, rate limiting, auth errors |
| **L3** — Business logic errors | Contextual display | Missing columns, invalid data, processing failures |

### 3.5 Frontend Display Strategy

- **Toast** (`react-hot-toast`) for all API-level errors — displayed in the axios response interceptor globally
- **Inline** (form-level) for field validation errors — displayed per-component
- **Per-feature localized error message maps**: each feature (`upload`, `auth`, `admin`, `dashboards`, `users`) maintains its own `errorMessages` map: `Record<ErrorCode, string>`
- **Resolution order:**
  1. Look up `error.code` in feature's message map → display localized Russian text
  2. Unknown code → display `error.detail` (backend English message)
  3. No detail → display generic fallback ("Произошла ошибка")

---

## 4. Execution Waves

### Wave 1 — Foundation (2 tasks, sequential)

**Must complete before all other waves.**

| Task | Name | Files | Effort | Risk |
|------|------|-------|--------|------|
| TASK_01_01 | Create ErrorCode StrEnum and restructure ErrorResponse/AppException | `src/mkobi/models/enums.py`, `src/mkobi/utils/exceptions.py` | medium | medium |
| TASK_01_02 | Update exception handlers for RFC 7807 format | `src/mkobi/utils/exceptions.py`, `src/mkobi/api/app.py` | small | low |

**Deliverables:**
- `ErrorCode(StrEnum)` with ~40 codes in `enums.py`
- `ErrorResponse` model with RFC 7807 fields: `type`, `title`, `status`, `detail`, `code`, `details`
- `AppException` constructor accepts `code: ErrorCode` and `details: dict | None`
- 4 existing subclasses updated + 2 new (`AuthenticationException`, `ConflictException`)
- Status code mapping mechanism on `AppException`
- All exception handlers produce RFC 7807 JSON
- `StarletteHTTPException` handler added

---

### Wave 2 — High-Priority Backend Routes (2 tasks, parallel after Wave 1)

| Task | Name | Sites | Effort | Risk |
|------|------|-------|--------|------|
| TASK_02_01 | Migrate upload.py | 16 | medium | medium |
| TASK_02_02 | Migrate auth.py | 16 | medium | **high** |

**Key constraints:**
- `upload.py`: Preserve temp file cleanup in `finally` blocks; careful ValueError→ErrorCode mapping
- `auth.py`: Token refresh flow must not break; cookie handling unchanged; rate limiting preserved

---

### Wave 3 — More Backend Routes (2 tasks, parallel after Wave 1)

| Task | Name | Sites | Effort | Risk |
|------|------|-------|--------|------|
| TASK_03_01 | Migrate admin.py | 20 | medium | medium |
| TASK_03_02 | Migrate dashboards_crud.py | 14 | small | medium |

**Key constraints:**
- `admin.py`: Admin role checks must not be weakened
- `dashboards_crud.py`: Resource-level access control preserved

---

### Wave 4 — Remaining Backend Routes (5 tasks, parallel after Wave 1)

| Task | Name | Sites | Effort | Risk |
|------|------|-------|--------|------|
| TASK_04_01 | Migrate deps.py | 16 | medium | **high** |
| TASK_04_02 | Migrate graphs.py | 16 | small | low |
| TASK_04_03 | Migrate users.py | 15 | small | medium |
| TASK_04_04 | Migrate layouts.py | 15 | small | low |
| TASK_04_05 | Migrate remaining 10 route files | ~42 total | small | low |

**Key constraints:**
- `deps.py`: **HIGH RISK** — used by ALL endpoints. FastAPI DI system must continue working. AppException must be caught by registered handler, not FastAPI's default.
- Remaining files: `dashboards_access.py` (7), `processing_configs.py` (7), `dashboards_graphs.py` (4), `processing_logs.py` (3), `filter_values.py` (1), `data.py` (6), `dashboards_filters.py` (9), plus `dashboards.py`, `filters.py`, `client_errors.py` (verify zero sites)

---

### Wave 5 — Frontend (3 tasks, sequential within wave, after backend complete)

| Task | Name | Files | Effort | Risk |
|------|------|-------|--------|------|
| TASK_05_01 | Create ApiError interface and extractApiError utility | `frontend/src/shared/types/api.types.ts`, `frontend/src/shared/api/errorHandler.ts` | small | low |
| TASK_05_03 | Create per-feature error message maps | `frontend/src/features/*/model/errorMessages.ts` (5 files) + `frontend/src/shared/api/errorMessages.ts` | medium | low |
| TASK_05_02 | Update axios interceptor for RFC 7807 + localized toasts | `frontend/src/shared/api/axiosInstance.ts` | small | medium |

**Note:** TASK_05_02 depends on both TASK_05_01 and TASK_05_03. TASK_05_01 and TASK_05_03 can run in parallel.

**Key constraints:**
- `extractApiError()` extraction chain: AxiosError → `error.response.data` → `error.message` → generic Russian fallback
- Handles both new RFC 7807 format and legacy FastAPI validation format
- Axios interceptor preserves existing 401/403/session handling exactly
- Login endpoint errors still skipped (handled inline by LoginForm)
- No `any` types anywhere

---

### Wave 6 — Documentation (3 tasks, parallel after backend complete)

| Task | Name | Files | Effort | Risk |
|------|------|-------|--------|------|
| TASK_06_01 | Update AGENTS.md with error handling section | `AGENTS.md` | small | minimal |
| TASK_06_02 | Create error format security documentation | `docs/08-security/error-format.md` | small | minimal |
| TASK_06_03 | Create error handling reference guide | `docs/99-reference/error-handling-guide.md` | small | minimal |

---

### Wave 7 — Verification (1 task, after all above)

| Task | Name | Effort | Risk |
|------|------|--------|------|
| TASK_07_01 | End-to-end verification of error handling | medium | medium |

**Verification checklist:**
- [ ] Zero `raise HTTPException` sites in any route/deps file
- [ ] Backend `ruff check src/` passes
- [ ] Backend `mypy src/` passes
- [ ] Frontend `npm build` succeeds (TypeScript compilation)
- [ ] Frontend `npm lint` passes
- [ ] Backend `pytest tests/` passes (or failures documented)
- [ ] Frontend `npm test` passes (or failures documented)
- [ ] `ErrorCode` enum appears in OpenAPI spec
- [ ] All documentation files created and valid
- [ ] All frontend error handling files created
- [ ] RFC 7807 format verified in actual API responses (smoke check)

---

## 5. Dependency Graph

```
Wave 1:
  TASK_01_01 → TASK_01_02

Wave 2 (depends on Wave 1):
  TASK_01_01 + TASK_01_02 → TASK_02_01 (upload.py)
  TASK_01_01 + TASK_01_02 → TASK_02_02 (auth.py)

Wave 3 (depends on Wave 1):
  TASK_01_01 + TASK_01_02 → TASK_03_01 (admin.py)
  TASK_01_01 + TASK_01_02 → TASK_03_02 (dashboards_crud.py)

Wave 4 (depends on Wave 1):
  TASK_01_01 + TASK_01_02 → TASK_04_01 (deps.py)
  TASK_01_01 + TASK_01_02 → TASK_04_02 (graphs.py)
  TASK_01_01 + TASK_01_02 → TASK_04_03 (users.py)
  TASK_01_01 + TASK_01_02 → TASK_04_04 (layouts.py)
  TASK_01_01 + TASK_01_02 → TASK_04_05 (remaining routes)

Wave 5 (depends on Wave 1 + backend):
  TASK_01_01 + TASK_01_02 → TASK_05_01 (ApiError types)
  TASK_05_01 → TASK_05_03 (error message maps)
  TASK_05_01 + TASK_05_03 → TASK_05_02 (axios interceptor)

Wave 6 (depends on Wave 1 + backend):
  TASK_01_01 + TASK_01_02 + TASK_02_01-02 + TASK_03_01-02 + TASK_04_01-05 → TASK_06_01 (AGENTS.md)
  TASK_01_01 + TASK_01_02 → TASK_06_02 (error-format.md)
  TASK_01_01 + TASK_01_02 + TASK_05_01-03 → TASK_06_03 (error-handling-guide.md)

Wave 7 (depends on everything):
  All TASK_02_* + TASK_03_* + TASK_04_* + TASK_05_* + TASK_06_* → TASK_07_01 (verification)
```

**Parallel execution groups:**
- Wave 1: sequential (01 → 02)
- Waves 2, 3, 4: fully parallel after Wave 1 completes
- Wave 5: TASK_05_01 → (TASK_05_03 ∥ TASK_05_02 after 03)
- Wave 6: all 3 tasks parallel
- Wave 7: sequential after all

---

## 6. Migration Rules (for all backend tasks)

### Raising errors — ALWAYS

```python
# CORRECT
raise AppException(code=ErrorCode.DASHBOARD_NOT_FOUND, detail="Dashboard not found")

# CORRECT with details
raise AppException(
    code=ErrorCode.FILE_TOO_LARGE,
    detail="File exceeds maximum allowed size",
    details={"max_size_mb": 100, "filename": filename}
)

# FORBIDDEN — never use in route/service code
raise HTTPException(status_code=404, detail="...")
```

### Rules

1. Always use `raise AppException(code=ErrorCode.X, detail="...", details={...})` — never `raise HTTPException(...)`
2. `detail` is a clear English developer-facing message. Never include stack traces, raw exception text, or internal paths
3. `details` contains structured context: column names, field names, max values, allowed values
4. Every new error condition gets a new `ErrorCode(StrEnum)` entry — no ad-hoc string codes
5. Service layer raises `AppException` — routes only catch and re-raise
6. No manual `JSONResponse` with error shapes in route code
7. Global exception handlers in `app.py` / `add_exception_handlers()` are the only place that produces HTTP error responses

### Frontend rules

1. For automatic toast display: rely on the axios interceptor — no `try/catch` needed
2. For inline form errors: `try/catch` → `extractApiError()` → set field error state from `code` + `details`
3. Never show raw `error.message` to the user — always resolve through the error message map
4. L1 client-side validation uses Zod or inline checks — messages are hardcoded in the component
5. When backend adds a new `ErrorCode(StrEnum)` entry, the corresponding frontend feature `errorMessages` map MUST be updated

---

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `deps.py` migration breaks FastAPI DI | **Critical** — all endpoints down | Test DI propagation early; run full test suite after deps.py migration |
| `auth.py` breaks token refresh flow | **High** — users locked out | Preserve 401 status code mapping; test refresh after migration |
| `upload.py` disrupts file cleanup | **High** — orphan files on disk | Preserve `finally` blocks unchanged; only replace raise statements |
| `ValidationException` changes from 400 → 422 | **Medium** — existing tests fail | Document as known behavior change; update tests |
| Existing tests reference old ErrorResponse shape | **Medium** — test failures | Update tests after Wave 1 foundation is complete |
| StarletteHTTPException handler conflicts with FastAPI defaults | **Low** — incorrect error format | Register handler in correct order: AppException → StarletteHTTPException → Exception |
| Frontend axios interceptor breaks token refresh queue | **High** — concurrent 401s fail | Preserve existing 401/403 logic exactly; only add generic handler at end |

---

## 8. Detailed Task Specifications

> Full task specifications with acceptance criteria, validation commands, and step-by-step instructions are in the individual YAML files:
>
> `C:\py_dev\mkobi\.ai\plans\tasks\PLAN_01_01_error_code_enum.yaml` through `PLAN_01_18_verification.yaml`

### Quick reference

| Wave | Task ID | YAML File | Target File(s) |
|------|---------|-----------|----------------|
| 1 | TASK_01_01 | `PLAN_01_01_error_code_enum.yaml` | `enums.py`, `exceptions.py` |
| 1 | TASK_01_02 | `PLAN_01_02_exception_handlers.yaml` | `exceptions.py`, `app.py` |
| 2 | TASK_02_01 | `PLAN_01_03_upload_migration.yaml` | `upload.py` |
| 2 | TASK_02_02 | `PLAN_01_04_auth_migration.yaml` | `auth.py` |
| 3 | TASK_03_01 | `PLAN_01_05_admin_migration.yaml` | `admin.py` |
| 3 | TASK_03_02 | `PLAN_01_06_dashboards_crud_migration.yaml` | `dashboards_crud.py` |
| 4 | TASK_04_01 | `PLAN_01_07_deps_migration.yaml` | `deps.py` |
| 4 | TASK_04_02 | `PLAN_01_08_graphs_migration.yaml` | `graphs.py` |
| 4 | TASK_04_03 | `PLAN_01_09_users_migration.yaml` | `users.py` |
| 4 | TASK_04_04 | `PLAN_01_10_layouts_migration.yaml` | `layouts.py` |
| 4 | TASK_04_05 | `PLAN_01_11_remaining_routes_migration.yaml` | 10 route files |
| 5 | TASK_05_01 | `PLAN_01_12_frontend_error_types.yaml` | `api.types.ts`, `errorHandler.ts` |
| 5 | TASK_05_03 | `PLAN_01_14_error_message_maps.yaml` | 6 error message map files |
| 5 | TASK_05_02 | `PLAN_01_13_axios_interceptor_update.yaml` | `axiosInstance.ts` |
| 6 | TASK_06_01 | `PLAN_01_15_agents_md_update.yaml` | `AGENTS.md` |
| 6 | TASK_06_02 | `PLAN_01_16_error_format_docs.yaml` | `docs/08-security/error-format.md` |
| 6 | TASK_06_03 | `PLAN_01_17_error_handling_guide.yaml` | `docs/99-reference/error-handling-guide.md` |
| 7 | TASK_07_01 | `PLAN_01_18_verification.yaml` | (verification only) |

---

## 9. Success Criteria

Phase 01 is complete when ALL of the following are true:

1. **Zero** `raise HTTPException` sites remain in any route or deps file
2. All error responses across the API return RFC 7807 JSON with `code` and `details`
3. `ErrorCode(StrEnum)` is the single source of truth for all error codes
4. Frontend `extractApiError()` correctly parses both RFC 7807 and legacy formats
5. Users see localized Russian messages (not raw HTTP codes or English developer messages)
6. Token refresh flow, auth cookies, and rate limiting are unchanged
7. All `ruff`, `mypy`, `pytest`, and frontend build/lint checks pass
8. Documentation is updated (AGENTS.md, error-format.md, error-handling-guide.md)

---

## 10. Git Context

- **Current branch:** `feat/react`
- **Branch status:** Diverged from `origin/feat/react` (1 local commit, 1 remote commit)
- **Unstaged changes:** 3 files modified (`filter_transforms.py`, `types.py`, `data_worker.py`) — unrelated to this phase
- **Untracked:** `.ai/plans/`, `.ai/problems/decisions/`, `.ai/researches/` — this planning work

**Recommended commit strategy:**
- Commit each wave as it completes: `git add -A && git commit -m "feat(error-handling): wave N — <description>"`
- After all waves: `git push origin feat/react` (may need `--force-with-lease` due to divergence)

---

_Plan created: 2026-06-03_
_Validated: yes (1 revision iteration)_
_Total tasks: 18 across 7 waves_
_Estimated total effort: ~16-20 hours of autonomous agent work_
