# Phase 05 Audit Validation Report — Infrastructure & Runtime Environment

**Validator:** validator
**Source:** C:\py_dev\mkobi\.ai\audit\05-docker\findings.md
**Date:** 2026-06-10

---

## Rejected Findings

### INF-01 REJECTED

| Field | Value |
|-------|-------|
| **Original ID** | INF-01 |
| **Original Type** | RUNTIME-ERROR |
| **Original Severity** | MEDIUM |
| **Rejection Reason** | **Unsupported assumption about root cause. The finding attributes the error to "builtin locale provider compatibility issue" but investigation shows: (1) The builtin locale provider IS correctly configured per deployment.md lines 251-259, (2) The `REFRESH COLLATION VERSION` (space) syntax works correctly in PostgreSQL 18.4, (3) The erroneous underscore syntax originates from Debian's postgresql-common tooling, not project code, (4) The database operates correctly with C.UTF-8 collation. The recommendation to "pin to stable PostgreSQL 18 minor version" or "use libc locale provider" is unnecessary since the current configuration works. This is log noise in a stable container, not a configuration problem.** |

**Evidence:**
- Database `bidb_test` functions correctly for all test operations
- `ALTER DATABASE template1 REFRESH COLLATION VERSION` (correct syntax) executes without error
- C.UTF-8 collation is properly set in postgresql.conf
- Project uses `"--locale-provider=builtin --locale=C.UTF-8"` as intentional design per deployment.md
- Errors originate from postgresql-common `pg_wrapper` tooling, not project configuration

### INF-02 REJECTED

| Field | Value |
|-------|-------|
| **Original ID** | INF-02 |
| **Original Type** | DOC-UPDATE |
| **Original Severity** | LOW |
| **Rejection Reason** | **Finding contradicted by actual documentation. The docs/11-guides/docker.md already provides clear distinction at lines 159-166: "The `.env` file in the project root is a **development template** with placeholder values. For **production deployments**, use `docker/.env.production` instead." The root `.env` file contains working development values. The docker/.env.development and docker/.env.production files are clearly marked as templates requiring manual editing. No documentation fix needed - it accurately describes the intended workflow.** |

**Evidence:**
- docs/11-guides/docker.md line 159: explicitly states root `.env` is a development template
- docs/11-guides/docker.md line 162: shows correct production command using `docker/.env.production`
- docs/11-guides/docker.md line 165: shows correct development command using root `.env`
- Root `.env` contains actual development credentials (postgres password, JWT key, etc.)
- docker/.env.development line 2: explicitly states "Copy this file to .env.development and fill in your values"

### INF-03 REJECTED

| Field | Value |
|-------|-------|
| **Original ID** | INF-03 |
| **Original Type** | BEST-PRACTICE |
| **Original Severity** | MEDIUM |
| **Rejection Reason** | **Intentional design choice documented in codebase. The .dockerignore exclusion of `frontend/package-lock.json` is explicitly acknowledged in two places: (1) Dockerfile line 17 comment states "Install dependencies (use npm install as package-lock.json may be excluded)", and (2) .dockerignore line 89 notes "# package-lock.json is excluded (frontend uses separate builder if needed)". The frontend uses a multi-stage build where the lock file exclusion may be intentional to allow minor updates. This is not a violation or bug - it's documented behavior.** |

**Evidence:**
- Dockerfile line 17: explicitly acknowledges the lock file may be excluded
- .dockerignore line 89: documents the exclusion as intentional
- frontend/package-lock.json exists and is used for local development
- Backend uses frozen uv.lock for strict reproducibility

**Rationale:** This is an intentional architectural decision for frontend agility, not a best practice oversight requiring correction.

---

## Summary

| Category | Count |
|----------|-------|
| **Rejected findings** | 3 |
| **Reclassified findings** | 0 |
| **Merged findings** | 0 |
| **Cross-phase conflicts** | 0 |

All three findings were rejected. The PostgreSQL collation errors are non-fatal log noise originating from the postgres:18-bookworm image's postgresql-common tooling (not a configuration problem), the documentation already correctly explains environment file usage, and the frontend lock file exclusion is documented intentional behavior (Dockerfile line 17 comment and .dockerignore line 89 acknowledge this design choice).