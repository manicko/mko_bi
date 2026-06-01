# Validation Report — Phase 05: Infrastructure & Runtime Environment

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/05-docker/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted (unchanged) | Rejected | Reclassified | Merged |
|----------------|-------|----------------------|----------|--------------|--------|
| Mandatory | 1 | 1 | 0 | 0 | 0 |
| Advisory | 7 | 6 | 0 | 1 | 0 |
| **Total** | **8** | **7** | **0** | **1** | **0** |

---

## Reclassified Findings

### INF-02: Reclassified `RUNTIME-ERROR` → `SPEC-DEVIATION`

| Field | Original | Updated |
|-------|----------|---------|
| **ID** | INF-02 | INF-02 |
| **Severity** | HIGH | HIGH |
| **Type** | RUNTIME-ERROR | SPEC-DEVIATION |
| **Classification** | mandatory | mandatory |
| **Status** | ACCEPTED (reclassified) | — |

**Rationale:** The finding is CONFIRMED by runtime evidence — `docker exec docker-app-1` returns `ENV=development` and `AUTO_MIGRATE=true`, and `docker compose config` resolves all environment variables to development values (`JWT__SECRET_KEY: dev-secret-key-for-local-development`, `DATABASE__PASSWORD: 1234`, `ADMIN_PASSWORD: admin@example.com`). The `.env` file at project root sets `ENV=development` which overrides the production compose's `${ENV:-production}` default, causing the production-targeted container to run in development mode with weak credentials.

However, the finding type `RUNTIME-ERROR` is inaccurate. The stack does **start** successfully — containers do not crash or refuse to start. The problem is that it starts **in the wrong mode** with weak credentials, which is a configuration/deviation issue, not a runtime crash. The `RUNTIME-ERROR` type should be reserved for findings where containers fail to start or services crash at runtime.

Reclassifying to `SPEC-DEVIATION` because: the docker-compose.yml design (using `${ENV:-production}` with `VAR:?` enforcement) explicitly intends production mode by default, but the presence of `.env` in the repository root (committed to git, as confirmed by file existence) subverts this design. This is a deviation from the documented deployment pattern, not a runtime error.

**Evidence (runtime-confirmed):**
- `docker exec docker-app-1 sh -c 'echo $ENV'` → `development`
- `docker exec docker-app-1 sh -c 'echo $AUTO_MIGRATE'` → `true`
- `docker compose config` resolves `ENV: development`, `AUTO_MIGRATE: "true"`, all secrets to development defaults

---

## Rejected Findings

**None.** All 8 findings describe real, applicable issues in the Docker infrastructure.

---

## Reclassified INF-02 — Detailed Assessment

### Sub-claim: `.env` referenced via `--env-file .env`

**Partially inaccurate.** The docker-compose.yml files do not themselves contain `--env-file .env` directives. The `--env-file .env` flag appears in `docs/11-guides/docker.md` (all 21 command examples in the documentation). However, Docker Compose **automatically** loads `.env` from the project root when running `docker compose up` from the project directory — the explicit `--env-file .env` in docs is redundant for the default case. The real issue is that `.env` exists in the repo root with development values and is automatically loaded regardless of the compose file's production intent.

**Corrected recommendation:** Instead of "remove or rename the default .env," the more precise fix is:
1. Remove `ENV=development` from `.env` (or set `ENV=production` as the default)
2. Ensure `.env` does not contain weak default credentials (use placeholder values like `change_me` as `.env.example` already does)
3. The `.env` file is gitignored in practice (`.env` is a gitignore pattern), so the risk is local development convenience vs production safety when the file is copied to a deployment target

---

## Cross-Phase Conflicts

### 1. INF-02 vs Phase 04 (SEC-002) — Overlapping weak default secrets

