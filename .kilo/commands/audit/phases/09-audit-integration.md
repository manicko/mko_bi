---
name: audit-integration
description: Cross-cutting integration audit covering API contract consistency, auth flow end-to-end, data flow end-to-end, database-backend alignment, frontend-backend type alignment, Docker service wiring
agent: audit-executor
alwaysApply: false
---

# Phase 9 Audit — Integration

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** This phase runs AFTER all 8 silo phases complete. It receives ALL 8 silo-phase validated findings as additional context.

---

## Audit Dimensions

### 1. API Contract Consistency

Verify frontend API client calls match backend route definitions.

| Check | Status | Evidence |
|-------|--------|----------|
| Frontend API client calls match backend route definitions | | |
| Path parameters, query parameters, request body shapes match | | |
| Check `.ai/structure/front/ts_anchors.yaml` for API call patterns against `src/mkobi/api/routes/` route definitions | | |

**Files to Audit:**
- `frontend/src/features/*/api/*.ts`
- `src/mkobi/api/routes/*.py`

---

### 2. Auth Flow End-to-End

Verify JWT authentication flow works correctly across frontend and backend.

| Check | Status | Evidence |
|-------|--------|----------|
| Frontend attaches JWT tokens correctly (axios interceptors) | | |
| Backend validates tokens (dependencies in `deps.py`) | | |
| Token refresh flow works end-to-end | | |
| Session/cookie handling secure (Secure flag, SameSite) | | |

**Files to Audit:**
- `frontend/src/shared/api/axiosInstance.ts`
- `src/mkobi/core/security.py`
- `src/mkobi/api/routes/auth.py`

---

### 3. Data Flow End-to-End

Verify complete data flow: Upload → Process → Store → Retrieve → Render.

| Check | Status | Evidence |
|-------|--------|----------|
| Upload endpoint receives file correctly | | |
| Processing pipeline (Polars) produces correct aggregates | | |
| Storage manager writes correct JSONB to PostgreSQL | | |
| Data retrieval endpoint returns correct shape | | |
| Frontend renders data correctly (Plotly charts) | | |

**Files to Audit:**
- `src/mkobi/data/loaders/`
- `src/mkobi/data/processing/`
- `src/mkobi/data/storage/`
- `src/mkobi/api/routes/data.py`
- `frontend/src/features/dashboards/ui/charts/`

---

### 4. Database ↔ Backend Alignment

Verify SQLAlchemy models match Alembic migration schema.

| Check | Status | Evidence |
|-------|--------|----------|
| SQLAlchemy models match Alembic migration schema | | |
| Check for schema drift | | |

**Files to Audit:**
- `src/mkobi/db/models/*.py` vs `alembic/versions/*.py`

---

### 5. Frontend ↔ Backend Type Alignment

Verify TypeScript types match Pydantic response models.

| Check | Status | Evidence |
|-------|--------|----------|
| TypeScript types match Pydantic response models | | |
| Response shapes, field names, nullable types align | | |

**Files to Audit:**
- `frontend/src/shared/types/api.types.ts` vs `src/mkobi/models/*.py`

---

### 6. Docker Service Wiring

Verify services communicate correctly via Docker network.

| Check | Status | Evidence |
|-------|--------|----------|
| Services communicate via Docker network | | |
| Environment variables flow correctly between services | | |
| Health checks reference correct inter-service endpoints | | |

**Files to Audit:**
- `docker/docker-compose.yml`
- `docker/docker-compose.override.yml`
- `Dockerfile`

---

## Input Dependencies

This phase consumes validated findings from all 8 silo phases:
- Phase 1: Audit scope definition
- Phase 2-8: Silo-specific findings (validated)

All findings are available for cross-reference to validate integration points.

---

## Findings

### INT-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | INT-{NN} |
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
| `id` | string | Unique identifier with `INT-` prefix (e.g., `INT-001`, `INT-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements