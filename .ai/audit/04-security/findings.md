# Phase 04 Audit Findings — Security

**Executor:** audit-executor
**Template:** `.ai/audit/templates/audit-findings.md`
**Status:** complete
**Validated:** no

---

## Findings

### SEC-001: Hardcoded Development Secrets Committed to Repository

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `.env`, `docker/.env` |
| **Classification** | mandatory |

**Description:** Production-equivalent secret values are committed to the repository in both `.env` and `docker/.env` files. The JWT secret key `dev-secret-key-for-local-development` and admin credentials `admin@example.com` with weak password are present in tracked files. This violates the security principle that secrets should not be in version control and creates a risk if these files are deployed to production without modification.

**Evidence:**
- File `.env` lines 19, 48-49, 52:
  ```
  JWT__SECRET_KEY=dev-secret-key-for-local-development
  ADMIN_USERNAME=admin@example.com
  ADMIN_PASSWORD=admin@example.com
  MKOBI_APP_PASSWORD=dev_password
  ```
- File `docker/.env` lines 19, 48-49, 52: identical values
- File `docker/.env.example` lines 20, 53, 56 show the expectation for secrets to be changed in production

**Recommendation:** Remove `.env` and `docker/.env` from version control (add to `.gitignore` if not already). Ensure deployment documentation requires setting `JWT__SECRET_KEY` with a cryptographically strong value (e.g., `openssl rand -hex 32`). The `.env.example` file is correctly configured as a template with placeholder values.

---

### SEC-002: JWT Tokens Not Revoked on User Deactivation

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/security.py`, `src/mkobi/api/deps.py`, `src/mkobi/db/repositories/user_repo.py`, `src/mkobi/db/models/user.py` |
| **Classification** | mandatory |

**Description:** The `User` model has an `is_active` field (line 60 in `user.py`) but this field is never checked during JWT token validation or user authentication. If a user is deactivated (is_active=False), their existing JWT tokens remain valid and they can continue to access the system. This is a critical authentication bypass vulnerability.

**Evidence:**
- File `src/mkobi/db/models/user.py` line 60: `is_active: Mapped[bool]` field exists
- File `src/mkobi/core/security.py` lines 299-337: `decode_token()` and `validate_refresh_token()` do not check user status
- File `src/mkobi/api/deps.py` lines 419-451: `get_current_user_dependency()` does not verify `is_active` status
- File `src/mkobi/db/repositories/user_repo.py` line 90: `get_by_email_with_hash()` returns user without checking `is_active`

**Recommendation:** Add `is_active` check in `get_current_user_dependency()` after fetching user, and in `get_by_email_with_hash()`. Return 401 for inactive users. Consider implementing a token blacklist/revocation mechanism for immediate token invalidation upon deactivation.

---

### SEC-003: Missing IDOR Protection on Graph Endpoints

| Field | Value |
|-------|-------|
| **ID** | SEC-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/graphs.py`, `src/mkobi/services/graph_service.py` |
| **Classification** | mandatory |

**Description:** The `/graphs/{graph_id}` endpoint (and the `/graphs/` list endpoint) use only `CurrentUser` authentication without verifying that the user has access to the dashboard that owns the graph. This allows any authenticated user to access any graph by ID, potentially exposing data from dashboards they don't have permission to view.

**Evidence:**
- File `src/mkobi/api/routes/graphs.py` lines 135-180: `get_graph_endpoint()` uses `CurrentUser` dependency (line 144) but never checks dashboard access
- File `src/mkobi/api/routes/graphs.py` lines 98-132: `get_graphs_endpoint()` lists all graphs without dashboard access control
- No call to `check_dashboard_access()` exists in either endpoint
- The `data.py` endpoint correctly implements IDOR protection (lines 79-93) by checking dashboard access

**Recommendation:** Add dashboard access verification to all graph endpoints. For `get_graph_endpoint()`, fetch the graph, extract dashboard_id from it, then verify user has "view" access before returning data. For `get_graphs_endpoint()`, either restrict to admin-only or filter by user-accessible dashboards.

---

### SEC-004: Missing IDOR Protection on Layout Endpoints

| Field | Value |
|-------|-------|
| **ID** | SEC-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/layouts.py` |
| **Classification** | mandatory |

**Description:** Layout endpoints use only `CurrentUser` authentication without verifying dashboard ownership. Users can enumerate and view layouts for dashboards they don't have access to, potentially exposing sensitive configuration information.

**Evidence:**
- File `src/mkobi/api/routes/layouts.py` lines 103-139: `get_layouts_endpoint()` uses `CurrentUser` but lists all layouts without access control
- File `src/mkobi/api/routes/layouts.py` lines 142-188: `get_layout_endpoint()` uses `CurrentUser` but doesn't verify dashboard association
- No call to `check_dashboard_access()` in either endpoint
- Layout model has `dashboard_id` field that should be used for access verification

**Recommendation:** Add dashboard access verification for layout endpoints. Since layouts are associated with dashboards via `layout_id` in dashboard creation, verify that the user has access to the relevant dashboard before returning layout data.

---

### SEC-005: Rate Limiting Silently Disabled on Redis Failure

| Field | Value |
|-------|-------|
| **ID** | SEC-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/data_service.py`, `src/mkobi/core/security.py` |
| **Classification** | mandatory |

**Description:** Rate limiting defaults to `fail_closed=False` (line 283 in `config.py`). When Redis is unavailable, the rate limiter silently disables rate limiting instead of blocking requests. This allows unlimited upload attempts during a Redis outage, potentially enabling brute-force or DoS attacks.

**Evidence:**
- File `src/mkobi/config.py` line 283: `rate_limiter_fail_closed: bool = Field(default=False, ...)`
- File `src/mkobi/services/data_service.py` lines 54-71: On Redis error, rate limiter becomes `None` and logs warning "Rate limiter disabled - uploads will not be rate-limited"
- File `src/mkobi/core/security.py` lines 64-77: `RateLimiter.check_rate_limit()` returns `True` (allow) when Redis fails and `fail_closed=False`

**Recommendation:** Consider setting `RATE_LIMITER_FAIL_CLOSED=true` for production environments to ensure security is maintained during infrastructure failures. Alternatively, implement exponential backoff or in-memory fallback rate limiting.

---

### SEC-006: Missing Security Headers in Application Layer

| Field | Value |
|-------|-------|
| **ID** | SEC-006 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** The FastAPI application does not set security headers (Content-Security-Policy, Strict-Transport-Security, X-Content-Type-Options beyond CORS). Security headers are only set in the optional nginx reverse proxy (lines 17-19 in `docker/nginx/nginx.conf`). If nginx is not used, the application lacks these protections.

**Evidence:**
- File `src/mkobi/app.py`: No middleware for security headers
- File `docker/nginx/nginx.conf` lines 17-19 set `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`
- CSP and HSTS headers are missing in both application and nginx config

**Recommendation:** Add security headers middleware to the FastAPI application for defense-in-depth. At minimum, add `X-Content-Type-Options: nosniff` and `X-Frame-Options: SAMEORIGIN` to the application. For nginx, add `Strict-Transport-Security` header if HTTPS is enforced.

---

### SEC-007: Upload Endpoint Missing Dashboard Existence Verification

| Field | Value |
|-------|-------|
| **ID** | SEC-007 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `src/mkobi/services/data_service.py` |
| **Classification** | advisory |

**Description:** While the upload endpoint checks dashboard access via `check_dashboard_access`, it does not verify that the dashboard exists before checking access. This could lead to timing differences that might leak information about dashboard existence, and may produce confusing error messages.

**Evidence:**
- File `src/mkobi/api/routes/upload.py` line 51-58: `upload_file_endpoint()` uses `EditorUser` but the function `_execute_upload` in `data_service.py` only checks access (lines 117-131)
- No explicit check for dashboard existence before access check in the service layer

**Recommendation:** Add explicit dashboard existence check before access verification to provide clearer error messages and prevent potential timing attacks. Return 404 for non-existent dashboards and 403 only for existing dashboards with insufficient access.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 3 |
| MEDIUM | 2 |
| LOW | 0 |

## Mandatory Fixes

- SEC-001: Remove hardcoded secrets from tracked `.env` files
- SEC-002: Implement user `is_active` check during JWT authentication
- SEC-003: Add dashboard access verification to graph endpoints
- SEC-004: Add dashboard access verification to layout endpoints

## Advisory Recommendations

- SEC-005: Enable fail-closed rate limiting in production
- SEC-006: Add security headers middleware to FastAPI application
- SEC-007: Add dashboard existence verification before access checks on upload endpoint