INF-02 reports that `.env` contains weak credentials (`DATABASE__PASSWORD=1234`, `JWT__SECRET_KEY=dev-secret-key-for-local-development`) and that `docker-compose.override.yml` provides fallback weak values. Phase 04 (SEC-002, validated) reports the same issue from the security angle, noting that `docker/.env` contains weak values and recommending startup validation for JWT secret key entropy.

**Assessment:** Complementary, not conflicting. INF-02 focuses on the Docker Compose mechanism (`.env` loaded automatically, overriding production defaults). SEC-002 focuses on the security mechanism (weak JWT secrets, no entropy validation). Both recommend removing weak defaults; INF-02's fix is configuration-level while SEC-002's fix is code-level (add entropy validation to `JWTSettings`). These fixes are orthogonal and both needed.

### 2. INF-04 vs Phase 03 (DB-01/DB-02) — Migration pattern

INF-04 reports `AUTO_MIGRATE: "true"` in production compose conflicts with the dedicated `migrate` service. Phase 03 (DB-01) reports branched migrations that should be squashed. These are independent — the `AUTO_MIGRATE` setting affects runtime behavior, while DB-01 affects migration DDL correctness. No conflict.

### 3. INF-04 vs Deployment Docs (deployment.md line 194)

The finding claims `docs/10-deployment/deployment.md` line 194 describes setting `AUTO_MIGRATE=false` when using the migration job pattern. **Upon verification**, deployment.md line 194 actually states: *"`AUTO_MIGRATE=true` — runs `alembic upgrade head` on container startup (default in docker-compose.yml)"* and line 196 describes the migration job pattern where the `migrate` service runs first and `AUTO_MIGRATE=false` is possible. The finding's line reference is imprecise — the document doesn't mandate `AUTO_MIGRATE=false` for the migration job pattern; it notes it as a possibility. This is a minor evidence error in the finding but doesn't invalidate the core recommendation (redundant migrations waste resources and bloat logs).

---

## Rollout Safety Assessment

### INF-02 (Development .env overrides production mode) — Rollout Risk: LOW

- **Risk:** Minimal. Modifying `.env` to set `ENV=production` and removing weak defaults does not affect running containers (requires `docker compose down && docker compose up -d` to take effect). The `.env` file is meant to be environment-specific.
- **Dependency:** None. Self-contained change to `.env` (local) and `docker-compose.override.yml` (dev defaults).
- **Mitigation:** Deployments that use `.env.production` or environment variable injection (CI/CD, K8s) are unaffected. Only local development using the default `.env` is affected, and the fix is to remove development-only values.

### INF-01 (Pin base images to SHA256 digests) — Rollout Risk: LOW

- **Risk:** Pinning to SHA256 requires updating digests periodically as base images are patched. Without automated tooling (Dependabot, Renovate), this is a manual maintenance burden.
- **Dependency:** None. Self-contained change to `docker/Dockerfile`.
- **Mitigation:** Add Renovate or Dependabot to automate digest updates. Without automation, this recommendation has poor ROI for a single-developer project.

### INF-03 (Add health checks for rq-worker and nginx) — Rollout Risk: LOW

- **Risk:** Adding health checks to services that currently have `profiles: [production]` (and are therefore not running in dev/test) has no effect on development.
- **Dependency:** None. Self-contained change to `docker/docker-compose.yml`.
- **Mitigation:** rq-worker health check using `uv run rq info --url redis://redis:6379/0` assumes `uv` is available in the rq-worker container — it is, since the rq-worker uses the `prod` target which has `uv` installed.

### INF-04 (Set AUTO_MIGRATE=false with migrate service) — Rollout Risk: LOW

- **Risk:** Setting `AUTO_MIGRATE: "false"` in production compose when the `migrate` service is already configured is safe. Migrations will run exactly once via the `migrate` service.
- **Dependency:** The `migrate` service must be running and healthy before `app` starts. Already enforced by `depends_on: migrate: condition: service_completed_successfully`.
- **Mitigation:** Test the change in a staging environment to verify migrations run correctly via the dedicated service.

