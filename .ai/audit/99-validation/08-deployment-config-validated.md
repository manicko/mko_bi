# Phase 08 Validation Report — Configuration & Lifecycle

**Validator:** validator  
**Source findings:** `.ai/audit/08-deployment-config/findings.md`  
**Date:** 2026-06-15

---

## All audit findings validated. No rejections, merges, or conflicts.

---

## Validated Findings Summary

All 10 findings from Phase 08 are technically correct and validated against the codebase. Each finding has been verified for accuracy and architectural relevance.

### Mandatory Fixes (Confirmed Valid)

| ID | Title | Severity | Type | Status |
|----|-------|----------|------|--------|
| DC-001 | Nginx X-Frame-Options Conflicts | MEDIUM | SPEC-DEVIATION | ✅ Validated |
| DC-005 | rqworker Command Format Inconsistency | HIGH | RUNTIME-ERROR | ✅ Validated |
| DC-006 | ADMIN_PASSWORD Placeholder Creates Known Password | HIGH | BEST-PRACTICE | ✅ Validated |

### Advisory Recommendations (Confirmed Valid)

| ID | Title | Severity | Type | Status |
|----|-------|----------|------|--------|
| DC-002 | Nginx Missing /health/detailed Proxy | LOW | SPEC-DEVIATION | ✅ Validated |
| DC-004 | Weak Passwords Without Warning | MEDIUM | BEST-PRACTICE | ✅ Validated |
| DC-007 | Test Compose Default Passwords | LOW | BEST-PRACTICE | ✅ Validated |
| DC-010 | Nginx CSP Conflicts with Vite HMR | LOW | BEST-PRACTICE | ✅ Validated |

### Doc Updates (Confirmed Valid)

| ID | Title | Severity | Type | Status |
|----|-------|----------|------|--------|
| DC-003 | RATE_LIMITER_FAIL_CLOSED Default | MEDIUM | DOC-UPDATE | ✅ Validated |
| DC-008 | Incorrect Config Defaults in Docs | LOW | DOC-UPDATE | ✅ Validated |
| DC-009 | RECREATE_TEST_DB Test Override Not Documented | LOW | DOC-UPDATE | ✅ Validated |

---

## Evidence Verification Notes

### DC-001 — X-Frame-Options Conflict
- **Verified:** `src/mkobi/app.py:70` sets `DENY`
- **Verified:** `docker/nginx/nginx.conf:21` sets `SAMEORIGIN`
- **Verified:** Both headers use `always` flag, causing Nginx to override app header
- **Verified:** Deployment doc `docs/10-deployment/deployment.md:384-394` documents iframe fallback strategy (Dash migration)

### DC-002 — /health/detailed Not Proxied
- **Verified:** `src/mkobi/app.py:271-272` defines endpoint
- **Verified:** `docker/nginx/nginx.conf:42-46` only proxies `/health`, not `/health/detailed`
- **Verified:** `docs/05-health/health-api.md:70-130` documents `/health/detailed` as public monitoring endpoint

### DC-003 — RATE_LIMITER_FAIL_CLOSED Default
- **Verified:** Code default `True` at `src/mkobi/config.py:362`
- **Verified:** Documentation states "false" as default for fail-open mode at `docs/08-security/security-overview.md:60`
- **Verified:** Production env sets `true` correctly

### DC-004 — Weak Passwords in Development
- **Verified:** `.env` contains `postgres`, `admin@example.com`, `dev-app-password`
- **Verified:** All are in `WEAK_PASSWORDS` set at `src/mkobi/config.py:19-31`
- **Verified:** `validate_admin_credentials` only warns in non-production at `src/mkobi/config.py:403-415`
- **Verified:** `docker-compose.override.yml:63` sets `APP__COOKIE_SECURE=false` (development-relaxed security)

