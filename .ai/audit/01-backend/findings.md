# Phase 01 Audit Findings — Backend Architecture

**Executor:** audit-executor
**Template:** .kilo/commands/audit/phases/01-audit-backend.md
**Status:** complete
**Validated:** no

---

## Findings

### BE-001: HTTPException raised directly violating project error handling rules

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/utils/time_utils.py |
| **Classification** | mandatory |

**Description:** `time_utils.py` raises `HTTPException` directly from FastAPI in two places, violating the project rule: "Do NOT raise `HTTPException` directly — always use `AppException` with `ErrorCode` enum." This bypasses the centralized RFC 7807 error handling pipeline, producing non-standard error responses that lack the `code`, `type`, and `title` fields required by the specification.

**Evidence:**
- `src/mkobi/utils/time_utils.py:9` — `from fastapi import HTTPException`
- `src/mkobi/utils/time_utils.py:108` — `raise HTTPException(status_code=400, detail=f"Invalid date format: {date_string}")`
- `src/mkobi/utils/time_utils.py:149` — `raise HTTPException(status_code=400, detail=f"Invalid ISO date format: {date_string}")`

**Recommendation:** Replace `HTTPException` with `AppException(code=ErrorCode.VALIDATION_ERROR, detail=...)` and remove the FastAPI `HTTPException` import. This ensures all error responses follow the RFC 7807 format with consistent `code`, `type`, `title`, and `status` fields.

---

### BE-002: Dead code — unused functions in permissions.py

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/core/permissions.py |
| **Classification** | advisory |

**Description:** Three functions in `permissions.py` are defined but never invoked anywhere in production code or tests: `get_current_user()` (line 265), `_get_current_user_with_session()` (line 287), and `_decode_token_cached()` (line 248). These duplicate logic already present in `deps.py::get_current_user_dependency()`. None are referenced in `docs/SPEC.md` or by any Pydantic model, so this is genuine dead code (not a spec deviation).

**Evidence:**
- `src/mkobi/core/permissions.py:248` — `_decode_token_cached` — `@lru_cache(maxsize=1000)` decorated function, never called from any import site
- `src/mkobi/core/permissions.py:265` — `get_current_user` — async function, never imported outside the module
- `src/mkobi/core/permissions.py:287` — `_get_current_user_with_session` — private async function, only called by dead `get_current_user`
- Grep for `from mkobi.core.permissions import.*get_current_user` returns zero matches in `src/` and `tests/`
- The actual auth flow uses `deps.py::get_current_user_dependency` which calls `core/security.py::decode_token` directly

**Recommendation:** Remove `get_current_user`, `_get_current_user_with_session`, and `_decode_token_cached` from `permissions.py`. The `lru_cache` on `_decode_token_cached` would also bypass token revocation if it were ever accidentally used, making its removal doubly beneficial.

---

### BE-003: Private attribute access across layer boundary in auth route

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/auth.py, src/mkobi/services/auth_service.py |
| **Classification** | mandatory |

**Description:** The `_handle_login` function in the auth route accesses `auth_service._rate_limiter` (a private attribute of `AuthService`) to perform rate limiting directly in the transport layer. This violates the "No Business Logic in Transport" invariant: the route handler decides rate-limiting logic (key construction, max_attempts, TTL) by reaching into the service's private internals. Additionally, the `_rate_limiter` prefix convention signals this is an implementation detail that may change without notice.

**Evidence:**
- `src/mkobi/api/routes/auth.py:77` — `rate_limiter = auth_service._rate_limiter`
- `src/mkobi/api/routes/auth.py:78-85` — Rate limit check with `rate_limiter.check_rate_limit(f"login:{client_ip}", max_attempts=5, ttl=300)`
- The route constructs the rate limit key and parameters itself rather than delegating to the service

**Recommendation:** Either (a) expose a public `check_login_rate_limit(client_ip: str) -> bool` method on `AuthService` that encapsulates the rate-limiting logic, keeping it in the service layer; or (b) create the rate limiter independently in the route (as done in `upload.py` and `register_request`), removing the private attribute dependency. Option (a) is cleaner and better encapsulated.

---

### BE-004: Client error endpoint lacks rate limiting — log flood risk

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/api/routes/client_errors.py |
| **Classification** | advisory |

**Description:** The `POST /api/v1/client-errors` endpoint is intentionally unauthenticated (to receive errors from unauthenticated frontend states) but has no rate limiting. An attacker can flood this endpoint with requests, causing excessive log writes that consume disk space and degrade monitoring signal quality (log injection / log flooding attack).

**Evidence:**
- `src/mkobi/api/routes/client_errors.py:29-35` — `report_client_error` endpoint has no `Depends()` for authentication and no `AsyncRateLimiter` check
- Description explicitly states "No authentication required" (line 33)
- Every other public-facing endpoint (`/auth/register-request`, `/auth/login`) applies rate limiting

**Recommendation:** Add IP-based rate limiting to the client error endpoint (e.g., `max_attempts=30, ttl=60`) to prevent abuse while allowing legitimate error reporting. This follows the same pattern used in `auth.py` for the registration request endpoint.

---

### BE-005: Inline Pydantic model in route file breaks layer separation

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/api/routes/client_errors.py |
| **Classification** | advisory |

**Description:** `ClientErrorPayload` is defined directly inside `client_errors.py` instead of in the `src/mkobi/models/` package. All other request/response models across the codebase are defined in the models layer (`models/auth.py`, `models/data.py`, `models/user.py`, etc.). This inconsistency breaks the Clean Architecture invariant that transport layer should depend only on interface contracts and models, not define its own schemas.

**Evidence:**
- `src/mkobi/api/routes/client_errors.py:19-26` — `class ClientErrorPayload(BaseModel)` defined inline in route file
- Every other route imports its models from `mkobi.models.*`

**Recommendation:** Move `ClientErrorPayload` to `src/mkobi/models/` (e.g., a new `models/client_errors.py` or into `models/data.py`), then import it in the route. This maintains consistent layer separation across the codebase.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 1 |

## Mandatory Fixes

- **BE-001**: Replace `HTTPException` with `AppException(code=ErrorCode.VALIDATION_ERROR)` in `time_utils.py` to comply with RFC 7807 error handling specification.
- **BE-003**: Refactor `auth_service._rate_limiter` access in auth route — expose a public method on `AuthService` or create the rate limiter independently.

## Advisory Recommendations

- **BE-002**: Remove dead code (`get_current_user`, `_get_current_user_with_session`, `_decode_token_cached`) from `permissions.py`.
- **BE-004**: Add IP-based rate limiting to the client error endpoint to prevent log flooding.
- **BE-005**: Move `ClientErrorPayload` from route file to `src/mkobi/models/` package.

## Doc Updates Needed

None.
