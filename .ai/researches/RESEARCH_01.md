# RESEARCH_01: Error Handling Infrastructure Analysis

**Date:** 2026-06-03
**Scope:** Backend (FastAPI) + Frontend (React/TypeScript) error handling

---

## 1. Current Backend Error Infrastructure

### 1.1 AppException Hierarchy (`src/mkobi/utils/exceptions.py`)

```
Exception
├── AppException (base)
│   ├── NotFoundException (404, "NOT_FOUND")
│   ├── PermissionDeniedException (403, "PERMISSION_DENIED")
│   ├── ValidationException (400, "VALIDATION_ERROR")
│   └── FileUploadException (400, "FILE_UPLOAD_ERROR")
└── Exception (global catch-all handler)
```

**AppException attributes:**
- `status_code: int` (default: 500)
- `detail: str` (default: "Internal server error")
- `error_code: str` (default: "INTERNAL_ERROR")

### 1.2 ErrorResponse Model

```python
class ErrorResponse(BaseModel):
    error: str          # Human-readable message
    detail: str | None  # Additional detail (optional)
    code: str | None    # Machine-readable error code (optional)
    # model_config = {"extra": "allow"}  # Allows extra fields
```

### 1.3 Exception Handlers (`add_exception_handlers`)

Two handlers registered:

1. **`AppException` handler** — logs error, returns JSON with `error` and `code` fields
2. **`Exception` handler** (global) — logs error, returns generic 500 response with `INTERNAL_ERROR` code

### 1.4 Error Code Constants

**Current state:** Error codes are hardcoded strings scattered across the codebase.

**Existing error codes in AppException subclasses:**
- `INTERNAL_ERROR`
- `NOT_FOUND`
- `PERMISSION_DENIED`
- `VALIDATION_ERROR`
- `FILE_UPLOAD_ERROR`

**No centralized ErrorCode enum exists.**

---

## 2. Current Frontend Error Infrastructure

### 2.1 Axios Instance (`frontend/src/shared/axiosInstance.ts`)

**Request interceptor:**
- Adds JWT token with expiration check
- Removes expired tokens automatically

**Response interceptor handles:**
- **401 errors:** Token refresh flow with request queuing
  - Skips login endpoint (lets inline form handle errors)
  - Skips refresh endpoint (prevents infinite loops)
  - Queues concurrent requests during refresh
  - Redirects to `/login` on refresh failure
- **403 errors:** Shows toast "Access denied"
- **Other errors:** Rejects with error for component-level handling

### 2.2 Error Display

- Uses `react-hot-toast` for error notifications
- No centralized error type/interface for API errors
- No structured error code handling on frontend

### 2.3 Frontend Error Types

**Current state:** No dedicated error types in `api.types.ts` or `enums.ts`.

The `FileUploadStatus` enum exists but is unrelated to API error codes.

---

## 3. Per-Zone Gap Analysis

### 3.1 Upload Zone (`upload.py`)

**HTTPException count:** 16 raise sites

