# Phase 08 Validation Report — Configuration & Lifecycle

**Validator:** validator
**Source:** .ai/audit/08-deployment-config/findings.md
**Mode:** problems-only
**Date:** 2026-06-05

---

## Reclassified Findings

### DC-001 — Production .env.production template missing required secret values

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Original Type** | SPEC-DEVIATION |
| **Reclassified Type** | DOC-UPDATE |
| **Original Severity** | HIGH |
| **Adjusted Severity** | LOW |
| **Classification** | advisory |

**Rationale:** The finding's core claim — that missing placeholders cause "unclear errors" — is stale. The production `docker-compose.yml` uses `${VAR:?error}` enforcement syntax (e.g., `DATABASE__PASSWORD: ${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}`), which produces explicit, clear error messages when variables are unset. Docker Compose will refuse to start and print exactly which variable is missing.

However, the inconsistency between `.env.production` (comments only, no placeholder keys) and `.env.development` / `.env.example` (explicit `CHANGE_ME_*` placeholder keys) is a real template quality issue. An operator copying `.env.production` as a starting point would not have a complete checklist of required secrets in the file itself — they would need to cross-reference `docker-compose.yml` or the documentation.

**Reclassification reasoning:** This is not a spec deviation — the file is intentionally a comment-only template (line 2: "Copy this file to .env.production and fill in all values"). The `?error` enforcement in docker-compose.yml provides the safety net. The issue is documentation quality: the template should either include `CHANGE_ME_*` placeholder keys for consistency with other template files, or the deployment docs should explicitly state that `.env.production` is a comment-only reference and operators must use `docker-compose.yml` as the source of truth for required variables.

**Recommendation:** Add `CHANGE_ME_*` placeholder keys to `.env.production` for consistency with `.env.development` and `.env.example`, OR update `docs/10-deployment/deployment.md` to document the intentional difference and guide operators to use `docker-compose.yml` as the authoritative list of required variables.

---

### DC-004 — Unauthenticated /health/detailed endpoint exposed in production

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Original Severity** | HIGH |
| **Adjusted Severity** | LOW |
| **Type** | SPEC-DEVIATION (unchanged) |
| **Classification** | advisory (downgraded from mandatory) |

**Rationale:** The finding is technically correct — `/health/detailed` has no authentication. However, the severity is overstated for the following reasons:

1. **Documented as public:** `docs/05-health/health-api.md` line 26 explicitly states `Auth level: Public (no authentication required)` for the detailed health check endpoint. This is an intentional design decision, not an oversight.

2. **Minimal information exposure:** The endpoint returns:
   - Database connectivity status (`connected`/`disconnected`) — this is also exposed by the public `/health` endpoint
   - Database type (`postgresql`) — not sensitive
   - Static file availability and path (`frontend/dist`) — not sensitive
   - Database error message on failure — this is the only potentially sensitive data, but it is only returned when the database is already unreachable (a 503-equivalent scenario)

3. **Consistent with industry practice:** Detailed health endpoints are commonly left public for load balancer and monitoring system consumption. The basic `/health` endpoint is the primary probe; `/health/detailed` is for admin dashboards and troubleshooting.

4. **No credentials, configuration values, or internal network information is exposed.**

**Remaining concern:** The database error message in the response (line 291: `"error": str(e)`) could leak internal connection details (e.g., hostnames, connection strings) in error scenarios. This should be sanitized to a generic message in production.

**Recommendation:** Downgrade to advisory. If hardening is desired: (a) sanitize the database error message in production to avoid leaking connection details, or (b) restrict the endpoint to internal network access via nginx configuration rather than application-level authentication.

---

## Validated Findings (Problems Found)

### DC-002 — Admin password default value is weak and in WEAK_PASSWORDS list

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory |

**Status:** VALIDATED — mandatory fix.

**Evidence confirmed:**
- `config.py` line 18: `WEAK_PASSWORDS = {"password", "123456", "admin", "secret", "test", "admin@example.com"}` — `"admin"` is in the set.
- `config.py` line 297: `admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")` — default is `"admin"`.
- `config.py` lines 329-354: `validate_admin_credentials` model_validator catches weak passwords in production (lines 336-345).

**Analysis:** The production validator (`validate_admin_credentials`) correctly rejects `admin` as a password when `environment == EnvironmentEnum.PRODUCTION`. However, the default value `"admin"` is problematic for two reasons:

1. **Non-production environments:** In development/staging, the application will start with `admin/admin` credentials if `ADMIN_PASSWORD` is not explicitly set. The validator only logs a warning in non-production (lines 347-353), it does not prevent startup.

2. **Operator confusion:** An operator who forgets to set `ADMIN_PASSWORD` in a non-production deployment will have a running system with weak credentials and only a log warning (which may not be noticed).

**The fix is correct:** Changing the default to `"CHANGE_ME_ADMIN_PASSWORD"` (or similar obviously-invalid value) forces operators to explicitly set the password, eliminating the risk of accidental weak defaults.

**Semantic target stability:** The default value at line 297 is a stable anchor — it is a field definition unlikely to be refactored.

---

### DC-003 — Missing production debug mode validation

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory |

**Status:** VALIDATED — mandatory fix.

**Evidence confirmed:**
- `config.py` line 267: `debug: bool = False` — no validator rejects `True` in production.
- `app.py` line 204: `debug=config.debug` — passed directly to FastAPI.
- `app.py` lines 205-206: `docs_url` and `redoc_url` are gated on `config.environment == EnvironmentEnum.PRODUCTION`, but `debug` is not.

