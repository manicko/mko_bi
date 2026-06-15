---
name: 04-security
description: Security audit covering authentication, authorization, credential handling, input validation, and trust boundaries
agent: auditor
alwaysApply: false
problems-only: true
---

# Phase 04 Audit Findings — Security

**Executor:** auditor
**Template:** .kilo/commands/audit/phases/04-audit-security.md
**Status:** complete
**Validated:** no

---

## Findings

### SEC-01: User Enumeration via Login Timing Side-Channel

| Field | Value |
|-------|-------|
| **ID** | SEC-01 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/auth_service.py` |
| **Classification** | advisory |

**Description:** The `login_user` method in `AuthService` has a timing side-channel that allows attackers to enumerate valid email addresses. When a user is not found, the method returns `None` immediately (fast path). When a user exists but the password is wrong, it calls `verify_password` which executes bcrypt (slow path, ~100ms+). An attacker can measure response time differences to determine whether an email is registered.

**Evidence:**
- `src/mkobi/services/auth_service.py:201-206` — Early return on `user_obj is None` without dummy bcrypt call:
```python
user_obj = await self.user_repo.get_by_email_with_hash(email=email, db=db)
if user_obj is None:
    return None  # Fast path - no bcrypt

if not verify_password(password, user_obj.password_hash):
    return None  # Slow path - bcrypt was called
```
- The `_handle_login` wrapper at `src/mkobi/api/routes/auth.py:93-101` returns the same error message "Invalid credentials" for both cases, which is correct, but the timing difference remains exploitable.

**Recommendation:** Add a dummy `bcrypt.checkpw` call with a dummy hash when `user_obj is None`, so both code paths take similar time. For example, hash a constant dummy password and verify against it in the "user not found" branch. This is a small change that eliminates the timing oracle. Effort: trivial.

---

### SEC-02: User Enumeration via Registration Request Error Messages

| Field | Value |
|-------|-------|
| **ID** | SEC-02 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/auth_service.py`, `src/mkobi/api/routes/auth.py` |
| **Classification** | advisory |

**Description:** The `register_request` method returns distinct error messages that allow attackers to enumerate:
1. Whether an email is already registered as a user
2. Whether a registration request exists and its status (pending, approved, rejected)
3. Whether an email domain is blocked

The error messages are returned to the client as `AppException` details (HTTP 422), making them directly visible to attackers.

**Evidence:**
- `src/mkobi/services/auth_service.py:416` — "A request for this email already exists" (PENDING/APPROVED)
- `src/mkobi/services/auth_service.py:422-424` — "Your request was rejected. Contact an administrator for more information." (REJECTED)
- `src/mkobi/services/auth_service.py:438` — `f"User with email '{email}' already exists"` (user exists)
- `src/mkobi/services/auth_service.py:432` — "This email domain is not allowed for registration" (blocked domain)
- `src/mkobi/api/routes/auth.py:573-576` — All ValueError messages are forwarded to the client as `detail=str(e)`

**Recommendation:** Return a generic message like "If this email is eligible for registration, a request has been created" for all cases. Only reveal the blocked domain error (which is informational). The "user already exists" and "request already exists" cases should return the same generic success-like message to prevent enumeration. Effort: small.

---

### SEC-03: `.env` File with Real Credentials Present in Working Tree

| Field | Value |
|-------|-------|
| **ID** | SEC-03 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `.env` (project root) |
| **Classification** | advisory |

**Description:** The `.env` file in the project root contains values that, while labeled as development-only, follow patterns that could be accidentally used in production or committed to git. The `.gitignore` correctly excludes `.env`, but the file contains a JWT secret key that is 47 characters long (above the 32-char minimum) and a password that matches the admin username. While currently not tracked by git, the presence of a `.env` file with non-placeholder values in the working tree is a risk — any misconfiguration of `.gitignore` or `git add -f` would commit these.

**Evidence:**
- `.env:15` — `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`
- `.env:19` — `ADMIN_PASSWORD=admin@example.com` (same as username)
- `.env:10-11` — `DATABASE__PASSWORD=postgres`, `DATABASE__ADMIN_PASSWORD=postgres`
- `.gitignore:155` — `.env` is correctly excluded, but `.env` exists in working tree

**Recommendation:** Replace all values in `.env` with clearly non-functional placeholders (e.g., `JWT__SECRET_KEY=REPLACE_ME_32_CHARS_MIN`, `ADMIN_PASSWORD=REPLACE_ME`) and document that developers must set real values locally. This prevents accidental use of weak defaults. The `.env.example` file already has proper `CHANGE_ME` placeholders. Effort: trivial.

---

### SEC-04: `cookie_secure` Defaults to `True` Without Environment-Specific Override

