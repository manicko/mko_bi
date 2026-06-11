---
name: 08-deployment-config-validated
description: Validated findings for configuration & lifecycle audit phase
agent: validator
validated: true
---

# Phase 08 Validation Report

**Validator:** validator
**Source:** .ai/audit/08-deployment-config/findings.md
**Date:** 2026-06-11

---

## Rejected Findings

### DC-001 — Rejected: Missing RATE_LIMITER_FAIL_CLOSED in Docker Compose App Environment

**Finding Type:** SPEC-DEVIATION → **Rejected**

**Evidence-based Rationale:**

The finding claims Docker Compose should declare `RATE_LIMITER_FAIL_CLOSED` for transparency. This is a **documentation clarity issue, not a spec deviation**.

**Verification:**

1. **Security checklist table** (docs/10-deployment/security-checklist.md:33): `RATE_LIMITER_FAIL_CLOSED` defaults to `false` (fail-open) in development, `true` (fail-closed) in production.

2. **Current implementation** (src/mkobi/config.py:362): `rate_limiter_fail_closed: bool = Field(default=True, alias="RATE_LIMITER_FAIL_CLOSED")` — **defaults to the secure value**.

3. **Production configuration** (docker/.env.production:38): `RATE_LIMITER_FAIL_CLOSED=true` — **explicitly set**.

4. **Security checklist verification section** (docs/10-deployment/security-checklist.md:79-81): Shows example `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}` as a *sample* of what verification might show, not a mandatory declaration.

**Analysis:**

- The default value in code IS the secure (fail-closed) value  
- The production `.env.production` explicitly sets `RATE_LIMITER_FAIL_CLOSED=true`
- When `ENV=production`, there is no ambiguity — the value is `true`
- The security checklist line 79-81 is a *verification example*, not a specification requirement for compose declaration

**Conclusion:** Rejection reason: **DOCUMENTATION CLARITY ISSUE, NOT SPEC DEVIATION** — the default is already secure, and production explicitly configures it. The security checklist documentation example should be clarified to distinguish example from requirement, but the code is correct.

---

## Reclassified Findings

### DC-004 — Reclassified: LOG_LEVEL Variable Name Mismatch

**Original Type:** DOC-UPDATE → **Reclassified to:** BEST-PRACTICE

**Rationale:**

**Verification:**

1. **Compose file** (docker/docker-compose.yml:110): `LOGGING__LEVEL: ${LOG_LEVEL:-INFO}` — references `LOG_LEVEL` (uppercase)

2. **Production env** (docker/.env.production:28): `LOGGING__LEVEL=INFO` — sets `LOGGING__LEVEL` (with underscores)

3. **Development override** (docker/docker-compose.override.yml:66): `LOGGING__LEVEL=DEBUG` — hardcoded override that bypasses the variable substitution issue

**Analysis:**

The compose file's `${LOG_LEVEL:-INFO}` substitution references a non-existent `LOG_LEVEL` variable. When `.env.production` is loaded:
- `LOGGING__LEVEL=INFO` is defined in the env file
- But compose substitutes `${LOG_LEVEL:-INFO}` which looks for `LOG_LEVEL` (not `LOGGING__LEVEL`)
- Since `LOG_LEVEL` is undefined, the fallback `INFO` is used
- This masks the variable name inconsistency

However, this is in the "Optional Security Hardening" section (security-checklist.md:60-67), not the "Required Production Variables" section. The current behavior (INFO level) is acceptable; changing to WARNING is a hardening recommendation, not a security requirement.

---

## Validated Findings

### DC-002 — Validated as SPEC-DEVIATION (Mandatory)

**Evidence:**

- `docker/docker-compose.yml:109`: `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}` — Default provides localhost placeholder
- `docs/10-deployment/security-checklist.md:58`: `CORS_ORIGINS` — Required in production (must be explicitly set)
- `src/mkobi/config.py:429-456`: Placeholder validation rejects `"http://localhost:3000"` in production at **startup**, not at Docker Compose level

**Analysis:**

The backend correctly validates and rejects placeholder CORS origins in production. However, the security checklist expects Docker Compose to **fail-fast using `${CORS_ORIGINS:?error}` syntax** (like `JWT__SECRET_KEY` and `DATABASE__PASSWORD`).

Finding is VALID: docker-compose.yml should use `${CORS_ORIGINS:?CORS_ORIGINS is required in production}` for clear fail-fast behavior at container startup instead of cryptic runtime error.

---

### DC-003 — Validated as BEST-PRACTICE (Advisory)

**Evidence:**

- `docs/10-deployment/security-checklist.md:64`: "`LOGGING__LEVEL | INFO | Set to `WARNING` to reduce log verbosity" — in "Optional Security Hardening" section

**Analysis:**

This is a valid advisory recommendation. The security checklist recommends `WARNING` for production, but the production template uses `INFO`. This is correctly classified as BEST-PRACTICE — a hardening suggestion, not a security requirement.

---

## Cross-Phase Conflicts

**None detected.** All findings are consistent with code implementation and documentation.

---

## Rollout Safety Assessment

| Finding ID | Dependency Risk | Rollout Concern |
|------------|-----------------|-----------------|
| DC-002 | Low | Changing `${CORS_ORIGINS:-[...]}` to `${CORS_ORIGINS:?...}` will cause startup failure if unset — this is the intended behavior per security checklist |
| DC-003 | Low | Log level change is non-breaking, affects only verbosity |
| DC-004 | Low | Variable name mismatch causes env file setting to be ignored — harmless but confusing |

---

## Summary

| Status | Count |
|--------|-------|
| Rejected | 1 (DC-001) |
| Reclassified | 1 (DC-004) |
| Validated Mandatory | 1 (DC-002) |
| Validated Advisory | 1 (DC-003) |

**TOTAL REJECTED:** DC-001 is invalid — no remediation required. The code defaults to the secure value and production explicitly configures it.

**TOTAL RECLASSIFIED:** DC-004 corrected to BEST-PRACTICE (harmless variable name inconsistency, not a security issue).