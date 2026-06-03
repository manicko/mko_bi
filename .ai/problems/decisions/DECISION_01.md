# Phase 1: Error Handling Standardization — Decisions

**Gathered:** 2026-06-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Standardize **all** API error responses across the entire backend into a single structured format with machine-readable codes, and build a unified frontend error handling system so users see meaningful, localized, process-specific messages instead of raw HTTP codes (`419`, `undefined`, `Network Error`).

This covers:
1. Backend — `ErrorCode(StrEnum)`, `AppException` as the single error path, RFC 7807-inspired response format
2. Frontend — shared error extractor utility, per-feature localized error message maps, toast + inline display strategy
3. Research deliverable — mapped error zones per route group with specific refactoring scope

NOT covered: adding new validation rules, changing business logic, rate limiter redesign, i18n framework integration.
</domain>

<decisions>
## Implementation Decisions

### Error Response Format (Backend)

- **RFC 7807 Problem Details, extended** with `code` and `details`:
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
- `type`: URI-style error type for documentation/reference
- `title`: Short human-readable summary
- `status`: HTTP status code (integer)
- `detail`: Developer-facing message (English, for logging/debug)
- `code`: Machine-readable `ErrorCode(StrEnum)` value — the contract between backend and frontend
- `details`: Optional structured context (e.g., `max_size_mb`, `column`, `allowed_types`)

### Error Codes

- All error codes defined centrally in a new `ErrorCode(StrEnum)` enum
- Codes follow `UPPER_SNAKE_CASE` convention: `MISSING_COLUMN`, `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`, `INVALID_ENCODING`, `RATE_LIMITED`, etc.
- Shared with frontend via OpenAPI spec generation (existing project pipeline)
- `ErrorResponse` Pydantic model updated to match RFC 7807 shape

### Backend Error Path

- **`AppException` is the single error-raising mechanism** — all `raise HTTPException(...)` calls (currently 319 sites) replaced with `raise AppException(status_code=..., code=ErrorCode.X, detail="...")`
- `AppException` constructor updated to accept `code: ErrorCode` and `details: dict | None`
- Existing `AppException` subclasses (`FileUploadException`, `ValidationException`, etc.) refactored to use `ErrorCode`
- Global exception handler in `add_exception_handlers()` updated to produce RFC 7807 shape
- `StarletteHTTPException` handler updated to produce same format (wraps `HTTP_XXX` codes)

### Frontend Error Extraction

- **Shared utility function** `extractApiError()` in `shared/api/errorHandler.ts`:
  - Input: `unknown` (caught error)
  - Output: `{ type, title, status, detail, code, details }` — always returns a valid object
  - Extraction chain: Axios error → `error.response.data` → fallback to `error.message` → generic message
  - Handles both new RFC 7807 format and legacy `FastAPI` validation format (with `errors` array)

### Frontend Display Strategy

- **Toast** (`react-hot-toast`) for all API-level errors — displayed in the axios response interceptor globally
- **Inline** (form-level) for field validation errors — displayed per-component
- **Per-feature localized error message maps**: each feature (`upload`, `auth`, `admin`, `dashboards`) maintains its own `errorMessages` map: `Record<ErrorCode, string>`
- Resolution order:
  1. Look up `error.code` in feature's message map → display localized Russian text
  2. Unknown code → display `error.detail` (backend English message)
  3. No detail → display generic fallback ("Произошла ошибка")
- `details` object values appended to message smartly (e.g., `"Размер файла превышает допустимый. Максимальный размер: 100 МБ."`)

### Frontend Type Safety

- `ApiError` interface exported from `shared/types/api.types.ts` matching RFC 7807 shape
- `ErrorCode` type generated from OpenAPI spec (`StrEnum` → TypeScript union type)
- `extractApiError()` returns typed `ApiError`, never `any`

### Error Layers

Three-tier error architecture:
1. **L1 — Client-side pre-validation** (React): file size, extension, required fields — no network request, instant feedback
2. **L2 — API transport errors**: HTTP status codes, network failures, rate limiting, auth errors — handled by axios interceptor
3. **L3 — Business logic errors**: missing columns, invalid data, processing failures — displayed in context (upload queue, form fields)

### Migration Scope (All Zones)