**Issues:**
- Uses `HTTPException` directly instead of `AppException` subclasses
- ValueError mapping via `_handle_value_error()` is fragile (string matching on error messages)
- Mixes `HTTPException` and `AppException` in same endpoint
- Inconsistent status codes: uses both `413_CONTENT_TOO_LARGE` and `413_REQUEST_ENTITY_TOO_LARGE`
- No error codes in responses (HTTPException doesn't support `error_code`)

**Error patterns:**
- File size validation: 413
- Rate limiting: 429
- MIME/Format validation: 415
- Generic validation: 422
- Permission denied: 403
- Not found: 404
- Server errors: 500

### 3.2 Auth Zone (`auth.py`)

**HTTPException count:** 16 raise sites

**Issues:**
- All errors use `HTTPException` directly
- No error codes in responses
- Inconsistent detail messages (some specific, some generic)
- Rate limiting returns 401 (should be 429)

**Error patterns:**
- Invalid credentials: 401
- Token issues: 401
- Validation errors: 422
- Rate limiting: 429 (but also 401 in some cases)
- Server errors: 500

### 3.3 Dashboards CRUD Zone (`dashboards_crud.py`)

**HTTPException count:** 14 raise sites

**Issues:**
- Mixes `HTTPException` and `PermissionDeniedException`
- No error codes in responses
- Inconsistent error messages

**Error patterns:**
- Not found: 404
- Permission denied: 403
- Validation errors: 422
- Server errors: 500

### 3.4 Admin Zone (`admin.py`)

**HTTPException count:** 20 raise sites

**Issues:**
- All errors use `HTTPException` directly
- No error codes in responses
- Inconsistent error messages

**Error patterns:**
- Not found: 404
- Validation errors: 422
- Conflict: 409
- Server errors: 500

### 3.5 Filter Values Zone (`filter_values.py`)

**HTTPException count:** 1 raise site

**Issues:**
- Minimal error handling
- Only catches generic Exception

### 3.6 Data/Services Zone (`data.py`)

**HTTPException count:** 6 raise sites

**Issues:**
- Mixes `HTTPException` and `DashboardPermissionError`
- No error codes in responses

**Error patterns:**
- Access denied: 403
- Not found: 404
- Invalid JSON: 422
- Server errors: 500

### 3.7 Other Route Files

| File | HTTPException Count |
|------|---------------------|
| `graphs.py` | 16 |
| `users.py` | 15 |
| `layouts.py` | 10+ |
| `dashboards_access.py` | 7 |
| `processing_configs.py` | 7 |
| `dashboards_filters.py` | 9 |
| `dashboards_graphs.py` | 4 |
| `processing_logs.py` | 3 |
| `deps.py` | 16 |
| `app.py` | 1 |

---

## 4. HTTPException Raise Sites Summary

**Total raise sites in `src/mkobi`:** 168

**Breakdown by file:**
- `upload.py`: 16
- `auth.py`: 16
- `admin.py`: 20
- `dashboards_crud.py`: 14
- `graphs.py`: 16
- `users.py`: 15
- `deps.py`: 16
- `layouts.py`: 10+
- `dashboards_filters.py`: 9
- `dashboards_access.py`: 7
- `processing_configs.py`: 7
- `data.py`: 6
- `dashboards_graphs.py`: 4
- `processing_logs.py`: 3
- `filter_values.py`: 1
- `app.py`: 1

**Status code distribution (approximate):**
- 500 (Internal Server Error): ~40%
- 404 (Not Found): ~20%
- 403 (Forbidden): ~15%
- 422 (Unprocessable Entity): ~15%
- 401 (Unauthorized): ~5%
- 409 (Conflict): ~3%
- 413/415/429: ~2%

---

## 5. Recommended ErrorCode Enum Structure

```python
# src/mkobi/models/enums.py (additions)

class ErrorCode(StrEnum):
    """Machine-readable error codes for API responses."""

    # General errors (1xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Authentication errors (2xx)
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    INVALID_TOKEN = "INVALID_TOKEN"
    REFRESH_TOKEN_REQUIRED = "REFRESH_TOKEN_REQUIRED"

    # Authorization errors (3xx)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCESS_DENIED = "ACCESS_DENIED"

    # Resource errors (4xx)
    NOT_FOUND = "NOT_FOUND"
    DASHBOARD_NOT_FOUND = "DASHBOARD_NOT_FOUND"
    GRAPH_NOT_FOUND = "GRAPH_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    FILTER_NOT_FOUND = "FILTER_NOT_FOUND"
    LAYOUT_NOT_FOUND = "LAYOUT_NOT_FOUND"
    PROCESSING_CONFIG_NOT_FOUND = "PROCESSING_CONFIG_NOT_FOUND"
    PROCESSING_LOG_NOT_FOUND = "PROCESSING_LOG_NOT_FOUND"
    REGISTRATION_REQUEST_NOT_FOUND = "REGISTRATION_REQUEST_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"

    # Validation errors (5xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    INVALID_ROLE = "INVALID_ROLE"
    INVALID_PERMISSION = "INVALID_PERMISSION"
    INVALID_JSON = "INVALID_JSON"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    PASSWORD_MISMATCH = "PASSWORD_MISMATCH"
    DASHBOARD_ID_MISMATCH = "DASHBOARD_ID_MISMATCH"

    # File upload errors (6xx)
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"

    # Conflict errors (7xx)
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    REGISTRATION_REQUEST_PENDING = "REGISTRATION_REQUEST_PENDING"
    REGISTRATION_REQUEST_ALREADY_PROCESSED = "REGISTRATION_REQUEST_ALREADY_PROCESSED"
    FILTER_ALREADY_BOUND = "FILTER_ALREADY_BOUND"
    FILTER_NOT_BOUND = "FILTER_NOT_BOUND"

    # Processing errors (8xx)
    PROCESSING_FAILED = "PROCESSING_FAILED"
    PROCESSING_IN_PROGRESS = "PROCESSING_IN_PROGRESS"
```

---

## 6. Migration Risks and Edge Cases

### 6.1 High-Risk Areas

1. **Upload endpoint (`upload.py`)**
   - Complex ValueError mapping logic
   - Multiple status codes for same error type
   - File cleanup in finally block must be preserved

2. **Auth endpoints (`auth.py`)**
   - Token refresh flow is critical
   - Rate limiting logic must be preserved
   - Cookie handling must remain unchanged

3. **Dependency injection (`deps.py`)**
   - 16 raise sites in auth/permission checks
   - Changes affect all endpoints using these dependencies

### 6.2 Edge Cases

1. **Mixed exception types in same endpoint**
   - Some endpoints catch both `HTTPException` and `AppException`
   - Must ensure proper exception chaining

2. **Inconsistent status codes**
   - Upload uses both `413_CONTENT_TOO_LARGE` and `413_REQUEST_ENTITY_TOO_LARGE`
   - Should standardize on one

3. **Error message exposure**
   - Some endpoints expose internal error messages (e.g., `str(e)`)
   - Should use generic messages for 500 errors

4. **Frontend error handling**
   - Frontend expects specific error structure
   - Must maintain backward compatibility during migration

5. **Concurrent request handling**
   - Token refresh queue must not be broken
   - Error responses must be consistent for queued requests

### 6.3 Migration Strategy Recommendations

1. **Phase 1: Add ErrorCode enum and update ErrorResponse**
   - Add `ErrorCode` StrEnum to `models/enums.py`
   - Update `ErrorResponse` to include `code` field prominently
   - No breaking changes

2. **Phase 2: Create AppException subclasses for common errors**
   - Add `AuthenticationException`, `AuthorizationException`, etc.
   - Update exception handlers to use new subclasses

3. **Phase 3: Migrate route files incrementally**
   - Start with low-risk files (e.g., `filter_values.py`)
   - Progress to medium-risk (e.g., `dashboards_crud.py`)
   - Finish with high-risk (e.g., `upload.py`, `auth.py`)

4. **Phase 4: Update frontend**
   - Add error code handling to axios interceptor
   - Create error code to message mapping
   - Update components to use structured error codes

---

## 7. Blockers

### 7.1 Technical Blockers

1. **No centralized error code registry**
   - Error codes are hardcoded strings
   - No single source of truth for error codes

2. **Inconsistent exception handling patterns**
   - Some files use `HTTPException`, others use `AppException`
   - No clear guidelines on when to use which

3. **Frontend-backend contract mismatch**
   - Frontend doesn't parse error codes
   - No structured error response handling on frontend

### 7.2 Process Blockers

1. **No error handling documentation**
   - No ADR or spec for error handling patterns
   - New developers have no guidance

2. **Test coverage gaps**
   - Error handling paths may not be fully tested
   - Migration could introduce regressions

---

## 8. Recommendations

### 8.1 Immediate Actions

1. **Create `ErrorCode` enum** in `models/enums.py`
2. **Document error handling patterns** in AGENTS.md or SPEC.md
3. **Standardize exception usage** across route files

### 8.2 Short-term Improvements

1. **Expand AppException hierarchy** with domain-specific exceptions
2. **Update all route files** to use AppException subclasses
3. **Add error code parsing** to frontend axios interceptor

### 8.3 Long-term Improvements

1. **Create error handling middleware** for common patterns
2. **Add error code to OpenAPI spec** for auto-generated docs
3. **Implement error code localization** support

---

## Appendix A: File Locations

| Component | File Path |
|-----------|-----------|
| AppException | `src/mkobi/utils/exceptions.py` |
| ErrorResponse | `src/mkobi/utils/exceptions.py` |
| Exception handlers | `src/mkobi/utils/exceptions.py` |
| Enums | `src/mkobi/models/enums.py` |
| Axios instance | `frontend/src/shared/axiosInstance.ts` |
| Frontend types | `frontend/src/shared/types/api.types.ts` |
| Frontend enums | `frontend/src/shared/types/enums.ts` |

## Appendix B: HTTPException Status Codes Used

| Status Code | Count (approx.) | Usage |
|-------------|-----------------|-------|
| 500 | ~65 | Generic server errors |
| 404 | ~30 | Resource not found |
| 403 | ~25 | Permission denied |
| 422 | ~25 | Validation errors |
| 401 | ~10 | Authentication failures |
| 409 | ~5 | Resource conflicts |
| 413 | ~4 | File too large |
| 415 | ~4 | Invalid file type |
| 429 | ~4 | Rate limit exceeded |
| 400 | ~2 | Bad request |

---

## RESEARCH COMPLETE
