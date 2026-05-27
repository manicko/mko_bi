---
name: audit-database
description: Database architecture audit covering schema compliance, indexes, migrations, JSONB usage, test isolation, async compatibility, scalability risks
agent: audit-executor
alwaysApply: false
---

# Phase 3 Audit — Database Architecture

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator:
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Audit Dimensions

### 1. Database Inventory

Search in: `.env`, `docker-compose.yml`, `docker-compose.test.yml`, `config.py`, `init_db.sh`, `conftest.py`.

| Logical Name | DSN Variable | Environment | Purpose | Creation Method |
|---|---|---|---|---|
| bidb | DATABASE_URL | dev/prod | Main application database | Docker / manual |
| bidb_test | TEST_DATABASE_URL | test | Test database (isolated) | Auto-recreated on startup |

**Files to Audit:**
- `.env`
- `.env.example`
- `docker/docker-compose.yml`
- `docker/docker-compose.test.yml`
- `src/mkobi/db/starter.py`

---

### 2. Schema Compliance

Verify all 10 tables match specification with correct types, constraints, and CASCADE/SET NULL behavior.

| Check | Status | Evidence |
|-------|--------|----------|
| All 10 tables exist (users, dashboards, graphs, aggregated_data, layouts, dashboard_access, dashboard_filters, filters, processing_configs, processing_logs) | | |
| users: UUID PK, correct types, nullable constraints | | |
| dashboards: UUID PK, correct types, layout FK, CASCADE to graphs/aggregated_data/dashboard_access | | |
| graphs: UUID PK, BIGSERIAL aggregate_position, CASCADE to aggregated_data | | |
| aggregated_data: BIGSERIAL PK, JSONB dims + metrics, foreign keys to dashboard/graph | | |
| layouts: UUID PK, nullable name | | |
| dashboard_access: UUID PK, CASCADE on user/dashboard delete | | |
| dashboard_filters: UUID PK, CASCADE on filter/dashboard delete | | |
| filters: UUID PK, correct types | | |
| processing_configs: UUID PK, correct types, CASCADE to dashboards | | |
| processing_logs: UUID PK, SET NULL on dashboard | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py`
- `alembic/versions/*.py`

---

### 3. UUID Strategy

Verify UUID for entity tables, BIGSERIAL for aggregated_data (intentional design).

| Check | Status | Evidence |
|-------|--------|----------|
| UUID used for all entity tables (users, dashboards, graphs, layouts, filters, etc.) | | |
| BIGSERIAL used for aggregated_data.id (intentional - high-volume inserts) | | |
| UUID defaults using `uuid_generate_v4()` or `gen_random_uuid()` | | |
| Consistency between ORM models and migration scripts | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py`
- `alembic/versions/*.py`

---

### 4. JSONB Usage

Verify dims + metrics usage in aggregated_data, GIN index, key sorting for deterministic UPSERT.

| Check | Status | Evidence |
|-------|--------|----------|
| aggregated_data.dims is JSONB (vs JSON or TEXT) | | |
| aggregated_data.metrics is JSONB | | |
| GIN or B-tree index on aggregated_data.dims | | |
| dims keys sorted recursively before DB writes (UPSERT determinism) | | |
| JSONB usage justified (flexible configs) | | |
| No over-denormalized JSONB (structured data in columns) | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py`
- `alembic/versions/*.py`
- `src/mkobi/data/storage/manager.py`

---

### 5. Indexes

Verify all 7 core indexes plus additional indexes present.

| Check | Status | Evidence |
|-------|--------|----------|
| Unique index on (dashboard_id, graph_id, dims::text) for aggregated_data | | |
| Index on users.email | | |
| Index on dashboards.owner_id | | |
| Index on dashboard_access.user_id | | |
| Index on processing_logs.task_id | | |
| Index on processing_logs.dashboard_id | | |
| Index on dashboard_filters.filter_id | | |
| GIN index on aggregated_data.dims (if applicable) | | |
| Composite indexes for join optimization | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py`
- `alembic/versions/*.py`

---

### 6. Migrations

Verify migration chain integrity, reproducibility, no broken revisions, ENUM checkfirst=True.

| Check | Status | Evidence |
|-------|--------|----------|
| Migration chain intact (alembic_version table) | | |
| Reproducible from scratch on empty database | | |
| No broken revisions | | |
| No circular dependencies | | |
| ENUM types created with checkfirst=True | | |
| Expected ENUM types: user_role, dashboard_permission_level, graph_type, filter_type, processing_status, registration_status | | |
| No manual SQL changes outside migrations | | |
| No non-idempotent migrations | | |

**Files to Audit:**
- `alembic/versions/*.py`
- `alembic/env.py`
- `alembic/script.py.mako`

---

### 7. Roles & Permissions

Verify least privilege, no superuser for application.

| Check | Status | Evidence |
|-------|--------|----------|
| Roles defined in SQL scripts or init scripts | | |
| Application connects with limited privilege user | | |
| No superuser usage by application | | |
| Separation of privileges (migration vs runtime) | | |
| Ownership correctly assigned | | |

**Files to Audit:**
- `alembic/versions/*.py`
- `docker/*.sql`
- `src/mkobi/db/starter.py`

---

### 8. Test Isolation

Verify bidb_test separate, SAVEPOINT rollback, NullPool.

| Check | Status | Evidence |
|-------|--------|----------|
| Test DB is physically separate (bidb_test ≠ bidb) | | |
| Separate DSN (TEST_DATABASE_URL) | | |
| Test engine uses NullPool (no connection pooling issues) | | |
| Each test runs in SAVEPOINT, rolled back after completion | | |
| No access to prod/dev from test | | |
| Migrations don't affect production | | |
| Recreate strategy on RECREATE_TEST_DB=true | | |

**Files to Audit:**
- `tests/conftest.py`
- `.env.test`
- `docker-compose.test.yml`

---

### 9. Async Compatibility

Verify asyncpg driver, no sync in async context.

| Check | Status | Evidence |
|-------|--------|----------|
| asyncpg driver used (not psycopg2) | | |
| Async SQLAlchemy engine (create_async_engine) | | |
| No sync engine usage in async context | | |
| Connection lifecycle properly managed | | |
| Pool configuration correct (asyncpg) | | |
| Transaction handling via async sessions | | |

**Files to Audit:**
- `src/mkobi/db/starter.py`
- `src/mkobi/db/models/*.py`

---

### 10. Scalability

Verify archival strategy, growth risks identified.

| Check | Status | Evidence |
|-------|--------|----------|
| processing_logs archival strategy exists or planned | | |
| aggregated_data growth risks identified | | |
| Potential bottlenecks documented | | |
| Missing indexes identified | | |
| Full table scan risks identified | | |
| Oversized tables identified | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py`
- `alembic/versions/*.py`

---

### 11. Schema Drift Detection (ORM vs Alembic vs Real DB)

Verify consistency between SQLAlchemy models, Alembic migrations, and real PostgreSQL schema.

| Check | Status | Evidence |
|-------|--------|----------|
| ORM models match Alembic migrations | | |
| Alembic migrations match real DB schema | | |
| No missing tables | | |
| No missing columns | | |
| No type mismatches | | |
| No constraint discrepancies | | |
| No index discrepancies | | |
| No manual DB changes | | |
| No legacy columns/tables | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py`
- `alembic/versions/*.py`

---

## Findings

### DB-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | DB-{NN} |
| **Severity** | {severity} |
| **Type** | {type} |
| **Affected Modules** | {modules} |
| **Classification** | {mandatory|advisory} |

**Description:** {description}

**Evidence:** {evidence}

**Recommendation:** {recommendation}

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## Mandatory Fixes

{List all findings classified as mandatory}

## Advisory Recommendations

{List all findings classified as advisory}

## Doc Updates Needed

{List all findings classified as DOC-UPDATE type}

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier with `DB-` prefix (e.g., `DB-001`, `DB-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/db/models/`, `alembic/versions/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements

---

**Report Format:** See `.ai/audit/templates/audit-findings.md` for full template.