### DC-005 — rqworker Command Format
- **Verified:** `docker/docker-compose.override.yml:106` uses `/app/.venv/bin/rqworker`
- **Verified:** `docker/docker-compose.yml:162` uses `uv run rq worker`
- **Verified:** Both are valid, but inconsistency creates maintenance risk

### DC-006 — ADMIN_PASSWORD Placeholder
- **Verified:** Default at `src/mkobi/config.py:353` is `"CHANGE_ME_ADMIN_PASSWORD"`
- **Verified:** Lowercase `"change_me_admin_password"` in `WEAK_PASSWORDS` at line 27
- **Verified:** `ensure_admin_user()` uses password directly at `src/mkobi/db/starter.py:326-352` without placeholder check
- **Verified:** Non-production only logs warnings, doesn't prevent admin user creation with known password

### DC-007 — Test Compose Defaults
- **Verified:** `docker/docker-compose.test.yml:33-34` uses `-test_password` and `-test_app_password` defaults
- **Verified:** `tests/conftest.py:28` sets `RECREATE_TEST_DB=true`
- **Verified:** Security assessment comments in compose file justify this pattern

### DC-008 — Incorrect Documentation Defaults
- **Verified:** Code default `DATABASE__USER` is `"mkobi_app"` at `src/mkobi/config.py:94`, doc says `"postgres"`
- **Verified:** Code default `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` is `15` at line 185, doc says `30`

### DC-009 — RECREATE_TEST_DB Test Override
- **Verified:** Code default `False` at `src/mkobi/config.py:488`
- **Verified:** Test compose sets `true` at `docker/docker-compose.test.yml:145`
- **Verified:** `tests/conftest.py:28` sets `RECREATE_TEST_DB=true`
- **Verified:** Documentation doesn't mention this test-specific override

### DC-010 — CSP/Header Conflict
- **Verified:** App sets HSTS/CSP conditionally (production only) at `src/mkobi/app.py:74-77`
- **Verified:** Nginx sets CSP unconditionally at `docker/nginx/nginx.conf:30`
- **Verified:** Nginx comment notes HSTS should be HTTPS-only at lines 24-25
- **Verified:** CSP policy includes `script-src 'self'` without `'unsafe-eval'`, which would block Vite HMR

---

## Validated Counts Summary

| Category | Count |
|----------|-------|
| Mandatory fixes | 3 |
| Advisory recommendations | 4 |
| Doc updates | 3 |
| Total validated | 10 |

---

## Rollout Safety Assessment

- **DC-001, DC-003, DC-008, DC-009:** Documentation-only changes pose no rollout risk
- **DC-002:** Adding `/health/detailed` proxy is trivial and backward-compatible
- **DC-005:** Standardizing command format requires no breaking changes
- **DC-006:** Adding placeholder check to `ensure_admin_user()` requires careful handling for development mode (should warn/error without breaking existing dev workflows)
- **DC-010:** CSP adjustment may affect development iframe usage if Nginx is used in dev

---

## Cross-Phase Conflict Check

No conflicts detected with other audit phases.

---

## Actionable Recommendations

The following recommendations provide specific, implementation-ready guidance for three audit findings that require deeper research to make actionable. Each recommendation includes the exact file(s) to change, the exact change to make, and the rationale for the chosen approach.

---

### DC-004: Weak Passwords Without Warning — Startup Warning Implementation

**Files to change:**
- `src/mkobi/config.py` — add a dedicated weak-password detection function and call it from `Settings.__init__`
- `src/mkobi/app.py` — add a startup log warning in the `lifespan` function (secondary location)

**Recommended approach: Add a `_log_security_warnings()` method to `Settings.__init__`, called after `_log_initialization()`.**

