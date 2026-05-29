---
name: 04-security
description: Security audit covering authentication, authorization, credential handling, input validation, and trust boundaries
agent: audit-executor
alwaysApply: false
---

# Phase 04 Audit Findings — Security

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### SEC-001: Missing Minimum Password Length Enforcement in Registration

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/auth.py`, `src/mkobi/services/auth_service.py` |
| **Classification** | mandatory |

**Description:** While the `validate_password()` utility function in `utils/validators.py` (line 145) enforces minimum password length of 8 characters, this validation is NOT applied during user registration in `auth_service.py`. The `register_user()` method (lines 115-168) does not validate password strength before hashing and storing. The `RegisterRequest` model uses a simple `str` type without any validator. This allows users to register with weak passwords like single characters.

**Evidence:**
- `src/mkobi/models/auth.py:99` - `password: str` with no field validator
- `src/mkobi/services/auth_service.py:115-168` - `register_user()` method performs no password validation
- `src/mkobi/utils/validators.py:145-180` - `validate_password()` exists but is NOT called during registration
- Compare to `config.py:292-301` which validates admin password strength in production

**Recommendation:** Add field validator to `RegisterRequest` model to enforce minimum password length using `validate_password()` or add explicit password validation in `register_user()` method before hashing.

---

### SEC-002: JWT Secret Key Accepts Default Algorithm Without Explicit Configuration

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/config.py`, `src/mkobi/core/security.py` |
| **Classification** | advisory |

**Description:** The JWT configuration uses `algorithm: str = "HS256"` as a default in `JWTSettings` (line 128 in `config.py`). While the algorithm IS explicitly used in token creation/verification, there's no validation or warning if a weak algorithm is configured. Additionally, `validate_refresh_token()` at line 355 in `security.py` silently returns None when `secret_key` is not configured instead of raising an error, which could lead to confusing behavior during testing.

**Evidence:**
- `src/mkobi/config.py:128` - Default algorithm set without validation
- `src/mkobi/core/security.py:355-358` - `validate_refresh_token()` returns None when secret_key is None instead of raising error

**Recommendation:** Consider adding algorithm validation to reject weak algorithms (e.g., "none") and ensure consistent error handling for missing JWT secret across all token functions.

---

### SEC-003: MIMETYPE Validation Can Be Bypassed by Missing Content-Type

| Field | Value |
|-------|-------|
| **ID** | SEC-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/data/loaders/validator.py`, `src/mkobi/services/file_processing.py` |
| **Classification** | mandatory |

**Description:** The `validate_mime_type()` function (lines 22-42 in `validator.py`) returns early (line 33) when `content_type is None`, effectively skipping MIME type validation. An attacker could potentially upload malicious files without a Content-Type header and bypass this security check. The file extension validation happens separately but MIME type should not be silently skipped.

**Evidence:**
- `src/mkobi/data/loaders/validator.py:31-33` - Returns without validation when content_type is None
- `src/mkobi/services/file_processing.py:78` - Calls `validate_mime_type()` which can be bypassed

**Recommendation:** Change the MIME type validation to reject requests with missing Content-Type header OR default to a safe validation behavior. At minimum, log a warning and consider the request suspicious.

---

### SEC-004: Security Headers Missing in FastAPI Response

| Field | Value |
|-------|-------|
| **ID** | SEC-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** Security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) are configured in nginx (lines 17-20 in `nginx.conf`) but are NOT added to FastAPI responses. If the application is accessed directly without nginx (e.g., during development or testing), these security headers are missing.

**Evidence:**
- `src/mkobi/app.py:108-285` - No security header middleware configured
- `docker/nginx/nginx.conf:17-20` - Security headers only in nginx, not in application

**Recommendation:** Add security headers middleware in FastAPI application using `starlette.middleware.base` or a library like `secure` to ensure headers are present regardless of deployment configuration.

---

### SEC-005: Temporary Passwords Generated with Insufficient Entropy

| Field | Value |
|-------|-------|
| **ID** | SEC-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/admin.py` |
| **Classification** | advisory |

**Description:** Temporary passwords for newly approved users are generated using `secrets.token_urlsafe(16)` (line 188 in `admin.py`). While `secrets.token_urlsafe` is cryptographically secure, 16 bytes (128 bits) produces approximately 22 base64 characters. This is considered secure, but modern best practices recommend longer passwords for temporary credentials.

**Evidence:**
- `src/mkobi/api/routes/admin.py:188` - `temp_password = secrets.token_urlsafe(16)`

**Recommendation:** Increase token length to 32 bytes for temporary passwords to provide stronger entropy and longer lifetime before potential brute-force attacks.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

- SEC-001: Missing minimum password length enforcement in registration
- SEC-003: MIME type validation can be bypassed by missing Content-Type header

## Advisory Recommendations

