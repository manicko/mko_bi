# Phase 04 Audit Findings — Security

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### SEC-001: No Token Revocation Mechanism — Deactivated Users Can Still Use Valid Tokens

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/deps.py`, `src/mkobi/core/security.py` |
| **Classification** | mandatory |

**Description:** The application uses stateless JWT tokens without any token revocation or blacklisting mechanism. When a user is deactivated (`is_active = false`), their existing JWT access tokens remain technically valid until the `exp` claim expires. The `get_current_user_dependency` in `deps.py` does check `is_active` at line 455-461, but this only protects access-token-based flows. If a token was issued just before deactivation, there is no way to invalidate it prematurely. The refresh token mechanism (httpOnly cookies) has no server-side storage to revoke either. The access token expiry defaults to only 15 minutes (configurable), and refresh tokens default to 7 days (10080 minutes), meaning a deactivated user could continue refreshing for up to 7 days.

**Evidence:**
- `src/mkobi/api/deps.py:405-487` — `get_current_user_dependency` checks `is_active` but cannot revoke existing valid tokens.
- `src/mkobi/core/security.py:299-337` — `decode_token()` only validates signature and `exp`. No revocation check.
- No token blacklist/blocklist table, no `jti` claim in JWT payload, no Redis-based token revocation store exists in codebase.
- `src/mkobi/core/security.py:211-256` — `create_access_token` does not include a `jti` (JWT ID) claim.

**Recommendation:** Implement a token denylist using Redis (already used for rate limiting). Add a `jti` claim to all tokens, store active `jti` values in Redis with TTL matching token expiry, and add a revocation endpoint that removes tokens from the allowlist. On user deactivation, revoke all outstanding tokens for that user. Alternatively, reduce refresh token lifetime significantly and implement sliding refresh with rotation.

---

### SEC-002: JWT Secret Key Stored as Default in `.env` File Committed alongside `.env.example` with Weak Values

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `.env`, `.env.example`, `docker/.env` |
| **Classification** | mandatory |

**Description:** The `.env` and `docker/.env` files contain weak default secret keys (`JWT__SECRET_KEY=dev-secret-key-for-local-development`, `DATABASE__PASSWORD=1234`, `MKOBI_APP_PASSWORD=dev_password`, `ADMIN_PASSWORD=admin@example.com`). While `.env` is listed in `.gitignore` (line 151), the `.env.example` file and `docker/.env` file both also contain these same weak values rather than empty/placeholder markers. The `.env.example` file explicitly says "change_me" but the actual `.env` contains production-configured services (real database, real Redis, real admin credentials). If a developer copies `.env.example` to `.env` without changing values — a common pattern — the system runs with trivially guessable secrets. The `docker/.env` file also ships with these defaults, and Docker Compose uses `${JWT__SECRET_KEY:?...}` enforcement only if an external `.env` overrides it; the `docker-compose.override.yml` uses `${JWT__SECRET_KEY:-dev-secret-key-for-local-development}` which provides a fallback.

**Evidence:**
- `C:\py_dev\mkobi\.env:19` — `JWT__SECRET_KEY=dev-secret-key-for-local-development`
- `C:\py_dev\mkobi\.env:11` — `DATABASE__PASSWORD=1234`
- `C:\py_dev\mkobi\.env:49` — `ADMIN_PASSWORD=admin@example.com`
- `C:\py_dev\mkobi\.env:52` — `MKOBI_APP_PASSWORD=dev_password`
- `C:\py_dev\mkobi\docker\.env` — same weak values duplicated
- `C:\py_dev\mkobi\docker\docker-compose.override.yml:21` — `JWT__SECRET_KEY: ${JWT__SECRET_KEY:-dev-secret-key-for-local-development}`
- `src/mkobi/config.py:127` — `secret_key: str | None = None` — default is None but no entropy validation

**Recommendation:** Ensure `.env` is never committed (already in .gitignore — verify). Change `docker/.env` to have empty/no values (use `${VAR:?error}` pattern everywhere with no fallbacks). Add entropy validation for JWT secret key at startup — reject keys shorter than 32 bytes or keys matching known weak patterns. Use a startup check that prevents running in production with default/weak secrets.

---

### SEC-003: `dashboards_crud.py` Update and Delete Endpoints Missing Resource-Level Access Control

| Field | Value |
|-------|-------|
| **ID** | SEC-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/dashboards_crud.py` |
| **Classification** | mandatory |

