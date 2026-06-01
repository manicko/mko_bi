# Validation Report — Phase 08: Configuration & Lifecycle

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/08-deployment-config/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted (unchanged) | Rejected | Reclassified | Merged |
|----------------|-------|----------------------|----------|--------------|--------|
| Mandatory | 1 | 1 | 0 | 0 | 0 |
| Advisory | 9 | 5 | 3 | 1 | 0 |
| **Total** | **10** | **6** | **3** | **1** | **0** |

---

## Rejected Findings

### DC-007: Rejected — No Action Required

| Field | Value |
|-------|-------|
| **ID** | DC-007 |
| **Original Severity** | LOW |
| **Original Type** | BEST-PRACTICE |
| **Rejection Reason** | Self-contradicting finding — the evidence confirms the code is already correct and sufficiently documented |

**Analysis:** The finding admits in its own description that "no code change needed — the behavior is correct" and that a comment explaining the superuser pattern "is already partially done." The finding was filed as a BEST-PRACTICE but its own recommendation is merely "could be more explicit" — this is below the threshold for an actionable audit finding. The `docker-compose.yml` already has a comment at line 37-39 explaining why the migrate service uses the postgres superuser. The `DATABASE__USER` values are intentionally different between services (least-privilege for `app`, superuser for `migrate`), which is a correct and well-established pattern. No further action needed.

---

### DC-008: Rejected — Standard Pattern, Not a Finding

| Field | Value |
|-------|-------|
| **ID** | DC-008 |
| **Original Severity** | LOW |
| **Original Type** | BEST-PRACTICE |
| **Rejection Reason** | The `tail -f /dev/null` pattern is the standard Docker approach for interactive test containers; the finding does not demonstrate actual harm |

**Analysis:** The finding describes a standard Docker Compose pattern for test containers. The `command: ["tail", "-f", "/dev/null"]` idiom is widely used to keep a container alive for interactive `docker compose exec` sessions. The finding itself notes that "the wasteful" database recreation only happens when the container starts — and the compose file's usage documentation (line 4: `docker compose -f docker/docker-compose.test.yml exec test-app uv run pytest tests/ -v`) already documents the correct workflow. No actual developer has reported this as a problem. The finding does not estimate time wasted or quantify the impact. This is an advisory suggestion that should be documented (if at all) as a comment in the compose file, not elevated to an audit finding.

---

### DC-004: Rejected — Spec-Compliant Design, Code Already Protects Production

| Field | Value |
|-------||
| **ID** | DC-004 |
| **Original Severity** | MEDIUM |
| **Original Type** | SPEC-DEVIATION |
| **Rejection Reason** | The `validate_admin_credentials` model validator in config.py (lines 285-301) already rejects weak passwords in production; the development defaults are intentional and properly gated |

**Analysis:** The finding claims the `"admin"` default in `config.py:248` and the `ADMIN_PASSWORD=admin@example.com` in `.env` files create a risk of weak credentials leaking to production. However, this misreads the actual protection mechanism:

1. **The `validate_admin_credentials` validator** (`config.py:285-301`) runs on every `Settings()` instantiation. In production (`environment == EnvironmentEnum.PRODUCTION`), it explicitly rejects any password in `WEAK_PASSWORDS` (which includes `"admin"` and `"admin@example.com"`). The application **refuses to start** with weak credentials in production.

2. **The `"admin"` default is intentionally minimal** — it ensures the application can start in development without requiring environment variables. This is a standard pattern for developer experience.

3. **The `.env` file is gitignored** (`gitignore:151`), so these defaults cannot leak to production through version control.

4. **Production deployments use `docker-compose.yml`** which enforces `${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}` — the password must be explicitly set.

The finding's recommendation to "remove the weak default" would break local development for new developers who clone the repo and run `docker compose up` without first creating a `.env`. The current design (weak dev defaults + production validator) is the correct pattern.

**Reclassified note:** This should not have been filed as a SPEC-DEVIATION because there is no specification being violated. The AGENTS.md guide states "Secrets only through environment variables" but does not prohibit development defaults, and the security-overview.md acknowledges development/staging environments have different security postures.

---

## Reclassified Findings

### DC-005: Reclassified `BEST-PRACTICE` → `SPEC-DEVIATION`

| Field | Original | Updated |
|-------|----------|---------|
| **ID** | DC-005 | DC-005 |
| **Severity** | MEDIUM | MEDIUM |
| **Type** | BEST-PRACTICE | **SPEC-DEVIATION** |
| **Classification** | advisory | advisory |
| **Status** | ACCEPTED (reclassified) | — |