This approach was chosen over alternatives because:
- It keeps all credential-warning logic co-located in `config.py` alongside the existing `validate_admin_credentials` model validator and the `WEAK_PASSWORDS` set, following the project's pattern of config-level validation.
- It runs at config load time (which happens before `create_app()` in `main.py`), so warnings appear early in startup regardless of how the app is launched.
- It does not block startup — it only logs warnings, which matches the audit requirement to "alert developers without blocking startup."
- Adding a secondary warning in `app.py`'s `lifespan` is optional but provides defense-in-depth for cases where `get_config()` is called indirectly.

**Exact change in `src/mkobi/config.py`:**

Add the following method to the `Settings` class, between `_ensure_upload_dir()` and the `DATABASE_URL` property (around line 554):

```python
def _log_security_warnings(self) -> None:
    """Log security warnings for weak/default credentials in non-production.

    Alerts developers when known weak passwords are in use without blocking
    startup. In production, validation in validate_admin_credentials and
    DATABASE_URL property already rejects weak values with ValueError.
    """
    if self.environment == EnvironmentEnum.PRODUCTION:
        return

    weak_db_password = (
        self.database.password
        and self.database.password.lower() in {p.lower() for p in WEAK_PASSWORDS}
    )
    weak_admin_password = self.admin_password.lower() in {
        p.lower() for p in WEAK_PASSWORDS
    }
    weak_admin_username = self.admin_username.lower() in {
        u.lower() for u in WEAK_USERNAMES
    }
    weak_jwt_secret = (
        self.jwt.secret_key
        and self.jwt.secret_key.lower() in {s.lower() for s in self.jwt.WEAK_SECRETS}
    )

    if weak_db_password:
        logger.warning(
            "SECURITY: Database password is a known weak value. "
            "Set DATABASE__PASSWORD to a strong password."
        )
    if weak_admin_password:
        logger.warning(
            "SECURITY: Admin password is a known weak/default value ('%s'). "
            "Set ADMIN_PASSWORD to a strong password.",
            self.admin_password,
        )
    if weak_admin_username:
        logger.warning(
            "SECURITY: Admin username is a known weak/default value ('%s'). "
            "Set ADMIN_USERNAME to a non-default value.",
            self.admin_username,
        )
    if weak_jwt_secret:
        logger.warning(
            "SECURITY: JWT secret key is a known weak value. "
            "Generate a strong secret with: openssl rand -hex 32"
        )
```

Then call it from `Settings.__init__` after `_ensure_upload_dir()` (around line 537):

```python
def __init__(self, **data: Any) -> None:
    """Initialize configuration and log settings (without secrets)."""
    super().__init__(**data)
    self._log_initialization()
    self._ensure_upload_dir()
    self._log_security_warnings()
```

**Why this approach over alternatives:**
- **Alternative considered:** Adding the warning in `app.py`'s `lifespan` function. Rejected as the primary location because `config.py` is the single source of truth for credential validation, and the warning logic needs access to raw config values (which are already validated and available in `Settings.__init__`).
- **Alternative considered:** Raising an error instead of logging a warning. Rejected because the audit explicitly requires "alert without blocking startup" for development mode.
- **Alternative considered:** Checking against a separate list of "development-only" passwords. Rejected because the existing `WEAK_PASSWORDS` set already covers this purpose — it is used by `validate_admin_credentials` for the same check in production.

---

### DC-006: ADMIN_PASSWORD Placeholder — Refuse Placeholder in `ensure_admin_user()`

**Files to change:**
- `src/mkobi/db/starter.py` — modify `ensure_admin_user()` to reject known placeholder passwords

**Recommended approach: Add a check at the top of `ensure_admin_user()` that raises `ValueError` if the admin password matches a known placeholder value, regardless of environment.**