- SEC-002: JWT secret key accepts default algorithm without explicit validation
- SEC-004: Security headers missing in FastAPI response (present only in nginx)
- SEC-005: Temporary passwords generated with 16 bytes (acceptable but could be stronger)

## Verified Security Controls

The following security controls were verified as correctly implemented:

| Control | Status | Evidence |
|---------|--------|----------|
| Authentication required on protected endpoints | ✓ | `src/mkobi/api/deps.py:400-472` - `get_current_user_dependency` |
| Token validation at every trust boundary | ✓ | `src/mkobi/api/deps.py:400-472` - All endpoints use `CurrentUser` dependency |
| Token expiration enforced | ✓ | `src/mkobi/core/security.py:240-246` - `exp` claim added to all tokens |
| Invalid/missing tokens return 401 Unauthorized | ✓ | `src/mkobi/api/deps.py:421-427` - Raises 401 on invalid token |
| Credentials never stored in plaintext | ✓ | `src/mkobi/db/models/user.py:44-47` - `password_hash` column only |
| Credential comparison uses constant-time algorithm | ✓ | `src/mkobi/core/security.py:200` - bcrypt.checkpw() is constant-time |
| Authentication state managed securely | ✓ | `src/mkobi/core/security.py:375-400` - Secure cookies with HttpOnly, SameSite |
| Authorization checked on every protected resource | ✓ | `src/mkobi/api/deps.py:594-723` - Dashboard access dependencies |
| Role-based restrictions enforced | ✓ | `src/mkobi/core/permissions.py:85-119` - `check_role()` hierarchy check |
| Admin privileges follow least-privilege principle | ✓ | `src/mkobi/api/routes/admin.py:33-40` - Admin endpoints explicitly require admin |
| Existence vs access distinction (404 vs 403) | ⚠ | Uses 403 for both "not found" and "no access" in some cases |
| Authorization decisions centralized | ✓ | `src/mkobi/core/permissions.py:124-245` - Centralized `check_dashboard_access` |
| No hardcoded secrets in source code | ✓ | `src/mkobi/config.py:50-70` - `SecretsFileSource` supports file-based secrets |
| Secrets derived from environment variables | ✓ | `src/mkobi/config.py:368-374` - Priority order documented |
| Secret injection supports file-based secrets | ✓ | `src/mkobi/config.py:36-70` - `_FILE` suffix support implemented |
| Production refuses defaults or test credentials | ✓ | `src/mkobi/config.py:292-309` - Validates admin credentials in production |
| JWT signing key is cryptographically strong | ✓ | No weak keys enforced (relies on user configuration) |
| Algorithm explicitly configured | ✓ | `src/mkobi/core/security.py:250-254` - Uses `config.jwt.algorithm` |
| All external input validated before processing | ✓ | Pydantic models in all route handlers |
| File uploads validated (MIME type, size, path traversal) | ⚠ | Path traversal prevented, but MIME type bypass possible (SEC-003) |
| SQL injection prevented (parameterized queries) | ✓ | SQLAlchemy ORM with parameterized queries throughout |
| Invalid input produces clear error messages | ✓ | Exception handlers in `app.py:258-284` |
| Error messages don't leak sensitive information | ✓ | Generic error messages used in responses |
| Validation happens at trust boundary | ✓ | Validation in `api/routes/upload.py` before processing |
| Rate limiting on authentication endpoints | ✓ | `src/mkobi/api/routes/auth.py:66-76` - Login rate limiting |
| Rate limiting on write operations (upload) | ✓ | `src/mkobi/api/routes/upload.py:122-138` - Upload rate limiting |
| Throttling configurable by environment | ✓ | `src/mkobi/config.py:283` - `rate_limiter_fail_closed` setting |
| Fail-closed in production, fail-open in development | ✓ | `src/mkobi/core/security.py:63-77` - Configurable fail mode |
| Rate limit bypass not exploitable | ✓ | Redis-based with proper key scoping |
| Passwords hashed with secure algorithm | ✓ | `src/mkobi/core/security.py:150-174` - bcrypt with 12 rounds |
| Password hashes never logged | ✓ | No password hash logging in auth_service.py |
| Minimum password length enforced | ✗ | SEC-001 - No validation at registration |
| Temporary passwords are cryptographically random | ✓ | `src/mkobi/api/routes/admin.py:188` - Uses `secrets.token_urlsafe` |
| Password change requires current password verification | ✓ | `src/mkobi/services/auth_service.py:451-499` - Verifies current password |
| CORS origins explicitly configured | ✓ | `src/mkobi/app.py:126-138` - Validates CORS in production |
| CORS validated at startup in production | ✓ | `src/mkobi/app.py:126-138` - Raises error if not configured |

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `SEC-001`, `SEC-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction |
| `classification` | enum | `mandatory` or `advisory` |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements