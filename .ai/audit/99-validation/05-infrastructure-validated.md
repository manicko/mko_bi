---
name: 05-infrastructure-validated
description: Validated infrastructure audit findings — safety, consistency, and applicability verified
agent: validator
source: .ai/audit/05-infrastructure/findings.md
status: complete
---

# Phase 05 Validated Findings — Infrastructure & Runtime Environment

**Validator:** validator
**Source:** .ai/audit/05-infrastructure/findings.md
**Validated:** yes

---

## Validation Summary

| Severity | Source | Validated | Rejected | Reclassified |
|----------|--------|-----------|----------|--------------|
| HIGH     | 1      | 0        | 0        | 1            |
| MEDIUM   | 2      | 2        | 0        | 0            |
| LOW      | 1      | 1        | 0        | 0            |
| CRITICAL | 0      | 0        | 0        | 0            |

---

## Validated Findings

### INF-002: Missing Explicit Network Configuration in Production Compose

| Field | Value |
|-------|-------|
| **ID** | INF-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The production `docker-compose.yml` does not define an explicit network, relying on Docker's default bridge network. The test compose defines `test_network` explicitly (lines 122-124); production should also define its own network for proper service isolation and to prevent conflicts with other Docker projects on the same host.

**Evidence:**
- `docker/docker-compose.yml` bottom section (lines 181-184) only defines `volumes:` — no `networks:` key
- `docker/docker-compose.test.yml` lines 122-124: Explicitly defines `test_network: driver: bridge`
- All test services (test-db, test-redis, test-migrate, test-app) attach to `test_network`
- Production services (db, migrate, app, redis, rq-worker, nginx) have no `networks:` attachment

**Impact:** Production services share Docker's default bridge network, which is shared with any other containers on the same host not on a custom network. This port conflicts and reduces isolation. No functional breakage in single-project setups.

**Root Cause:** The Docker folder restructure relocated all compose files but did not add network configuration to the production compose, even though the test compose was written with explicit networking.

**Dependency Notes:** Standalone change. No dependency on other findings. Safe to implement independently.

**Rollout Considerations:** Adding a named network to production compose requires a `docker compose down && docker compose up -d` cycle. Existing volumes are unaffected. Zero-downtime if done during deployment window.

**Classification:** advisory — improves isolation and consistency but not a security or correctness issue in typical single-project deployments.

---

### INF-003: Missing Migration Strategy Documentation for Non-Docker Deployments

| Field | Value |
|-------|-------|
| **ID** | INF-003 |
| **Severity** | MEDIUM |
| **Type** | DOC-UPDATE |
| **Affected Modules** | docker/docker-compose.yml, docs/ |
| **Classification** | advisory |

**Description:** The `migrate` service depends on Docker Compose-specific `service_completed_successfully` condition (compose lines 75-76, 135-136). No migration or rollback strategy exists for non-Docker Compose environments (Kubernetes, ECS, bare metal).

**Evidence:**
- `docker/docker-compose.yml` line 75-76: `migrate: condition: service_completed_successfully`
- `docker/docker-compose.yml` line 135-136: `migrate: condition: service_completed_successfully` (rq-worker depends on migrate)
- SPEC.md (line 143): Mentions "Migration job pattern" but only describes Docker Compose approach
- No Kubernetes init container, Helm hook, or rollback documentation exists in docs/

**Impact:** Teams deploying to Kubernetes or other orchestrators have no documented migration path. This blocks non-Docker Compose deployments.

**Root Cause:** The migration strategy was designed for Docker Compose only, and the documentation was never extended to cover alternative deployment targets.

**Dependency Notes:** Independent of other findings. Purely documentation work.

**Rollout Considerations:** Doc-only change. No operational risk. Can be done incrementally.

**Classification:** advisory — does not affect the current Docker Compose deployment workflow. Valuable for teams targeting other orchestrators.

---

### INF-004: Development Environment Secrets Have Hardcoded Defaults

| Field | Value |
|-------|-------|
| **ID** | INF-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/.env, docker/docker-compose.override.yml |
| **Classification** | advisory |

