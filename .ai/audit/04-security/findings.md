# Phase 04 Audit Findings — Security

**Executor:** audit-executor
**Template:** `.kilo/commands/audit/phases/04-audit-security.md`
**Status:** complete
**Validated:** no

---

## Findings

### SEC-001: LRU-cached token decode bypasses revocation checks

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/permissions.py` |
| **Classification** | mandatory |

**Description:** The function `_decode_token_cached` in `permissions.py` uses `functools.lru_cache(maxsize=1000)` to cache token decode results. If a token is revoked (via Redis blacklist or user-level revocation), the cached decode still returns the old valid payload without calling `is_token_revoked()` or `is_user_tokens_revoked()`. The main dependency `get_current_user_dependency` in `deps.py` correctly calls `decode_token` directly and then checks revocation, but `_decode_token_cached` is a public function that could be (or may already be) called in code paths that skip revocation checks. Additionally, the LRU cache never respects token expiration — an expired token whose `exp` claim has passed can still be served from cache until the entry is evicted.

**Evidence:**
- `src/mkobi/core/permissions.py`, line ~183:
  ```python
  @lru_cache(maxsize=1000)
  def _decode_token_cached(token: str) -> dict[str, Any] | None:
      result: dict[str, Any] | None = decode_token(token)
      return result
  ```
- The `get_current_user()` function (same file) uses `_decode_token_cached(token)` and then calls `UserRepository().get()` but never checks `is_token_revoked()` or `is_user_tokens_revoked()`.
- In contrast, `get_current_user_dependency` in `deps.py` calls `decode_token(token)` (uncached) and checks revocation.

**Recommendation:** Remove the `_decode_token_cached` function entirely. If token decode performance is a concern, implement a short-lived TTL cache (e.g., 10–30 seconds) that also checks revocation status, or cache only the decode result and always check revocation on every request. At minimum, add revocation checks after every cached decode call.

---

### SEC-002: Unauthenticated and unrate-limited client error reporting endpoint

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/client_errors.py` |
| **Classification** | mandatory |

**Description:** The `POST /api/v1/client-errors` endpoint requires no authentication and applies no rate limiting. Any anonymous client can POST arbitrary payloads that are written directly to the server log. This enables:
1. **Log injection** — attacker-controlled `error.message`, `url`, and `componentStack` fields are interpolated directly into log output via `%s` formatting.
2. **Log flooding / DoS** — unbounded requests fill disk/logs without any throttling.
3. **Reconnaissance aid** — the endpoint confirms the server is alive and can be used to test infrastructure response patterns.

**Evidence:**
- `src/mkobi/api/routes/client_errors.py`, line 38–49:
  ```python
  @router.post(
      "",
      status_code=status.HTTP_204_NO_CONTENT,
      summary="Report client-side error",
      description="Accepts client error details for logging. No authentication required.",
  )
  async def report_client_error(payload: ClientErrorPayload) -> None:
      error_message = payload.error.get("message", "Unknown error")
      logger.error(
          "Client error: %s | url=%s | componentStack=%s",
          error_message,
          payload.url,
          payload.componentStack,
      )
  ```
- No `Depends(get_current_user_dependency)` or `Depends(require_viewer_role)`.
- No `AsyncRateLimiter` call.

**Recommendation:** Add at minimum authentication (`Depends(require_viewer_role)`) and rate limiting to this endpoint. If supporting pre-auth error reporting is required (e.g., for login page errors), add IP-based rate limiting (e.g., 10 requests per minute per IP) and sanitize/truncate all logged fields to prevent log injection.

---

### SEC-003: Refresh token endpoint lacks rate limiting