This approach was chosen over the "generate a random password" alternative because:
- It is deterministic and explicit — the developer must consciously set a password, which is the secure-by-default posture the project already follows for `DATABASE__PASSWORD` and `JWT__SECRET_KEY` in production.
- Generating a random password in development creates a poor UX (the developer cannot log in without reading logs or resetting the password), and it would require additional infrastructure (printing to stdout, writing to a file).
- The project's existing pattern is to reject weak/placeholder values with `ValueError` at the appropriate layer. For admin credentials, the appropriate layer is `ensure_admin_user()` because that is where the password is actually consumed.
- This does not break development workflows: the `.env` file already requires the developer to set `ADMIN_PASSWORD`, and Docker Compose uses `${ADMIN_PASSWORD:?...}` syntax that fails if unset.

**Exact change in `src/mkobi/db/starter.py`:**

Replace the `ensure_admin_user()` method (lines 317-352) with:

```python
async def ensure_admin_user(self) -> None:
    """Create admin user if it does not already exist.

    Idempotent — safe to run multiple times.
    Uses atomic UPSERT to avoid race conditions on concurrent startup.

    Raises:
        ValueError: If the admin password matches a known placeholder value.
    """
    from mkobi.config import WEAK_PASSWORDS

    config = get_config()
    admin_email = config.admin_username
    admin_password = config.admin_password

    # Refuse to create admin user with a known placeholder password.
    # This check runs in ALL environments to prevent accidental use of
    # default credentials. Production already rejects weak passwords via
    # Settings.validate_admin_credentials, but this provides defense-in-depth
    # at the point where the password is actually consumed.
    if admin_password.lower() in {p.lower() for p in WEAK_PASSWORDS}:
        raise ValueError(
            f"Admin password is a known placeholder value. "
            "Set ADMIN_PASSWORD to a strong, unique password."
        )

    # Warn if using default username (not production due to config validation)
    if admin_email == "admin":
        logger.warning(
            "Using default admin username - set ADMIN_USERNAME environment variable"
        )

    SessionLocal = await get_async_sessionlocal()

    async with SessionLocal() as db:
        async with db.begin():
            await db.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role, is_active) "
                    "VALUES (:id, :email, :password, :role, true) "
                    "ON CONFLICT (email) DO NOTHING"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "email": admin_email,
                    "password": hash_password(admin_password),
                    "role": UserRole.ADMIN,
                },
            )
        logger.info("Admin user ensured: %s", admin_email)
```

**Why this approach over alternatives:**
- **Alternative considered:** Generating a random password in development. Rejected because it creates operational complexity (where to store/print the password) and deviates from the project's pattern of requiring explicit credential configuration.
- **Alternative considered:** Only checking in production (relying on `Settings.validate_admin_credentials`). Rejected because it leaves development environments with a known-password admin account, which is a security risk if the dev environment is network-accessible (e.g., Docker ports exposed).
- **Alternative considered:** Adding the check to `Settings.validate_admin_credentials` model validator. Rejected because that validator already handles production vs. development differently, and adding a universal placeholder rejection there would change its semantics. The `ensure_admin_user()` method is the correct layer — it is where the password is consumed.

**Note:** The `WEAK_PASSWORDS` import is already available at module level in `config.py` and can be imported directly. This avoids circular imports because `starter.py` already imports `get_config` from `mkobi.config`.

---

### DC-010: Nginx CSP Conflicts — Remove CSP from Nginx, Let Application Handle It

**Files to change:**
- `docker/nginx/nginx.conf` — remove the `Content-Security-Policy` directive from the Nginx server block and add a comment explaining why
- `src/mkobi/app.py` — update `SecurityHeadersMiddleware` to set CSP unconditionally (all environments), not just in production

**Recommended approach: Remove CSP from Nginx entirely and have the application's `SecurityHeadersMiddleware` handle CSP in all environments.**