**Description:** The dashboard update (`PUT /dashboards/{dashboard_id}`) and delete (`DELETE /dashboards/{dashboard_id}`) endpoints in `dashboards_crud.py` enforce only global admin role via `dependencies=[Depends(require_admin_role)]` (lines 282, 351), but they do NOT verify that the admin user has dashboard-level admin permission. While global admins bypass all checks in `check_dashboard_access` (line 178 of `permissions.py`), the route-level dependency `require_admin_role` checks the `user.role == UserRole.ADMIN` in `deps.py:507`. However, the dashboard-level operations should also verify dashboard-specific admin permission at the service layer. The update endpoint calls `dashboard_service.update_dashboard()` without passing any user context, so any global admin can update/delete any dashboard without restriction. This is an IDOR risk in scenarios where roles might be extended in the future (e.g., dashboard-specific admins who are not global admins).

**Evidence:**
- `src/mkobi/api/routes/dashboards_crud.py:276-342` — `update_dashboard_endpoint` uses `require_admin_role` dependency and passes no user_id to service.
- `src/mkobi/api/routes/dashboards_crud.py:346-396` — `delete_dashboard_endpoint` uses `require_admin_role` dependency and passes no user_id to service.
- Compare with `src/mkobi/api/routes/graphs.py:286-353` — graph update properly checks `check_dashboard_access` with `required_permission="admin"` per-resource.
- `src/mkobi/services/dashboard_service.py:318-330` — `update_dashboard` does not accept or validate user context.

**Recommendation:** Add dashboard-level admin access verification in the update and delete endpoints by checking `require_dashboard_admin_access` dependency or calling `check_dashboard_access` with `required_permission="admin"` before performing the operation.

---

### SEC-004: Admin Approval Endpoint Returns Plain-Text Temporary Password in HTTP Response

| Field | Value |
|-------|-------|
| **ID** | SEC-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/admin.py`, `src/mkobi/services/auth_service.py` |
| **Classification** | mandatory |

**Description:** Both the admin password reset endpoint (`POST /admin/users/{user_id}/reset-password`) and the registration request approval endpoint (`POST /admin/registration-requests/{request_id}/approve`) return temporary plaintext passwords directly in the HTTP JSON response. The `reset_password_admin` function in `auth_service.py` generates the password via `_generate_temp_password()` and returns it as `temp_password` in the response dict (line 580). Similarly, the approval endpoint generates a temp password and returns it at line 258. These passwords are also securely generated using `secrets` module, but transmitting them in HTTP responses means they appear in server logs, browser history, proxy logs, and any intermediate TLS-terminating proxies.

**Evidence:**
- `src/mkobi/services/auth_service.py:563-580` — `reset_password_admin` returns `{"message": ..., "user_id": ..., "temp_password": temp_password}`.
- `src/mkobi/api/routes/admin.py:255-258` — approval endpoint returns `{"message": "Registration request approved", "user_id": ..., "temp_password": temp_password}`.
- `src/mkobi/services/auth_service.py:233-234` — login user endpoint does NOT return password (handles it properly with cookie-based refresh token).

**Recommendation:** Do not return temporary passwords in HTTP response bodies. Instead, send the temporary password via a separate secure channel (e-mail, or a one-time link that displays it). If it must be in the response, ensure it's masked or truncated (e.g., show only last 4 chars) and mandate immediate password change (which is already done via `force_password_change=True`).

---

### SEC-005: Missing HSTS and Content-Security-Policy Headers

| Field | Value |
|-------|-------|
| **ID** | SEC-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/app.py`, `docker/nginx/nginx.conf` |
| **Classification** | advisory |

**Description:** The application sets some security headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`) both in the FastAPI middleware (`app.py:67-71`) and in nginx (`nginx.conf:17-20`), but is missing two critical headers: `Strict-Transport-Security` (HSTS) and `Content-Security-Policy` (CSP). HSTS ensures browsers always use HTTPS for the domain, preventing SSL stripping attacks. CSP prevents XSS by restricting which scripts/styles can execute. Both the app middleware and the nginx config lack these headers.

**Evidence:**
- `src/mkobi/app.py:46-72` — `SecurityHeadersMiddleware` dispatches `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` but no `Strict-Transport-Security` or `Content-Security-Policy`.
- `C:\py_dev\mkobi\docker\nginx\nginx.conf:17-20` — Same four headers, missing HSTS and CSP.
- No occurrence of `Strict-Transport`, `HSTS`, `Content-Security-Policy`, or `CSP` in any source file.

**Recommendation:** Add `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` header. Add a `Content-Security-Policy` header appropriate for the frontend (e.g., `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'`). Configure both in the FastAPI middleware and in nginx for defense-in-depth.

---

### SEC-006: JWT Secret Key Has No Entropy or Strength Validation

| Field | Value |
|-------|-------|
| **ID** | SEC-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/config.py`, `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** The `JWTSettings` model in `config.py` defines `secret_key: str | None = None` with no validation for key strength or entropy. The only check in `app.py` at line 151-153 verifies that it is not `None` in production (`raise ValueError("JWT_SECRET_KEY must be set")`), but does not validate key length or complexity. A weak key like `"secret"` or `"dev"` would pass this check. The `admin_password` validator in `config.py:286-301` checks against common weak passwords, but no equivalent check exists for the JWT secret key.