| Field | Value |
|-------|-------|
| **ID** | SEC-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/auth.py` |
| **Classification** | mandatory |

**Description:** The `POST /api/v1/auth/refresh` endpoint does not apply any rate limiting. While the refresh token is stored in an httpOnly cookie (making direct theft harder), an attacker who obtains the cookie (via XSS in a subdomain, network sniffing on non-HTTPS connections, or browser vulnerability) could repeatedly call `/refresh` to obtain new access tokens without any throttling. Rate limiting is properly applied to the `/login` and `/register-request` endpoints but is missing from `/refresh`.

**Evidence:**
- `src/mkobi/api/routes/auth.py`, refresh endpoint (line ~175):
  ```python
  @router.post(
      "/refresh",
      ...
  )
  async def refresh(
      request: Request,
      response: Response,
      session: Annotated[AsyncSession, Depends(get_db_dependency)],
      redis_client: Any = Depends(get_redis_client_dependency),
  ) -> Token:
  ```
- No `AsyncRateLimiter` call inside the function.
- Contrast with `/login` which has:
  ```python
  if not await rate_limiter.check_rate_limit(
      f"login:{client_ip}", max_attempts=5, ttl=300
  ):
  ```

**Recommendation:** Add IP-based rate limiting to the `/refresh` endpoint, similar to the login endpoint. Suggested: 20 requests per minute per IP (more generous than login since legitimate usage is periodic, but still bounded).

---

### SEC-004: Rate limiter defaults to fail-open (bypass on Redis failure)

| Field | Value |
|-------|-------|
| **ID** | SEC-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/config.py`, `src/mkobi/core/security.py` |
| **Classification** | mandatory |

**Description:** The `RATE_LIMITER_FAIL_CLOSED` setting defaults to `False` in `config.py`. When Redis is unavailable (connection loss, restart, network partition), all rate limiting is bypassed — every request is allowed. This means that during a Redis outage, login bruteforce protection, upload throttling, and registration abuse prevention all disappear silently.

The production docker-compose correctly overrides this to `true`, but the application default is insecure. If someone deploys the application without docker-compose (e.g., bare-metal, Kubernetes with incorrect env), rate limiting would silently fail open.

**Evidence:**
- `src/mkobi/config.py`, line ~272:
  ```python
  rate_limiter_fail_closed: bool = Field(default=False, alias="RATE_LIMITER_FAIL_CLOSED")
  ```
- `src/mkobi/core/security.py`, `AsyncRateLimiter.check_rate_limit` (line ~95):
  ```python
  except Exception as e:
      logger.error("Rate limiter Redis error for key %s: %s", key, e)
      if self._fail_closed:
          ...
          return False
      logger.warning(
          "Rate limiter fail-open: allowing request for key %s "
          "(Redis unavailable)", key,
      )
      return True
  ```
- `docker/docker-compose.yml` overrides: `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}`

**Recommendation:** Change the default value of `RATE_LIMITER_FAIL_CLOSED` to `True`. Security controls should fail closed by default. If a deployment explicitly needs fail-open behavior (rare), they can set `RATE_LIMITER_FAIL_CLOSED=false` as an intentional opt-out.

---

### SEC-005: Detailed health endpoint exposes infrastructure information without authentication

| Field | Value |
|-------|-------|
| **ID** | SEC-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** The `GET /health/detailed` endpoint is unauthenticated and returns infrastructure details including database type (`postgresql`), connection status, and static file paths. This information aids reconnaissance by revealing the technology stack and internal architecture. Neither `/health` nor `/health/detailed` require authentication.

**Evidence:**
- `src/mkobi/app.py`, line ~290:
  ```python
  @application.get("/health/detailed", tags=["health"])
  async def detailed_health_check() -> dict[str, Any]:
      ...
      components["database"] = {
          "status": "connected",
          "type": "postgresql",
      }
      components["static_files"] = {
          "status": "available" if os.path.isdir("frontend/dist") else "unavailable",
          "path": "frontend/dist",
      }
  ```
- No `Depends(get_current_user_dependency)` or similar auth requirement.

**Recommendation:** Require authentication (admin role) on `/health/detailed`. The basic `/health` endpoint (with just status + DB connected) is acceptable without auth for load balancers, but the detailed version should be protected. Alternatively, remove the detailed endpoint and rely on external monitoring tools that authenticate separately.

---

### SEC-006: Production config does not reject placeholder database passwords

| Field | Value |
|-------|-------|
| **ID** | SEC-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/config.py` |
| **Classification** | mandatory |

**Description:** The config validates admin credentials in production (rejects weak usernames/passwords via `WEAK_USERNAMES`/`WEAK_PASSWORDS` sets) and validates the JWT secret key strength (minimum 32 characters, not in `WEAK_SECRETS`), but does NOT validate that `database.password` and `database.admin_password` are not placeholder values. If a deployment sets `ENV=production` with `DATABASE__PASSWORD=CHANGE_ME_GENERATE_STRONG_SECRET` (the `.env.example` placeholder), the application will start without error and connect to the database with the placeholder string as the password.

**Evidence:**
- `src/mkobi/config.py`, `DatabaseSettings` class — no validator on `password` or `admin_password` fields:
  ```python
  class DatabaseSettings(BaseModel):
      password: str | None = None
      admin_password: str | None = None
  ```
- Compare with `JWTSettings` which has:
  ```python
  @field_validator("secret_key")
  @classmethod
  def validate_secret_key(cls, v: str | None) -> str | None:
      if len(v) < 32:
          raise ValueError("JWT secret key must be at least 32 characters")
  ```
- And `Settings.validate_admin_credentials` which rejects weak admin passwords in production.

**Recommendation:** Add a `model_validator` on `DatabaseSettings` (or a post-init check in `Settings`) that rejects known placeholder values (e.g., `CHANGE_ME_GENERATE_STRONG_SECRET`, `postgres`) for `database.password` and `database.admin_password` when `environment == PRODUCTION`. Alternatively, require these passwords to meet a minimum length/strength threshold similar to the JWT secret key validator.

---

### SEC-007: Change-password endpoint lacks rate limiting

| Field | Value |
|-------|-------|
| **ID** | SEC-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/auth.py` |
| **Classification** | advisory |

**Description:** The `POST /api/v1/auth/change-password` endpoint does not apply rate limiting. While it requires authentication and current password verification, an attacker with a stolen session token could attempt rapid password changes (or bruteforce the current password field) without throttling.

**Evidence:**
- `src/mkobi/api/routes/auth.py`, `change_password` endpoint (line ~280):
  - Has `Depends(get_current_user_dependency)` for authentication.
  - No `AsyncRateLimiter` call.
  - Sends both `current_password` and `new_password` in request body — `current_password` is effectively a second auth factor that could be bruteforced.

**Recommendation:** Add per-user rate limiting to the change-password endpoint (e.g., 5 attempts per 15 minutes per user). This prevents bruteforce of the current password field even if an attacker has a valid access token.

---

### SEC-008: Logout endpoint missing rate limiting

| Field | Value |
|-------|-------|
| **ID** | SEC-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/auth.py` |
| **Classification** | advisory |

**Description:** The `POST /api/v1/auth/logout` endpoint has no rate limiting. While logout is a low-sensitivity operation, an attacker with any valid token could flood the endpoint to generate excessive Redis blacklist entries (one per call) and cause Redis memory pressure.

**Evidence:**
- `src/mkobi/api/routes/auth.py`, `logout` endpoint (line ~240) — no `AsyncRateLimiter` call.

**Recommendation:** Add per-user rate limiting (e.g., 10 requests per minute per user) to prevent abuse of the token revocation mechanism.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 4 |
| MEDIUM | 3 |
| LOW | 1 |

## Mandatory Fixes

- **SEC-001**: Remove or fix `_decode_token_cached` — cached token decode bypasses revocation checks and expiration enforcement.
- **SEC-002**: Add authentication and rate limiting to `/client-errors` endpoint — currently a public, unrate-limited write endpoint enabling log injection and DoS.
- **SEC-003**: Add rate limiting to `/auth/refresh` endpoint — missing rate limiting allows unbounded refresh token usage.
- **SEC-004**: Change `RATE_LIMITER_FAIL_CLOSED` default to `True` — fail-open default silently disables all rate limiting when Redis is unavailable.
- **SEC-006**: Add production validation for database passwords — placeholder values are not rejected in production mode.

## Advisory Recommendations

- **SEC-005**: Protect `/health/detailed` with authentication to prevent infrastructure information disclosure.
- **SEC-007**: Add rate limiting to `/auth/change-password` to prevent current-password bruteforce.
- **SEC-008**: Add rate limiting to `/auth/logout` to prevent Redis memory pressure via token revocation flooding.

## Doc Updates Needed

(None — all findings are code/configuration issues, not documentation gaps.)
