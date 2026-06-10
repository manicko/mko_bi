# Phase 05 Audit Findings — Infrastructure & Runtime Environment

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INF-01: PostgreSQL 18 Collation Refresh Error in Docker Container Logs

| Field | Value |
|-------|-------|
| **ID** | INF-01 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | docker/docker-compose.test.yml, docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The PostgreSQL 18 container logs show repeated `REFRESH COLLATION_VERSION` errors during initialization. PostgreSQL 18 introduced `ALTER DATABASE ... REFRESH COLLATION_VERSION` but the Docker image may be running a PostgreSQL version that doesn't fully support this syntax, or the initialization process is attempting this command inappropriately. The builtin locale provider was supposed to provide immutable collation but these errors indicate a compatibility issue.

**Evidence:**
```
test-db  | 2026-06-09 14:44:46.010 UTC [30943] ERROR:  syntax error at or near "COLLATION_VERSION" at character 34
test-db  | 2026-06-09 14:44:46.010 UTC [30943] STATEMENT:  ALTER DATABASE template1 REFRESH COLLATION_VERSION
```

Multiple similar errors occur during container startup (40+ instances in logs).

**Recommendation:** Investigate whether the PostgreSQL 18-bookworm image properly supports the builtin locale provider and `REFRESH COLLATION_VERSION` command. If this is a pre-release or beta compatibility issue, consider: (1) pinning to a specific stable PostgreSQL 18 minor version, or (2) using the `libc` locale provider if the builtin provider has issues. The errors appear non-fatal (database still starts and works) but indicate configuration drift.

---

### INF-02: Unclear Docker Environment File Configuration

| Field | Value |
|-------|-------|
| **ID** | INF-02 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | docker/.env*, .env, docs/11-guides/docker.md |
| **Classification** | advisory |

**Description:** Documentation in `docker.md` references multiple environment files inconsistently. The root `.env` file exists with actual values, while `docker/.env.development` and `docker/.env.production` are template/example files with placeholder values. The documentation suggests using `--env-file docker/.env.development` but that file contains `CHANGE_ME` placeholders that would fail at runtime. Users must copy and fill in values before use.

**Evidence:**
- `docker/.env.development` line 10: `DATABASE__PASSWORD=CHANGE_ME_GENERATE_STRONG_SECRET` (placeholder)
- `docker/.env.production` line 10-14: Comments show required secrets but no actual values
- `docker.md` line 162-166: Shows usage with `docker/.env.production` but doesn't clarify values must be filled
- Root `.env` exists with actual development values

**Recommendation:** Update documentation to clearly indicate that `docker/.env.development` is a template requiring manual copy-and-edit before use, and clarify the difference between the root `.env` (working development values) and `docker/.env*.` files (templates).

---

### INF-03: Frontend Dependencies Use Floating Version Ranges Without Lock File in Docker Build

| Field | Value |
|-------|-------|
| **ID** | INF-03 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/package.json, .dockerignore |
| **Classification** | advisory |

**Description:** The `frontend/package.json` uses floating version ranges (e.g., `^19.2.5`, `^7.75.0`) for dependencies, which violates the reproducibility principle. While `package-lock.json` exists and pins exact versions, the `.dockerignore` file excludes `package-lock.json` at line 69, causing builds to use floating versions instead of pinned ones. The Dockerfile frontend-builder stage uses `npm install` without the lock file.

**Evidence:**
- `frontend/package.json` line 26: `"react": "^19.2.5"` (floating version)
- `.dockerignore` line 69: `frontend/package-lock.json` (excluded from build)
- `Dockerfile` line 18: `RUN npm install` (uses package.json without lock file due to .dockerignore)

**Recommendation:** Remove `frontend/package-lock.json` from `.dockerignore` to ensure reproducible builds. The lock file should be included in Docker builds to guarantee the same dependency versions used during development are used in production builds. Alternatively, copy the lock file before `npm install` in the Dockerfile.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 1 |

## Advisory Recommendations

1. INF-01: Investigate PostgreSQL 18 collation compatibility and error messages in container logs
2. INF-02: Update documentation to clarify Docker environment file usage and template distinction
3. INF-03: Include `frontend/package-lock.json` in Docker build context for reproducible builds

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `BE-001`, `FE-003`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |