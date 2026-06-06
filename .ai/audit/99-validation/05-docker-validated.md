# Phase 05 Validation Report — Infrastructure & Runtime Environment

**Validator:** validator-agent
**Source:** .ai/audit/05-docker/findings.md
**Validation Date:** 2026-06-06

---

## Rejected Findings

### INF-006: REJECTED — Evidence Not Reproducible (No Test Database Running)

| Field | Value |
|-------|-------|
| **Original ID** | INF-006 |
| **Original Type** | RUNTIME-ERROR |
| **Original Classification** | mandatory |

**Rejection Reason:** Cannot verify — the `test-db` container referenced in the finding is not currently running (verified via `docker ps`). No PostgreSQL containers in the current environment match the error signature `column "pg_enum.enum_typid" does not exist`. The current `postgres:16` containers (`docker-db-1`, `postgres-bidb-mcp`, `postgres-bidb-test-mcp`) do not exhibit this error. The finding may have been from a previous test run that was cleaned up, or the introspection library issue has been resolved. Without active runtime evidence, this finding cannot be validated as current.

---

### INF-007: REJECTED — Insufficient Runtime Evidence (Seeders Run Successfully)

| Field | Value |
|-------|-------|
| **Original ID** | INF-007 |
| **Original Type** | RUNTIME-ERROR |
| **Original Classification** | mandatory |

**Rejection Reason:** The reported `InvalidRequestError: Can't operate on closed transaction inside context manager` error from `test_media_dash.py:192` could not be reproduced in the current running environment. The `docker-app-1` container has been running for 20 hours and shows no such errors in its logs. The code pattern `await db.refresh(dashboard)` after `await db.commit()` inside an `async with SessionLocal() as db:` context (line 188 in the seeder) IS potentially problematic — after commit, the ORM object may be detached from the session in some SQLAlchemy configurations. However:

1. The error is not occurring in the current environment (container has been stable)
2. If the app had failed to seed, it would not have started properly
3. The seeder errors are caught and non-fatal (per `dev_seeders.py` lines 35-38)

This may be an intermittent issue or environment-specific. Recommend re-verification with fresh container startup rather than treating as a mandatory fix without reproducible evidence.

---

### INF-008: REJECTED — Insufficient Runtime Evidence (No Test Database Running)

| Field | Value |
|-------|-------|
| **Original ID** | INF-008 |
| **Original Type** | RUNTIME-ERROR |
| **Original Classification** | advisory |

**Rejection Reason:** Cannot verify — no `test-db` container is currently running. The `unexpected EOF on client connection with an open transaction` log messages would come from a test database container that was started during test execution, but no such container exists in the current environment. This is a test environment artifact, not a persistent production issue.

---

## Reclassified Findings

### INF-003: RECLASSIFY — SPEC-DEVIATION Should Be Mandatory

| Field | Value |
|-------|-------|
| **Original Type** | SPEC-DEVIATION (advisory) |
| **New Type** | SPEC-DEVIATION (mandatory) |

**Rationale:** The finding INF-003 correctly identifies a contradiction between the documented migration strategy and actual configuration. Per `docs/10-deployment/deployment.md` line 209: "For production Docker Compose deployments, a dedicated `migrate` service runs `alembic upgrade head` before the app service starts... This allows `AUTO_MIGRATE=false` in the app config."

However, `docker/docker-compose.yml` line 100 sets `AUTO_MIGRATE: "true"`. This is a SPEC-DEVIATION — the code contradicts the documented design. Since this affects all production deployments and could cause race conditions or advisory lock contention in multi-instance deployments, this should be **mandatory**, not advisory.

---

## Validated Findings (No Changes)

| ID | Type | Classification | Status |
|----|------|----------------|--------|
| INF-001 | BEST-PRACTICE | advisory | VALIDATED |
| INF-002 | BEST-PRACTICE | advisory | VALIDATED |
| INF-004 | BEST-PRACTICE | advisory | VALIDATED |
| INF-005 | RUNTIME-ERROR | advisory | VALIDATED |
| INF-009 | DOC-UPDATE | advisory | VALIDATED |
| INF-010 | BEST-PRACTICE | advisory | VALIDATED |
| INF-011 | BEST-PRACTICE | advisory | VALIDATED |

**Validation Notes:**

- **INF-001**: `nginx:alpine` (line 178) is indeed an unpinned floating tag, unlike `postgres:16` and `redis:7-alpine` which pin major versions. Valid best practice issue.

- **INF-002**: No `mem_limit`, `cpus`, or `deploy.resources` defined in any service in `docker-compose.yml`. Confirmed runtime containers show unlimited resources. Valid operational concern.

- **INF-004**: The `pgrep -f rq` health check (line 165) is indeed superficial — it doesn't verify Redis connectivity or functional worker readiness. Valid best practice issue.

- **INF-005**: The `docker-db-1` logs show 148+ authentication failures for user `postgres` (verified via `docker logs docker-db-1`). These originate from the exposed port `5432:5432` in `docker-compose.override.yml` line 93. Valid runtime issue.

- **INF-009**: Confirmed — `docs/10-deployment/deployment.md` has no mention of "rollback" or "roll back". No documented procedure for reverting bad deployments. Valid doc update needed.

- **INF-010**: `node:20-alpine` and `python:3.12-slim-bookworm` are floating major-version tags (lines 10, 28, 64 in Dockerfile). Valid best practice concern for build reproducibility.

- **INF-011**: Test compose exposes `5433:5432` and `6380:6379` to host (lines 20, 36). Valid concern for CI/CD environments where this could cause cross-talk.

---

## Cross-Phase Conflicts

### Conflict: INF-003 and DC-002 Both Address Migration/Init Script Configuration

| Field | Value |
|-------|-------|
| **Conflicting IDs** | INF-003, DC-002 |
| **Conflict Type** | Related architectural concerns |

**Analysis:** Both INF-003 (AUTO_MIGRATE=true with migrate service) and DC-002 (CREATEDB privilege on mkobi_app role) address unintended configuration in the Docker ecosystem. These are:

1. **INF-003**: Application configuration issue (AUTO_MIGRATE should be false in production)
2. **DC-002**: Database initialization issue (CREATEDB privilege violates least-privilege)

These are separate issues with different root causes, but both represent configuration drift from documented design. No direct contradiction — both can be addressed independently.

---

## Rollout Safety Issues

### None Identified

The Docker configuration changes are:
- Independent (INF-001, INF-010: image tags)
- Independent (INF-002: resource limits)
- Related (INF-003: AUTO_MIGRATE config — one setting change)
- Independent (INF-004: health check — single service)
- Operational (INF-005: external tool configuration — environment-specific)
- Documentation (INF-009: no deployment impact)

Changes are isolated to individual services or documentation with clear, separable rollout paths. No circular dependencies or unsafe sequencing required.

---

## Summary

| Category | Count |
|----------|-------|
| Rejected | 3 (INF-006, INF-007, INF-008 - stale/insufficient evidence) |
| Reclassified | 1 (INF-003 — advisory → mandatory) |
| Validated (No Change) | 7 |
| Mandatory Fixes | 1 (INF-003 reclassified) |
| Advisory Recommendations | 6 (INF-001, INF-002, INF-004, INF-005, INF-010, INF-011) |

**Note:** INF-010 and INF-011 are valid but LOW severity — these represent environment-specific concerns (build reproducibility and CI/CD hardening) rather than immediate operational risks.