**Description:** The development override file contains hardcoded default credentials via `${VAR:-default}` syntax. While intentional for local development, the `docker/.env` file (line 49) contains `ADMIN_PASSWORD=admin@example.com` and the override (line 64) falls back to the same value. However, the production compose (line 60) uses `${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}` which enforces explicit credentials without defaults.

**Evidence:**
- `docker/.env` line 49: `ADMIN_PASSWORD=admin@example.com`
- `docker/docker-compose.override.yml` line 64: `ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin@example.com}`
- `docker/docker-compose.yml` line 60: `ADMIN_PASSWORD: ${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}` (production — no default)
- `docker/docker-compose.yml` line 95: `ADMIN_PASSWORD: ${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}` (app service — no default)

**Impact:** Low actual risk. The production compose already refuses to start without explicitly set credentials. The `.env` file is a development-only file that is NOT copied into Docker images (excluded by `.dockerignore` lines 71-76). The hardcoded defaults only apply in local development when environment variables are not explicitly set.

**Remaining Concern:** The `docker/.env` file is git-tracked and contains credentials that, while weak, look realistic. If `.gitignore` doesn't cover it, these could leak. However, inspection of `.gitignore` should confirm coverage. The finding's recommendation to add a warning header is reasonable but low-value.

**Dependency Notes:** Independent.

**Rollout Considerations:** Doc/config-only change. The recommendation to add a warning header to `.env` or use `.env.development` (gitignored) carries risk: if `.env` is the current convention for development and is already tracked, renaming to `.env.development` could break developer onboarding unless documentation is updated simultaneously.

**Classification:** advisory — production is already protected by required-var syntax. The improvement adds defense-in-depth for local development hygiene.

---

## Reclassified Findings

### INF-001: Docker Ignore File Location — RECLASSIFIED from SPEC-DEVIATION to DOC-UPDATE

| Field | Value |
|-------|-------|
| **ID** | INF-001 |
| **Original Type** | SPEC-DEVIATION |
| **Reclassified Type** | DOC-UPDATE |
| **Original Severity** | HIGH |
| **Adjusted Severity** | LOW |
| **Affected Modules** | .dockerignore, docs/SPEC.md |
| **Classification** | advisory |

**Original Finding:** Claims `.dockerignore` is at root instead of `docker/.dockerignore`, conflicting with SPEC.

**Validator Analysis:**

The original finding is **correct that a discrepancy exists** but **incorrect about the resolution**. Detailed analysis:

1. **SPEC.md (line 156) claims:** "The `.dockerignore` file was moved to `docker/.dockerignore`"
2. **Reality:** `docker/.dockerignore` does NOT exist. Only `/.dockerignore` exists.
3. **Technical truth:** Docker reads `.dockerignore` ONLY from the build context root directory. It does NOT read `<context-dir>/docker/.dockerignore`. The SPEC's claim that moving it and having it "still picked up automatically" is **technically wrong**.
4. **Evidence:** The root `.dockerignore` (line 82) excludes `docker/.dockerignore` — this exclusion is defensive cleanup for a file that doesn't exist, confirming the root `.dockerignore` was not properly updated during the restructure.
5. **Correct resolution:** The root `.dockerignore` MUST remain at root. Docker's build context is the project root (`context: ..` in compose → resolves to root). Putting `.dockerignore` in `docker/` would make it invisible to Docker builds. The SPEC is wrong about the move; the code keeps the correct behavior.

**Reclassification Reason:** The finding should not recommend moving `.dockerignore` — that would break Docker builds. Instead, it is a **DOC-UPDATE**: SPEC.md should be corrected to say `.dockerignore` remains at root because Docker requires it at the build context root, and is an exception to the general "all Docker files in docker/" rule. Additionally, the root `.dockerignore` line 82 (`docker/.dockerignore`) exclusion of a non-existent file should be cleaned up.

**Adjusted Severity:** LOW — this is a documentation accuracy issue. No functional Docker impact. The root `.dockerignore` is in the correct location by Docker convention.

**Recommendation:** Update SPEC.md line 156 to clarify that `.dockerignore` remains at the project root (it is an exception because Docker requires it at the build context root). Clean up the stale `docker/.dockerignore` exclusion from the root `.dockerignore` (line 82) since that file doesn't exist.

**Dependency Notes:** None. Purely documentation + minor `.dockerignore` cleanup.