**Rationale:** The finding describes `docker-compose.yml:101` setting `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}`. The AGENTS.md and SPEC.md both mandate that production configurations must not default to development values. The `docker-compose.yml` is the production compose file (per its own header: "Production configuration with multi-stage Dockerfile support"), and it includes a default that is only appropriate for development. This is a deviation from the documented deployment specification which requires explicit configuration of CORS origins in production. Reclassifying from BEST-PRACTICE to SPEC-DEVIATION because the finding identifies a concrete mismatch between the production compose file and the security requirements document (security-overview.md enforces no wildcard CORS, and production deployments should not default to localhost origins).

The recommendation to use `${CORS_ORIGINS:?CORS_ORIGINS is required}` (required variable, no default) is correct and aligns with how `JWT__SECRET_KEY`, `DATABASE__PASSWORD`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` are already handled in the same file.

---

## Cross-Phase Conflicts

### 1. DC-001 vs INF-02 (Phase 05) — Overlapping `.env` secret handling

**Finding IDs:** DC-001 (this phase) and INF-02 (Phase 05, validated)

**Nature:** Both findings address the `.env` files containing weak credentials. DC-001 focuses on the risk of accidental commit and recommends removing `.env` from the working tree. INF-02 (validated and reclassified as SPEC-DEVIATION) focuses on the `.env` file overriding production mode in Docker Compose.

**Resolution:** Complementary, not conflicting. DC-001's recommendation to remove `.env` from the working tree and rely on `.env.example` would also address INF-02's concern. Both findings should be implemented together. No conflict — they share the same root cause (`.env` exists with weak development values) but address different risk vectors (accidental commit vs production mode override).

**Merge candidate:** DC-001 and INF-02 could be merged into a single finding addressing "`.env` development defaults conflict with production deployment safety." However, since INF-02 is already validated and in a different phase, they should remain separate but cross-referenced.

### 2. DC-002 vs SEC-002 (Phase 04) — Both address defaults safety

**Finding IDs:** DC-002 (this phase) and SEC-002 (Phase 04, validated as SPEC-DEVIATION)

**Nature:** DC-002 addresses `RATE_LIMITER_FAIL_CLOSED` default inconsistency between code and Docker Compose. SEC-002 addresses weak default secrets in `.env` and `docker-compose.override.yml`. Both concern default values in configuration but address entirely different settings and different files.

**Resolution:** No conflict. Independent findings addressing different configuration keys.

### 3. DC-004 vs SEC-002 (Phase 04) — Overlapping weak admin password

**Finding IDs:** DC-004 (this phase, rejected) and SEC-002 (Phase 04, accepted)

**Nature:** Both findings address the `ADMIN_PASSWORD` weak default. DC-004 claims the `"admin"` default in `config.py` and `admin@example.com` in `.env` are risks. SEC-002 (validated) recommends adding JWT secret entropy validation and notes that weak defaults exist in override files.

**Note:** DC-004 was **rejected** in this validation because the `validate_admin_credentials` validator already protects production. SEC-002 remains accepted as it addresses JWT entropy (a different concern). There is no active conflict because the rejected finding is no longer actionable.

### 4. DC-010 vs DC-005 — Overlapping CORS origins issue

**Finding IDs:** DC-005 and DC-010 (both this phase)

**Nature:** DC-005 addresses `CORS_ORIGINS` default in `docker-compose.yml` (production compose). DC-010 addresses `cors_origins` in `app.yaml` (YAML config file) containing development values.

**Resolution:** These are independent manifestations of the same root cause: CORS origins with development values in configuration files. They address different files and different deployment vectors. No conflict — both recommendations (remove default from compose, remove `cors_origins` from YAML) are complementary.

---

## Rollout Safety Assessment

### DC-001 (Remove `.env` from working tree) — Rollout Risk: LOW

- **Risk:** Removing `.env` files would require developers to create their own `.env` from `.env.example`. This is a one-time inconvenience, not a breaking change, since the files are gitignored and cannot be restored from git.
- **Dependency:** None.
- **Mitigation:** Before removing `.env`, ensure `.env.example` has complete coverage of all required environment variables. Verify that `docker compose up` with `--env-file .env.example` works (may need adjustments since `.env.example` uses placeholder values like `change_me` for passwords).

### DC-002 (Change `rate_limiter_fail_closed` default to `True`) — Rollout Risk: LOW

- **Risk:** Changing the code-level default from `False` to `True` in `config.py:283` affects all non-Docker deployments (bare-metal, local development without Docker). Developers running outside Docker would now get fail-closed behavior, which could be confusing if Redis is unavailable.
- **Dependency:** None for the code change itself. The `docker-compose.override.yml` should explicitly set `RATE_LIMITER_FAIL_CLOSED=false` for development to maintain the current developer experience.
- **Mitigation:** Add `RATE_LIMITER_FAIL_CLOSED: "false"` to the `app` service environment in `docker-compose.override.yml` to preserve development behavior.

### DC-003 (Set `DEBUG=true` in development) — Rollout Risk: NONE

- **Risk:** Purely additive. Setting `DEBUG=true` in `docker-compose.override.yml` (which currently has no `DEBUG` override) only affects the development Docker deployment. No production impact.
- **Dependency:** None.
- **Mitigation:** None needed. This is a development convenience improvement.

### DC-005 (Make `CORS_ORIGINS` required in production compose) — Rollout Risk: MEDIUM

- **Risk:** Changing `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}` to `CORS_ORIGINS: ${CORS_ORIGINS:?CORS_ORIGINS is required}` means any production deployment that doesn't explicitly set `CORS_ORIGINS` will fail to start. This is the intentional behavior, but it's a breaking change for anyone currently relying on the default.
- **Dependency:** Documentation (`deployment.md`) must be updated to list `CORS_ORIGINS` as a required production environment variable.
- **Mitigation:** Add a comment in `docker-compose.yml` near the `CORS_ORIGINS` enforcement pointing to the deployment docs. Ensure CI/CD templates and deployment guides include `CORS_ORIGINS`.

### DC-006 (Set `AUTO_MIGRATE: "false"` for rq-worker in override) — Rollout Risk: NONE

- **Risk:** The `rq-worker` in `docker-compose.yml` already has `AUTO_MIGRATE: "false"` (line 158). The override doesn't override this value. Adding an explicit `AUTO_MIGRATE: "false"` in the override is redundant but clarifying. No functional change.
- **Dependency:** None.
- **Mitigation:** None needed. This is a defensive documentation improvement.

### DC-009 (Align `JWT__ACCESS_TOKEN_EXPIRE_MINUTES`) — Rollout Risk: NONE

- **Risk:** The effective value is 30 (from `.env`, which takes priority over YAML). Aligning `app.yaml` to match `.env` (changing from 15 to 30) is a documentation-only change — the 15 in YAML is never used as long as the environment variable is set.
- **Dependency:** None.
- **Mitigation:** Decide on the correct value (15 or 30) based on security requirements. 15 minutes is more secure; 30 minutes is more convenient. Update both `.env` and `app.yaml` to match.

### DC-010 (Remove `cors_origins` from `app.yaml`) — Rollout Risk: LOW

- **Risk:** The `app.yaml` `cors_origins` are only used when no `CORS_ORIGINS` environment variable is set. Since `docker-compose.yml` and `.env` both set it, the YAML values are never used in Docker deployments. Removing them eliminates a potential confusion source.
- **Dependency:** None.
- **Mitigation:** Verify that no deployment path relies on YAML-only configuration (e.g., running without Docker or without `.env` files). The `Settings` class default for `cors_origins` is `[]` (empty list, line 270), so removing from YAML is safe — production environments must always set `CORS_ORIGINS` explicitly.

---

## Mandatory Fixes (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| DC-001 | HIGH | SPEC-DEVIATION | `.env` files exist in working tree with weak credentials; risk of accidental commit |

## Advisory Recommendations (Accepted)

| ID | Severity | Type | Issue | Rollout Risk |
|----|----------|------|-------|--------------|
| DC-002 | MEDIUM | SPEC-DEVIATION | `rate_limiter_fail_closed` defaults to `False` (fail-open) in code, `true` in Docker Compose | LOW |
| DC-003 | LOW | BEST-PRACTICE | `DEBUG=false` in development environment reduces developer productivity | NONE |
| DC-005 | MEDIUM | SPEC-DEVIATION (reclassified) | `CORS_ORIGINS` defaults to localhost in production compose | MEDIUM |
| DC-006 | LOW | BEST-PRACTICE | `rq-worker` in override lacks explicit `AUTO_MIGRATE: "false"` | NONE |
| DC-009 | LOW | BEST-PRACTICE | `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` differs between `.env` (30) and `app.yaml` (15) | NONE |
| DC-010 | LOW | BEST-PRACTICE | `app.yaml` contains development-only `cors_origins` values | LOW |

---

## Summary

- **10 findings input**, **6 accepted** (1 mandatory + 5 advisory after reclassification), **3 rejected**, **1 reclassified** (DC-005: BEST-PRACTICE → SPEC-DEVIATION).
- **Rejected:** DC-004 (spec-compliant design with production validator), DC-007 (self-sufficient code, comment already exists), DC-008 (standard Docker pattern, no measurable harm).
- **Cross-phase conflicts:** DC-001 overlaps with INF-02 (Phase 05) — complementary, not conflicting. DC-010 and DC-005 share a root cause (CORS origins in config files) but are independent findings.
- **Highest rollout risk:** DC-005 (making CORS_ORIGINS required — breaks deployments relying on the default).
- **No merges** — no findings within this phase share duplicate root causes.
- **Key recommendation:** DC-005 should be implemented together with DC-010 (both address CORS origins configuration), and DC-002 should include an explicit `RATE_LIMITER_FAIL_CLOSED=false` in `docker-compose.override.yml` to preserve developer experience.
