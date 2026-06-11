---
name: 05-docker-validated
description: Validated Docker audit findings
agent: validator
alwaysApply: false
---

# Phase 05 Audit Findings Validation — Infrastructure & Runtime Environment

**Validator:** validator  
**Source:** `.ai/audit/05-docker/findings.md`  
**Mode:** problems-only

---

## Validated Findings Summary

All audit findings validated. Findings reclassified based on evidence analysis (see reclassification section below).

---

## CROSS-PHASE CONFLICTS

### Cross-Phase Reference: INF-001 and TST-001

**Analysis:** Both INF-001 (init script SQL error) and TST-001 (test uv binary access) are mandatory fixes required for containerized execution. However, they address orthogonal issues:
- INF-001: PostgreSQL role creation fails, preventing database connection
- TST-001: Test runners cannot execute uv from non-root user

Neither conflicts with the other. Both must be resolved for CI/CD pipeline viability.

---

### Conflict: INF-005 vs Security Credential Enforcement

**Status:** Design Tension (Not Conflict)

**Analysis:** INF-005 identifies that `.env` has `ENV=development` while production compose uses this file. However, examining the codebase:

- `docker/docker-compose.yml` line 91: `ENV: ${ENV:-production}` — defaults to `production` when unset
- The `.env` file contains development placeholders but is intended for local development
- `docker/.env.production` is the designated production template (line 163-165 in docker.md)
- Production deployment documentation (docker.md line 183-187) specifies: `docker compose --env-file docker/.env.production`

**Resolution:** No conflict exists. The `.env` file at project root is correctly configured for development. Production deployments use a separate `.env.production` file per documented workflow. The current behavior is by design.

---

## FINDING VALIDATION DETAILS

### INF-001: Init Script SQL Syntax Error — GRANT CONNECT Statement Invalid

**Validation Status:** ✅ CONFIRMED

**Evidence Analysis:**
- Line 29 in `docker/init-scripts/01-create-app-role.sh`: `GRANT CONNECT ON DATABASE :'dbname' TO mkobi_app;`
- The `:variable` syntax (without quotes) outputs the value as an identifier
- The `:'variable` syntax (with single quotes) outputs a quoted string literal
- PostgreSQL `GRANT CONNECT ON DATABASE` requires an unquoted identifier

**Technical Verification:**
- The `psql` documentation confirms `:variable` outputs unquoted value
- The `:'variable` syntax produces `'bidb'` (literal string including quotes)
- This would cause `syntax error at or near "'bidb'"` as reported in evidence

**Classification:** `SPEC-DEVIATION` — Implementation violates PostgreSQL syntax requirements. Mandatory fix.

---

### INF-002: PostgreSQL 18+ Volume Mount Path Incompatibility

**Validation Status:** ⚠️ RECLASSIFIED (Configuration Correct, Migration Documentation Needed)

**Evidence Analysis:**
- Volume mount at line 29 in `docker/docker-compose.yml`: `postgres_data:/var/lib/postgresql`
- Volume mount at line 39 in `docker/docker-compose.test.yml`: `test_postgres_data:/var/lib/postgresql`

**Documentation Cross-Reference:**
- Docker Hub for postgres:18-bookworm: "The defined `VOLUME` was changed in 18 and above to `/var/lib/postgresql`"
- PostgreSQL 18 uses `PGDATA=/var/lib/postgresql/18/docker` internally
- `docs/11-guides/docker.md` line 248 mentions: "PostgreSQL 18+ compatibility"

**Technical Verification:**
- The volume path `/var/lib/postgresql` is **correct** for PostgreSQL 18+
- The error occurs when upgrading from PG16/17 where volumes contain incompatible data
- PG16/17 used `/var/lib/postgresql/data` as the mount target

**Root Cause:** The error signature indicates a migration path issue, not a configuration defect. Users upgrading from older PostgreSQL versions need to clean volumes.

**Classification:** `SPEC-DEVIATION` → RECLASSIFIED as `DOC-UPDATE` — The configuration is correct for PG18+. The documentation should include upgrade instructions for users migrating from older PostgreSQL versions.

---

### INF-003: Frontend Vite Dev Server Crashes on Windows with SIGBUS

**Validation Status:** ✅ CONFIRMED

**Evidence Analysis:**
- Line 36 in `docker/docker-compose.override.yml`: command uses Vite with `--host 0.0.0.0`
- Line 38: `CHOKIDAR_USEPOLLING: "true"` is already configured
- SIGBUS errors are a known issue with file watching on Docker Desktop for Windows

**Technical Verification:**
- The `CHOKIDAR_USEPOLLING=true` setting is present but may require additional configuration
- The error shows the container repeatedly crashes and never becomes healthy

**Classification:** `SPEC-DEVIATION` — Platform compatibility issue. Mandatory fix for Windows development workflow.

---

### INF-004: PostgreSQL Collation Version Error (Cosmetic but Misleading)

**Validation Status:** ✅ CONFIRMED

**Evidence Analysis:**
- Uses `builtin` locale provider with `C.UTF-8` per SPEC.md v3.8
- This provides immutable collation version (fixed at `1`)
- The error stems from `postgresql-common` package incompatibility with PG18's stricter parser

**Documentation Cross-Reference:**
- `docs/11-guides/docker.md` lines 329-351 explicitly documents this as harmless
- States the `builtin` locale provider makes the refresh operation unnecessary

**Classification:** `BEST-PRACTICE` — Valid advisory. The error is cosmetic but documented. Optional improvement.

---

### INF-005: Production Compose Uses Development Target by Default

**Validation Status:** ✅ CONFIRMED (DESIGN BY INTENDS)

**Evidence Analysis:**
- `.env` line 7: `ENV=development` — correctly labeled as development template
- `docker/docker-compose.yml` line 91: `ENV: ${ENV:-production}` — defaults to production
- Production deployments documented to use `docker/.env.production`

**Resolution:** Not a defect. The `.env` file is correctly configured for development. Production deployments use a separate environment file. The finding misunderstands the intended workflow.

**Classification:** `BEST-PRACTICE` — Documentation clarification opportunity. Advisory recommendation to make production workflow more explicit in documentation.

---

### INF-006: Test Compose Exposes Internal Ports to Host

**Validation Status:** ✅ CONFIRMED (BY DESIGN - Already Best Practice Classification)

**Evidence Analysis:**
- Ports 5433, 6380, 8001 are intentionally exposed in `docker/docker-compose.test.yml`
- `docs/10-deployment/deployment.md` lines 197-215 explicitly documents this as intentional design
- Security risk assessment: LOW (no production data, default test passwords)
- Rationale: Native test execution from host terminal is faster than `docker compose exec`

**Recommendation:** The exposure is intentional per documented design. Consider adding a warning in the security documentation about CI/CD environments where this should be avoided.

**Classification:** `BEST-PRACTICE` — Already correctly classified as advisory. The documented design rationale is sufficient.

---

## ROLLOUT SAFETY ISSUES

### INF-001 Dependencies

The SQL syntax fix (INF-001) blocks all other services that depend on PostgreSQL:

| Finding ID | Dependent Service | Impact |
|------------|-------------------|--------|
| INF-001 | app, migrate, rq-worker | Cannot connect to database without `mkobi_app` role |

**Sequencing Risk:** INF-001 must be fixed before any database-dependent services can function. The fix is minimal (single character change in SQL).

---

## Merged Findings

None detected.

---

## VALIDATED COUNTS

| Type | Valid Findings | Classification |
|------|---------------|----------------|
| SPEC-DEVIATION | 2 (INF-001, INF-003) | Mandatory |
| DOC-UPDATE | 1 (INF-002 reclassified) | Advisory |
| BEST-PRACTICE | 3 (INF-004, INF-005, INF-006) | Advisory |

**Total Rejected:** 0  
**Total Reclassified:** 1 (INF-002: SPEC-DEVIATION → DOC-UPDATE)

---

## REQUIRED FIXES

1. **INF-001** — Fix psql `:'dbname'` to `:dbname` in init script (line 29)
2. **INF-003** — Add Windows-specific Vite compatibility environment (documented workaround)

---

## ADVISORY RECOMMENDATIONS

1. **INF-002 (reclassified)** — Add upgrade migration documentation for users migrating from PG16/17 to PG18
2. **INF-004** — Log filtering configuration for PostgreSQL collation errors (cosmetic)
3. **INF-005** — Clarify production .env workflow in documentation
4. **INF-006** — Add CI/CD warning about test port exposure (already BEST-PRACTICE)

---

**Validator Signature:** Trust evidence, not claims. Code has priority over assumptions.