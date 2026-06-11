---
name: audit-findings
description: Deployment configuration audit findings for mkobi BI Dashboard
agent: auditor
alwaysApply: false
---

# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### DC-001: Missing RATE_LIMITER_FAIL_CLOSED in Docker Compose App Environment

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | mandatory |

**Description:** The security checklist (`docs/10-deployment/security-checklist.md:80`) specifies that the `app` service environment block in Docker Compose must explicitly include `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}`. However, `docker-compose.yml` does NOT set this variable in the app service environment block (lines 90-111), making the documented verification step impossible to satisfy.

**Evidence:**
- `docs/10-deployment/security-checklist.md:80`: Shows expected: `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}`
- `docker/docker-compose.yml:90-111`: Environment block does NOT include `RATE_LIMITER_FAIL_CLOSED`
- While `config.py:362` defaults to `True`, the compose file should declare this for transparency and verification compliance

**Recommendation:** Add `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}` to the app service environment in `docker-compose.yml` to match the security checklist specification and enable the documented verification command to work correctly.

---

### DC-002: CORS_ORIGINS Default Value in Production Compose

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | mandatory |

**Description:** The `docker-compose.yml:109` provides a default value `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}` for production deployments. While the app's CORS validation (config.py:446-456) correctly rejects placeholder origins in production, this default creates a confusing UX where Docker Compose succeeds but the app fails on startup with a non-obvious error message. The security checklist mandates explicit production configuration.

**Evidence:**
- `docker/docker-compose.yml:109`: Provides default `["http://localhost:3000"]` which is a placeholder
- `docs/10-deployment/security-checklist.md:58`: `CORS_ORIGINS | Allowed CORS origins (JSON array) | Yes` — Required in production
- `src/mkobi/config.py:430-436`: `CORS_ORIGINS_PLACEHOLDERS` includes `"http://localhost:3000"` — validation catches this but the error message is cryptic

**Recommendation:** Remove the default value and use required syntax: `CORS_ORIGINS: ${CORS_ORIGINS:?CORS_ORIGINS is required in production}`. This ensures fail-fast at the Docker Compose level with a clear error message, matching the pattern used for `JWT__SECRET_KEY` and `DATABASE__PASSWORD`.

---

### DC-003: Logging Level Defaults to INFO Instead of WARNING in Production Template

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/.env.production |
| **Classification** | advisory |

**Description:** The security checklist recommends `LOGGING__LEVEL=WARNING` for production to reduce log verbosity and prevent potential sensitive information leakage in logs. However, `docker/.env.production:28` sets `LOGGING__LEVEL=INFO` which provides more verbose logging than recommended.

**Evidence:**
- `docs/10-deployment/security-checklist.md:64`: "LOGGING__LEVEL | INFO | Set to `WARNING` to reduce log verbosity"
- `docker/.env.production:28`: `LOGGING__LEVEL=INFO` — Does not follow recommended hardening
- Test environment correctly uses `WARNING` (docker-compose.test.yml:144)

**Recommendation:** Update `docker/.env.production` to use `LOGGING__LEVEL=WARNING` to align with the security checklist recommendation.

---

### DC-004: Missing LOG_LEVEL default in Production Compose Matches No Default

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The `docker-compose.yml:110` uses `${LOG_LEVEL:-INFO}` with a default of INFO. Combined with `docker/.env.production` setting INFO, the effective default is INFO. When `docker/.env.production` is updated to WARNING, this compose default would still override it if `LOG_LEVEL` is not explicitly set. The compose file should not provide a production-default.

**Evidence:**
- `docker/docker-compose.yml:110`: `LOGGING__LEVEL: ${LOG_LEVEL:-INFO}` — Default contradicts security recommendation
- `docker/.env.production:28`: Sets `LOGGING__LEVEL=INFO` (would be updated to WARNING per DC-003)

**Recommendation:** Either remove the default (use `${LOG_LEVEL:?LOG_LEVEL is required}`) or change the fallback to `${LOG_LEVEL:-WARNING}` to align with production best practices.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 1 |

## Mandatory Fixes

- DC-001: Missing RATE_LIMITER_FAIL_CLOSED in Docker Compose App Environment
- DC-002: CORS_ORIGINS Default Value in Production Compose

## Advisory Recommendations

- DC-003: Logging Level Defaults to INFO Instead of WARNING in Production Template
- DC-004: Missing LOG_LEVEL default in Production Compose Matches No Default

---