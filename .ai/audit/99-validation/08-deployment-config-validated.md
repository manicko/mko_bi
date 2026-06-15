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