Research phase must map all error zones. Phase 1 refactors **all** zones:
- `upload.py` — file upload & processing errors
- `auth.py` / `deps.py` — authentication & authorization errors
- `dashboards_crud.py` — dashboard CRUD errors
- `admin.py` — admin panel errors
- `filter_values.py` — filter data errors
- `data.py` / service layer — data processing & aggregation errors

Each zone is a separate planning task. Research produces the error inventory per zone.

### Axios Interceptor Behavior

- Existing interceptor in `axiosInstance.ts` preserves 401/403/session handling logic
- Add generic error handler at the end: non-401/403 errors → extract message → `toast.error(localizedMessage)`
- Login endpoint errors are still skipped (handled inline by `LoginForm`)

### Coding Standards & Documentation Update

This decision requires a dedicated documentation task. The following standards must be codified in project docs and enforced for all future code:

**Backend — Raising errors:**
- Always use `raise AppException(code=ErrorCode.X, detail="...", status_code=..., details={...})` — never `raise HTTPException(...)` in route/service code
- `detail` is a clear English developer-facing message (frontend fallback). Never include stack traces, raw exception text, or internal paths
- `details` contains structured context: column names, field names, max values, allowed values — anything useful for the frontend to display
- Every new error condition gets a new `ErrorCode(StrEnum)` entry — no ad-hoc string codes
- Service layer raises `AppException` — routes only catch and re-raise (no `HTTPException` in services)
- Validation errors from Pydantic models are handled by `validation_exception_handler` — routes don't catch them

**Backend — Error handler registration:**
- Global exception handlers in `app.py` and `add_exception_handlers()` are the only place that produces HTTP error responses
- No manual `JSONResponse` with error shapes in route code

**Frontend — Handling errors:**
- For automatic toast display: rely on the axios interceptor — no `try/catch` needed
- For inline form errors: `try/catch` → `extractApiError()` → set field error state from `code` + `details`
- Never show raw `error.message` to the user — always resolve through the error message map
- L1 client-side validation (file size, extension, required fields) uses Zod or inline checks — messages are hardcoded in the component

**Frontend — Adding new error codes:**
- When backend adds a new `ErrorCode(StrEnum)` entry, the corresponding frontend feature `errorMessages` map MUST be updated with a localized string
- Graceful degradation: unmapped code falls back to `error.detail` (backend English message)

**Documentation files to update (dedicated task in plan):**
- `AGENTS.md` — new section: "Error Handling" covering backend raising rules + frontend handling rules
- `docs/08-security/` — document RFC 7807 error response format as part of the API contract
- `docs/99-reference/` — add error handling guide: ErrorCode enum, AppException usage, frontend interceptor pattern, L1/L2/L3 layered approach

### KiloCode's Discretion

- Exact Russian text for error message maps (KiloCode writes these, user reviews)
- `type` URI format (domain path after `https://api.mkobi.com/errors/`)
- Order and grouping of error codes within `ErrorCode(StrEnum)`
- Exact formatting of `details` values in appended messages (position, punctuation)
- Component placement for inline error display (which components show errors inline vs toast only)
- Exact structure of per-feature error message map files (naming, location pattern)
</decisions>

<specifics>
## Specific Ideas

- Current broken state: shows `Error: undefined`, raw status codes like `419`, `Network Error`, `Request failed with status code 422`
- Target state: "В файле отсутствует обязательная колонка." instead of "Required column 'TVR' is missing."
- `details` values should be appended naturally to Russian messages (not just dumped as JSON)
- The project already generates OpenAPI from Pydantic — `ErrorCode(StrEnum)` should flow through to a TypeScript type automatically
- Existing `ErrorResponse` model (`error`, `detail`, `code` at top level) needs to be restructured to nested RFC 7807 shape
- Existing `AppException` subclasses need not be deleted — they can set default `ErrorCode` values
- React error display uses MUI components (the project standard)
</specifics>

<deferred>
## Deferred Ideas

- i18n framework integration (react-i18next, etc.) — future phase. Currently hardcoded Russian strings in message maps.
- Error tracking/analytics integration (Sentry, etc.) — future phase. `code` and `details` are already structured for this.
- Automatic retry logic for transient errors (network timeout, 503) — future phase.
- User-facing error ID for support ticket reference — could add `error_id` field to response in future.
- Batch/multi-error responses (multiple errors in one request) — future phase. Currently single error per response.

---

_Phase: 01-error-handling_
_Context gathered: 2026-06-03_