### INF-05 (Redis with authentication) — Rollout Risk: MEDIUM

- **Risk:** Adding `requirepass` to Redis breaks all services that connect without a password. The `rq-worker` connects via `redis://redis:6379/0` — this URL format doesn't include a password. All services (app, rq-worker) that use Redis must be updated to include the password in the connection URL (`redis://:password@redis:6379/0`).
- **Dependency:** The application's Redis connection configuration (`REDIS__HOST`, `REDIS__PORT`, and any password field in settings) must be updated alongside the compose change.
- **Mitigation:** Add `REDIS__PASSWORD` to settings, update all Redis connection URLs, then mount the custom `redis.conf` with `requirepass`. This is a 3-file minimum change (compose, redis.conf, config).

### INF-06 (PostgreSQL trust auth) — Rollout Risk: LOW

- **Risk:** Changing `pg_hba.conf` from `trust` to `scram-sha-256` for local connections in a container where only postgres runs is purely defense-in-depth. No functional change.
- **Dependency:** None.
- **Mitigation:** Advisory only for containers. No action required for current deployment model.

### INF-07 (Image size optimization) — Rollout Risk: MEDIUM

- **Risk:** Switching to `python:3.12-alpine` introduces musl libc compatibility issues with Polars (which uses native Rust libraries that depend on glibc). This could cause runtime crashes or subtle data corruption.
- **Dependency:** Must verify all Python binaries (Polars, asyncpg, numpy if present) work on musl.
- **Mitigation:** Do NOT switch to Alpine without thorough integration testing of data processing pipelines. The current `slim-bookworm` image is the safer choice.

### INF-08 (Explicit network configuration) — Rollout Risk: LOW

- **Risk:** Adding explicit networks to a running compose stack requires recreating containers (`docker compose down && docker compose up -d`).
- **Dependency:** None.
- **Mitigation:** Apply during a maintenance window. Containers will get new IP addresses on the named network.

---

## Mandatory Fixes (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| INF-02 | HIGH | SPEC-DEVIATION | Development `.env` file with weak credentials overrides production mode in Docker Compose |

## Advisory Recommendations (Accepted)

| ID | Severity | Type | Issue | Rollout Risk |
|----|----------|------|-------|--------------|
| INF-01 | MEDIUM | BEST-PRACTICE | Base images use floating tags (not pinned to digest) | LOW |
| INF-03 | MEDIUM | BEST-PRACTICE | No health checks on `rq-worker` and `nginx` services | LOW |
| INF-04 | LOW | BEST-PRACTICE | Redundant migration execution — `AUTO_MIGRATE=true` + dedicated migrate service | LOW |
| INF-05 | MEDIUM | BEST-PRACTICE | Redis runs without configuration file or authentication | MEDIUM |
| INF-06 | MEDIUM | BEST-PRACTICE | PostgreSQL uses `trust` auth for local connections | LOW |
| INF-07 | LOW | BEST-PRACTICE | Production image is 706MB — optimization possible | MEDIUM |
| INF-08 | LOW | BEST-PRACTICE | Production compose lacks explicit network configuration | LOW |

---

## Summary

- **8 findings validated**, 0 rejected, 1 reclassified (INF-02: RUNTIME-ERROR → SPEC-DEVIATION).
- **No cross-phase conflicts** with Phases 01-04. INF-02 partially overlaps with SEC-002 (both address weak default secrets) but the fixes are complementary, not conflicting.
- **No merges** — no findings share duplicate root causes.
- **1 mandatory fix** (INF-02), **7 advisory recommendations** (INF-01, INF-03 through INF-08).
- **Highest rollout risk:** INF-05 (Redis authentication — requires coordinated changes across service URLs and configs) and INF-07 (Alpine switch — musl compatibility risk).
- **Conservative recommendation:** Only INF-02 should be treated as mandatory. All other findings are advisory infrastructure improvements that should be prioritized by operational ROI, not urgency.
