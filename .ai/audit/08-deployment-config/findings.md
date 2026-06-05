# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DC-001: Production .env.production template missing required secret values

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/.env.production, docker/docker-compose.yml |
| **Classification** | mandatory |

**Description:** The production environment template file `docker/.env.production` lacks the actual secret values that must be set before deployment. Lines 9-14 document required secrets as comments but the variables are missing from the file. Docker Compose will fail with unclear errors if these aren't provided externally. Meanwhile, `docker/.env.development` and `.env.example` have explicit `CHANGE_ME_*` placeholders.

**Evidence:** `docker/.env.production` lines 9-14 shows comments without actual values:
```yaml
# Required secrets (MUST be set for production deployment)
# DATABASE__PASSWORD: Database password for postgres superuser
# MKOBI_APP_PASSWORD: Application role password for runtime operations
# JWT__SECRET_KEY: Strong secret key (use: openssl rand -hex 32)
# ADMIN_USERNAME: Initial admin username
# ADMIN_PASSWORD: Initial admin password
```

Compare with `docker/.env.development` which has proper placeholders:
```yaml
DATABASE__PASSWORD=CHANGE_ME_GENERATE_STRONG_SECRET
JWT__SECRET_KEY=CHANGE_ME_GENERATE_WITH_OPENSSL_RAND_HEX_32
MKOBI_APP_PASSWORD=CHANGE_ME_GENERATE_STRONG_SECRET
```

**Recommendation:** Add actual placeholder values following the `CHANGE_ME_*` pattern to `docker/.env.production`, making it consistent with other template files and ensuring deployment operators have a clear template with all required values documented.

---

### DC-002: Admin password default value is weak and in WEAK_PASSWORDS list

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | mandatory |

**Description:** The default value for `admin_password` in `config.py` (line 297) is `"admin"` which appears in the `WEAK_PASSWORDS` set. If `ADMIN_PASSWORD` environment variable is not set, the application may start with a weak password in non-production environments. While production validation catches weak passwords, the default value should be obviously invalid to force operators to set proper credentials.

**Evidence:**
- `config.py` line 18: `WEAK_PASSWORDS = {"password", "123456", "admin", "secret", "test", "admin@example.com"}`
- `config.py` line 297: `admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")`

**Recommendation:** Update the default value to be obviously invalid (e.g., `"CHANGE_ME_ADMIN_PASSWORD"`) so that operators are forced to set proper credentials, preventing accidental use of weak defaults.

---

### DC-003: Missing production debug mode validation

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py, src/mkobi/config.py |
| **Classification** | mandatory |

**Description:** The application accepts `debug: bool = False` configuration but does not validate that debug mode must be disabled in production. If `DEBUG=true` is accidentally set in production, it would enable FastAPI debug mode, expose sensitive error traces, and potentially enable the Swagger UI documentation endpoints that are otherwise disabled in production.

**Evidence:** `src/mkobi/app.py` lines 200-208 show debug mode being used without production validation:
```python
application = FastAPI(
    ...
    debug=config.debug,
    docs_url=None if config.environment == EnvironmentEnum.PRODUCTION else "/docs",
    redoc_url=None if config.environment == EnvironmentEnum.PRODUCTION else "/redoc",
    ...
)
```

**Recommendation:** Add validation in `config.py` to reject `debug=True` when `environment == EnvironmentEnum.PRODUCTION`:
```python
if self.environment == EnvironmentEnum.PRODUCTION and self.debug:
    raise ValueError("Debug mode cannot be enabled in production environment")
```

---

### DC-004: Unauthenticated /health/detailed endpoint exposed in production

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py |
| **Classification** | mandatory |

**Description:** The `/health/detailed` endpoint (lines 263-301 in app.py) is accessible without authentication in all environments including production. This endpoint exposes internal system information including database connectivity status, static file paths, and component states. The docstring indicates it's "intended for admin use and monitoring systems" but has no authentication guard.

**Evidence:** `src/mkobi/app.py` lines 263-269 show the endpoint without any security dependency:
```python
@application.get("/health/detailed", tags=["health"])
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check with component status.

    Checks database connectivity and returns detailed status information.
    This endpoint is intended for admin use and monitoring systems.
    """
    # No authentication check before providing system internals
```

**Recommendation:** Either:
1. Restrict `/health/detailed` to authenticated admin users only, or
2. Gate this endpoint to non-production environments only (return 404 in production), or
3. Move detailed health checks to a monitoring port/endpoint that uses a separate authentication mechanism

---

### DC-005: Test compose has hardcoded fallback credentials instead of failing

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.test.yml |
| **Classification** | advisory |

**Description:** The test docker-compose uses `-:-` syntax with fallback values for secrets (e.g., `JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_jwt_secret_key_for_integration_tests_32_chars}`) instead of erroring when variables are missing. This is intentional for CI/CD but creates inconsistency with the production compose which uses `:-error` syntax.

**Evidence:** `docker/docker-compose.test.yml` line 67:
```yaml
JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_jwt_secret_key_for_integration_tests_32_chars}
```

**Recommendation:** Consider documenting this intentional difference in a comment at the top of the test compose file or using a separate test environment validation pattern that makes the fallback explicit. The current approach is acceptable for testing but could confuse operators about expected behavior.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 1 |

## Mandatory Fixes

- DC-001: Production .env.production template missing required secret values
- DC-002: Admin password default value is weak and in WEAK_PASSWORDS list
- DC-003: Missing production debug mode validation
- DC-004: Unauthenticated /health/detailed endpoint exposed in production

## Advisory Recommendations

- DC-005: Test compose has hardcoded fallback credentials instead of failing

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `DC-001`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction |
| `classification` | enum | `mandatory` or `advisory` |