**Evidence:**
- `src/mkobi/config.py:124-130` — `JWTSettings` model with `secret_key: str | None = None` and no validator.
- `src/mkobi/app.py:151-153` — Only checks `if not config.jwt.secret_key`.
- `src/mkobi/config.py:17-18` — `WEAK_PASSWORDS` list defined for admin passwords but not for JWT secret.

**Recommendation:** Add a validator to `JWTSettings` that enforces minimum key length (at least 32 bytes for HS256) and checks against common weak values. In production mode, raise `ValueError` if the key doesn't meet minimum entropy requirements. Document that keys should be generated with `openssl rand -hex 32`.

---

### SEC-007: `document.cookie` Access for Refresh Token — Token Exposed to XSS via Non-HttpOnly Fallback

| Field | Value |
|-------|-------|
| **ID** | SEC-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/core/security.py`, `src/mkobi/api/routes/auth.py` |
| **Classification** | advisory |

**Description:** The refresh token is set as an httpOnly cookie (line 396 in `security.py`), which is good practice as it prevents JavaScript access via `document.cookie`. However, the cookie is set with `secure=config.app.cookie_secure` (line 397), and `cookie_secure` defaults to `True` in the `AppSettings` model (`config.py:148`). While the app-level default is correct, this is only safe in production if TLS is enforced. The `validate_refresh_token` endpoint (`refresh` in `auth.py:247-309`) reads the token from `request.cookies.get(COOKIE_NAME)` which is correct. However, the cookie's `samesite` is set to `"strict"` which may cause issues with legitimate cross-origin navigation (e.g., following links from external sites).

**Evidence:**
- `src/mkobi/core/security.py:393-400` — `set_secure_cookie` uses `httponly=True`, `secure=config.app.cookie_secure`, `samesite="strict"`.
- `src/mkobi/config.py:148` — `cookie_secure: bool = True` — good default.

**Recommendation:** Change `samesite` from `"strict"` to `"lax"` to allow legitimate cross-origin GET requests while still preventing CSRF on POST requests. Add a CSRF token for state-changing operations (POST/PUT/DELETE) as an additional defense layer even with SameSite cookies.

---

### SEC-008: Dashboard Data Endpoint Missing Resource-Level Access Control for Shared Dashboards

| Field | Value |
|-------|-------|
| **ID** | SEC-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/data_service.py` |
| **Classification** | advisory |

**Description:** The `get_aggregated_data` flow in `data_service.py:169-220` does not verify dashboard access at the service layer. Access control is enforced in the route handler (`data.py:86-100`) which calls `check_dashboard_access`, but the service method itself has no protection. If any other part of the codebase calls `data_service.get_aggregated_data()` directly without first checking access in the route, data could be leaked. The service layer should enforce defense-in-depth. Similarly, `get_available_metrics` and `get_available_dimensions` (lines 222-254) have no access checks at all at any layer.

**Evidence:**
- `src/mkobi/services/data_service.py:169-220` — `get_aggregated_data` with no access check, only accepts `dashboard_id` and `graph_id`.
- `src/mkobi/services/data_service.py:222-254` — `get_available_metrics` and `get_available_dimensions` have zero access control.
- `src/mkobi/api/routes/data.py:86-100` — Route handler does check access, but this is the only layer.

**Recommendation:** Add optional `user_id` and `user_role` parameters to data service methods and verify dashboard access within the service layer as defense-in-depth. At minimum, document that all callers must verify access before calling these methods.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 3 |
| LOW | 2 |

## Mandatory Fixes

- **SEC-001**: Implement token revocation mechanism (e.g., Redis denylist with `jti` claim).
- **SEC-002**: Remove weak default secrets from `docker/.env`, add entropy validation for JWT secret key.
- **SEC-003**: Add resource-level access control (dashboard admin permission) to dashboard update and delete endpoints.
- **SEC-004**: Stop returning plaintext temporary passwords in HTTP response bodies.

## Advisory Recommendations

- **SEC-005**: Add HSTS and CSP security headers at both app and nginx layers.
- **SEC-006**: Add strength/entropy validation to JWT secret key configuration.
- **SEC-007**: Change cookie `samesite` from `strict` to `lax`, add CSRF tokens for state-changing operations.
- **SEC-008**: Add defense-in-depth access control in data service layer.

## Doc Updates Needed

- Update `docs/08-security/security-overview.md` to document token revocation strategy.
- Update `docs/10-deployment/deployment.md` to include CSP and HSTS header configuration in nginx.