**Analysis:** If `DEBUG=true` is accidentally set in production:
- FastAPI debug mode is enabled, which includes detailed error tracebacks in responses (potential information disclosure).
- The `docs_url` and `redoc_url` are already gated by environment check (lines 205-206), so Swagger UI won't be exposed. This partially mitigates the risk.
- However, debug mode also affects exception handling behavior and may expose stack traces.

**The fix is correct and low-risk:** Adding a model_validator to reject `debug=True` in production is a simple, isolated change with no side effects.

**Semantic target stability:** The `debug` field at line 267 and the `validate_admin_credentials` model_validator at line 329 are stable anchors. The fix should be added as a new model_validator or integrated into the existing `validate_admin_credentials` validator.

---

## Validated Findings (No Problems)

### DC-005 — Test compose has hardcoded fallback credentials instead of failing

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |

**Status:** VALIDATED as-is. No problems found.

**Evidence confirmed:**
- `docker-compose.test.yml` lines 67, 98: `JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_jwt_secret_key_for_integration_tests_32_chars}` — fallback values present.
- The finding itself acknowledges this is intentional for CI/CD.

**Analysis:** The test compose is designed as a standalone, self-contained environment for CI/CD and local testing. Fallback values ensure tests can run without external configuration. This is a standard and acceptable pattern for test environments. The production compose correctly uses `${VAR:?error}` enforcement.

The recommendation to document this intentional difference is reasonable but very low priority. The test compose file already has a header comment explaining its purpose (lines 1-5).

---

## Cross-Phase Conflicts

### DC-002 vs Phase 01 (BE-002) — JWT secret validation

**Related findings:** DC-002 (Phase 08) and BE-002 (Phase 01) both touch on configuration validation in `config.py`.

**Analysis:** No conflict. BE-002 addresses a test failure where `monkeypatch.delenv` does not prevent pydantic-settings from loading `.env` values. DC-002 addresses the weak default for `admin_password`. These are independent issues in the same file but with different root causes and different fixes.

### DC-003 vs Phase 01 (BE-002) — Debug mode and config validation

**Related findings:** DC-003 (Phase 08) and BE-002 (Phase 01).

**Analysis:** No conflict. DC-003 recommends adding a production guard for debug mode. BE-002 fixes a test that incorrectly assumes env var deletion results in `None`. The debug mode validator would be a new model_validator in `config.py` and does not interact with the JWT secret loading behavior addressed by BE-002.

### DC-004 vs Phase 05 (Health) — Health endpoint documentation

**Related findings:** DC-004 (Phase 08) and Phase 05 (Health API).

**Analysis:** No conflict. Phase 05 documents the health endpoints as public. DC-004 flags the unauthenticated detailed endpoint as a potential concern. The documentation and the code are consistent — both treat the endpoint as public. DC-004's adjusted severity (LOW, advisory) reflects that this is a design decision, not a bug.

---

## Rollout Safety Analysis

### Dependency Graph

```
DC-002 (admin password default) — independent, config.py only
DC-003 (debug mode validation) — independent, config.py only
DC-001 (.env.production template) — independent, docker/ directory only
DC-004 (health endpoint hardening) — independent, app.py only
DC-005 (test compose docs) — independent, docker/ directory only
```

### Rollout Ordering

All five findings are independent with no interdependencies. They can be executed in any order or in parallel.

1. **DC-002** (mandatory, MEDIUM) — Single-line default value change in `config.py`. Zero risk.
2. **DC-003** (mandatory, MEDIUM) — Add model_validator to `config.py`. Low risk. Should be tested to ensure it does not break existing test configurations that may use `debug=True` in test environments.
3. **DC-001** (advisory, LOW) — Template file update. Zero risk.
4. **DC-004** (advisory, LOW) — Error message sanitization in `app.py`. Low risk.
5. **DC-005** (advisory, LOW) — Documentation comment. Zero risk.

### Semantic Target Stability

| Finding | Anchor | Stability |
|---------|--------|-----------|
| DC-002 | `admin_password` field default at `config.py:297` | **Stable** — field definition, unlikely to change |
| DC-003 | `debug` field at `config.py:267` + `validate_admin_credentials` at `config.py:329` | **Stable** — well-defined config structure |
| DC-001 | `docker/.env.production` lines 9-14 | **Stable** — template file, changes only when new secrets are added |
| DC-004 | `detailed_health_check` at `app.py:263-301` | **Stable** — endpoint definition with clear boundaries |
| DC-005 | `docker-compose.test.yml` header | **Stable** — file-level comment |

---

## Validated Counts

| Category | Count |
|----------|-------|
| Total findings in phase | 5 |
| Reclassified | 2 (DC-001: SPEC-DEVIATION → DOC-UPDATE, severity HIGH → LOW; DC-004: severity HIGH → LOW, mandatory → advisory) |
| Validated mandatory fixes | 2 (DC-002, DC-003) |
| Validated advisory recommendations | 3 (DC-001 reclassified, DC-004 reclassified, DC-005) |
| Rejected | 0 |
| Merged | 0 |

### Mandatory Fixes
- **DC-002** — Admin password default value is weak (`"admin"` in `WEAK_PASSWORDS`). Change default to obviously-invalid placeholder.
- **DC-003** — Missing production debug mode validation. Add model_validator to reject `debug=True` when `environment == PRODUCTION`.

### Advisory Recommendations
- **DC-001** — `.env.production` template uses comment-only format while `.env.development` uses `CHANGE_ME_*` placeholders. Reclassified as DOC-UPDATE. Add placeholder keys or document the intentional difference.
- **DC-004** — `/health/detailed` is public by design but database error messages could leak internal details. Downgraded to LOW advisory. Sanitize error messages in production.
- **DC-005** — Test compose fallback credentials are intentional. Optionally document the difference from production compose.