| Field | Value |
|-------|-------|
| **ID** | SEC-04 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/config.py` |
| **Classification** | advisory |

**Description:** The `AppSettings.cookie_secure` field defaults to `True`, which means the `Secure` flag is set on all cookies. While this is correct for production, it breaks cookie-based refresh token flow in local development over HTTP (browsers refuse to send `Secure` cookies over non-HTTPS connections). The `.env` file sets `ENV=development`, but there is no environment-based conditional for `cookie_secure`. Developers must explicitly set `APP__COOKIE_SECURE=false` in their local `.env` to test auth flows over HTTP.

**Evidence:**
- `src/mkobi/config.py:227` — `cookie_secure: bool = True`
- `src/mkobi/core/security.py:406-413` — `set_secure_cookie` uses `config.app.cookie_secure` for the `secure` flag
- No environment-based conditional or validator that sets `cookie_secure=False` for development

**Recommendation:** Add a model validator or environment-based default that sets `cookie_secure=False` when `environment == EnvironmentEnum.DEVELOPMENT`. This improves developer experience while maintaining secure defaults for production. Alternatively, document this requirement clearly in the setup guide. Effort: trivial.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 1 |

## Mandatory Fixes

None. All findings are advisory (best-practice improvements).

## Advisory Recommendations

1. **SEC-01** — Add dummy bcrypt call in login "user not found" path to prevent timing-based user enumeration.
2. **SEC-02** — Unify registration request error messages to prevent user enumeration.
3. **SEC-03** — Replace `.env` values with non-functional placeholders to prevent accidental use/commit.
4. **SEC-04** — Make `cookie_secure` environment-aware (False in development) or document the requirement.

## Doc Updates Needed

- **SEC-04** — If keeping `cookie_secure=True` as default, update setup documentation to note that `APP__COOKIE_SECURE=false` must be set for local HTTP development.

---

## Audit Notes

### Areas Reviewed and Found Acceptable

**Authentication:**
- JWT tokens use HS256 algorithm with `exp` claim and `jti` for revocation ✓
- Token validation enforces signature and expiration ✓
- Token revocation via Redis blacklist with TTL ✓
- User-level token revocation on deactivation ✓
- Refresh tokens stored in httpOnly, SameSite=strict cookies ✓
- Logout revokes both access and refresh tokens ✓
- `is_active` check enforced in `get_current_user_dependency` ✓
- All protected routes use `get_current_user_dependency` or role requirements ✓
- Public routes (`/login`, `/login/form`, `/refresh`, `/register-request`, `/client-errors`, `/health`) are intentionally unauthenticated ✓

**Authorization:**
- Role hierarchy (admin > editor > viewer) enforced consistently ✓
- Resource-level access control (`check_dashboard_access`) applied to dashboard-specific routes ✓
- IDOR protection via `check_dashboard_access` on graph/layout/config routes ✓
- Admin-only routes use `require_admin_role` dependency ✓
- Users can only access their own data (users.py:153) ✓

**Password Security:**
- bcrypt with 12 salt rounds ✓
- Constant-time comparison via `bcrypt.checkpw` ✓
- Password strength validation (min 8 chars, digit + letter) ✓
- Password change requires current password verification ✓
- Temporary passwords generated with `secrets` module ✓
- Passwords never logged ✓

**Input Validation:**
- File upload validates MIME type from content (not client header) ✓
- File size enforced before and during streaming ✓
- Filename sanitized with `Path(filename).name` to prevent path traversal ✓
- SQL injection prevented — no raw SQL with string interpolation found ✓
- All queries use SQLAlchemy parameterized queries ✓

**Rate Limiting:**
- Login: 5 attempts per 5 minutes per IP ✓
- Token refresh: 10 attempts per 5 minutes per IP ✓
- Registration requests: 3 attempts per hour per IP ✓
- File upload: 100 attempts per hour per user ✓
- Client error reporting: 100 attempts per hour per IP ✓
- Fail-closed mode configurable, defaults to `True` ✓

**CORS & Security Headers:**
- CORS origins validated at startup in production (fail-fast on wildcard and empty) ✓
- CORS origins validated as proper http(s) URLs ✓
- Security headers middleware sets X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy ✓
- HSTS and CSP headers set in production mode ✓
- API docs disabled in production ✓

**Credential Management:**
- No hardcoded secrets in source code ✓
- All secrets from environment variables ✓
- Docker secrets (`_FILE` suffix) supported ✓
- JWT secret key validated for minimum length (32 chars) and weak values ✓
- Production mode rejects weak/default admin credentials ✓
- Production mode rejects placeholder database passwords ✓
- `.env` file correctly excluded from git ✓