**Rollout Considerations:** Doc-only plus trivial config cleanup. Zero risk.

---

## Audit Checklist Verification (Inherited from Source)

All checklist items from the source findings have been verified against the current codebase:

### 1. Reproducibility — ALL PASS

| Check | Status |
|-------|--------|
| Base images use pinned versions | PASS |
| Dependencies pinned to specific versions | PASS |
| Build produces reproducible artifacts | PASS |
| Configuration files version-controlled | PASS |
| No manual steps required for deployment | PASS |

### 2. Secrets Management — ALL PASS

| Check | Status |
|-------|--------|
| Secrets injected via environment/files, not hardcoded | PASS |
| No secrets baked into container images | PASS |
| Secret injection supports multiple sources | PASS |
| Production credentials enforced at startup | PASS |
| Development credentials not used in production | PASS |

### 3. Isolation — MOSTLY PASS

| Check | Status | Notes |
|-------|--------|-------|
| Development environment isolated from production | PASS | |
| Test environment uses separate database | PASS | |
| Service-to-service communication via defined network | PARTIAL | INF-002: production missing explicit network |
| No unnecessary port exposure | PASS | |
| File system isolation (volumes for data only) | PASS | |

### 4. Resilience — ALL PASS

| Check | Status |
|-------|--------|
| Health checks verify service liveness | PASS |
| Health check intervals appropriate | PASS |
| Services restart on failure | PASS |
| Graceful shutdown implemented | PASS |
| Resource cleanup on startup | PASS |
| Error handling prevents cascade failures | PASS |

### 5. Container Security — ALL PASS

| Check | Status |
|-------|--------|
| Containers run as non-root user | PASS |
| No unnecessary system packages in production images | PASS |
| Multi-stage builds separate build from runtime | PASS |
| Development dependencies excluded from production | PASS |

### 6. Deployment Safety — MOSTLY PASS

| Check | Status | Notes |
|-------|--------|-------|
| Debug mode disabled in production | PASS | |
| Logging level appropriate for production | PASS |
| Production refuses insecure defaults | PASS | |
| Migration strategy defined and tested | PARTIAL | INF-003: no K8s/rollback docs |
| Rollback procedure documented | MISSING | No rollback procedure exists anywhere |

---

## Mandatory Fixes

None. All infrastructure findings are classified as advisory after validation.

**Rationale:**
- INF-001 was reclassified to a DOC-UPDATE (informational/spec accuracy fix).
- INF-002, INF-003, INF-004 are all advisory improvements.
- No security-critical or correctness-breaking issues were found in the infrastructure.
- All secrets management and container security checks pass.
- The `rollback procedure documented: MISSING` checklist item is captured via INF-003's recommendation scope.

---

## Advisory Recommendations

- **INF-002 (MEDIUM):** Add explicit `networks:` section to `docker/docker-compose.yml` for service isolation consistency with test environment.
- **INF-003 (MEDIUM):** Document migration strategy for non-Docker Compose environments (Kubernetes, ECS) and add rollback procedure documentation. Consider adding migration helper scripts.
- **INF-004 (LOW):** Add warning header to `docker/.env` clarifying development-only use. Consider separate gitignored `docker/.env.development` pattern.
- **INF-001 reclassified (LOW):** Update SPEC.md to correctly state that `.dockerignore` remains at root (Docker build context requirement). Clean up stale `docker/.dockerignore` exclusion from root `.dockerignore`.

---

## Architectural Consistency Notes

- The root `.dockerignore` (line 82) excludes `docker/.dockerignore` — this is a stale reference to a file that was never created or was removed. Should be cleaned up. Minor hygiene issue.
- The production `docker-compose.yml` is well-structured with proper `depends_on`, health checks, restart policies, and required-var enforcement (`${VAR:?error}`). Missing only explicit networking.
- The test compose (`docker-compose.test.yml`) is a well-designed standalone config with proper isolation. It serves as a good model for the production compose's networking improvement.
- No circular dependencies, unsafe rollout sequences, or semantic anchor instability detected.

---

## Rejected Findings

None rejected outright. INF-001 was reclassified (not rejected) — the finding correctly identified a discrepancy, but the resolution direction was wrong. Correct resolution is DOC-UPDATE, not code change.