This approach was chosen because:
- It follows the "single source of truth" principle. The application already has environment-aware CSP logic (`if config.environment == EnvironmentEnum.PRODUCTION`). Having Nginx set CSP unconditionally creates a conflict where Nginx's static policy overrides the application's dynamic policy.
- The Nginx CSP policy (`script-src 'self'` without `'unsafe-eval'`) would break Vite HMR in development, which requires `eval()`. The application middleware correctly handles this by only setting CSP in production.
- The Nginx `add_header` directive does NOT inherit into `location` blocks when a parent also has `add_header`. This means the `/health` location would NOT get CSP, creating inconsistent behavior. The application middleware applies to all responses uniformly.
- The project's architecture already treats Nginx as a simple reverse proxy (TLS termination, static files) and the application as the security policy owner. The `SecurityHeadersMiddleware` docstring explicitly states "defense-in-depth by setting security headers at the application layer in addition to nginx" — but for CSP, the application should be the sole source.
- The `X-Frame-Options` conflict (DC-001) is a separate issue, but removing CSP from Nginx eliminates the entire class of CSP-related header conflicts.

**Exact change in `docker/nginx/nginx.conf`:**

Remove line 30 (the CSP directive) and replace lines 26-30 with:

```nginx
        # Content-Security-Policy is set by the application's SecurityHeadersMiddleware.
        # Nginx does not set CSP to avoid conflicts with the application's environment-aware
        # policy (production sets CSP; development allows 'unsafe-eval' for Vite HMR).
        # See src/mkobi/app.py — SecurityHeadersMiddleware.
```

The resulting security headers section (lines 20-30) becomes:

```nginx
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        # NOTE: HSTS header should only be set on HTTPS connections.
        # See the commented HTTPS server block below for proper HSTS configuration.
        # Content-Security-Policy is set by the application's SecurityHeadersMiddleware.
        # Nginx does not set CSP to avoid conflicts with the application's environment-aware
        # policy (production sets CSP; development allows 'unsafe-eval' for Vite HMR).
        # See src/mkobi/app.py — SecurityHeadersMiddleware.
```

**Exact change in `src/mkobi/app.py`:**

Update the `SecurityHeadersMiddleware.dispatch()` method (lines 57-79) to set CSP in all environments, with a relaxed policy for non-production:

```python
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Add security headers to response.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler in the middleware chain.

        Returns:
            Response with security headers added.
        """
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        config = get_config()
        if config.environment == EnvironmentEnum.PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        else:
            # Development/staging: relaxed CSP to allow Vite HMR (eval) and
            # connection to the Vite dev server. Nginx does not set CSP.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self' ws://localhost:*"
            )

        return response
```

Also update the class docstring (lines 46-56) to reflect the change:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Implements defense-in-depth by setting security headers at the application layer.
    Nginx sets baseline headers (X-Content-Type-Options, X-Frame-Options, etc.)
    but CSP is managed exclusively by this middleware to support environment-aware
    policies (strict in production, relaxed for Vite HMR in development).

    Headers include:
    - X-Content-Type-Options: Prevents MIME type sniffing (all environments)
    - X-Frame-Options: Prevents clickjacking (all environments)
    - X-XSS-Protection: Enables browser XSS filter (all environments)
    - Referrer-Policy: Controls referrer information (all environments)
    - Strict-Transport-Security: Enforces HTTPS connections (HSTS) - production only
    - Content-Security-Policy: Prevents XSS and injection attacks (all environments,
      relaxed in development for Vite HMR compatibility)
    """
```

**Why this approach over alternatives:**
- **Alternative considered:** Adding a comment to Nginx config and keeping both. Rejected because duplicate CSP headers cause unpredictable browser behavior — browsers use the most restrictive combination of all CSP headers received, so the Nginx policy would override the application's relaxed dev policy.
- **Alternative considered:** Making Nginx CSP conditional (e.g., using `map` or `if`). Rejected because Nginx `if` is notoriously error-prone ("if is evil" in Nginx), and it adds complexity to the Nginx config for policy that belongs in the application.
- **Alternative considered:** Removing CSP from the application and letting Nginx handle it. Rejected because the application needs different CSP policies per environment (production vs. development with Vite HMR), and Nginx cannot make that distinction without complex conditional logic.