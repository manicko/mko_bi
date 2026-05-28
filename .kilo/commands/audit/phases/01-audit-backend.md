---
name: 01-backend
description: Backend architecture audit covering Clean Architecture compliance, API layer correctness, access control, code quality (typing, Pydantic, StrEnum, async, logging)
agent: audit-executor
alwaysApply: false
---

# Phase 01 Audit â€” Backend Architecture

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator  (SKIP if you already have it):
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Audit Dimensions

### 1. Backend Clean Architecture

Verify Clean Architecture compliance (layer separation, no business logic in routes, DI via deps.py).

| Check | Status | Evidence |
|-------|--------|----------|
| API Layer contains HTTP only, input validation, service calls | | |
| Service Layer contains business logic, orchestration | | |
| Repository Layer contains data access, SQL queries | | |
| No business logic inside route handlers | | |
| No SQL inside controllers/routes | | |
| No global mutable state | | |
| No cyclic imports | | |
| No hidden side effects | | |
| No mixed responsibilities between layers | | |
| Dependency Injection via `src/mkobi/api/deps.py` | | |
| Config centralization (pydantic-settings, env vars, Docker secrets) | | |
| Logging centralization (`src/mkobi/core/logging_config.py`) | | |
| Enum usage (StrEnum in `src/mkobi/models/enums.py`) | | |

**Files to Audit:**
- `src/mkobi/api/routes/*.py`
- `src/mkobi/services/*.py`
- `src/mkobi/db/repositories/*.py`
- `src/mkobi/models/*.py`
- `src/mkobi/api/deps.py`
- `src/mkobi/core/*.py`

---

### 2. API Endpoints

Verify all routes have correct Pydantic models and error handling.

| Check | Status | Evidence |
|-------|--------|----------|
| Auth endpoints: POST /login, POST /login/form, POST /register-request, POST /refresh, GET /me, POST /change-password | | |
| Dashboard endpoints: GET /my, GET /:id, POST, PUT, DELETE (admin only) | | |
| Data endpoints: GET /aggregated, POST /upload/:dashboard_id, POST /upload/:dashboard_id/process, GET /upload/status/:task_id, GET /upload/result/:task_id | | |
| Admin endpoints: GET /users, PATCH /users/:id/role, DELETE /users/:id, GET /registration-requests, POST /registration-requests/:id/{approve|reject}, GET /logs | | |
| Health endpoints: GET /health, GET /health/detailed, GET / all functional | | |
| Other endpoints: users CRUD, profile, self-deletion; filters CRUD; graphs CRUD; layouts CRUD; processing_configs CRUD; processing_logs access | | |
| All routes use Pydantic models (NOT raw dicts) | | |
| All errors via HTTPException (NOT print()) | | |
| No print() statements in route handlers | | |
| Display_name derived from email prefix (text before @) | | |
| JWT generation: algorithm explicitly set, expiration configured | | |
| JWT validation via dependencies in deps.py | | |
| Email validation uses Pydantic EmailStr | | |
| Rate limiting on login (5/5min per email) and register-request (3/hour per IP/email) | | |
| Refresh token verifies user still exists in DB | | |
| Change-password requires current password, user stays logged in after change | | |

**Files to Audit:**
- `src/mkobi/api/routes/auth.py`
- `src/mkobi/api/routes/dashboards.py`
- `src/mkobi/api/routes/data.py`
- `src/mkobi/api/routes/upload.py`
- `src/mkobi/api/routes/admin.py`
- `src/mkobi/api/routes/users.py`
- `src/mkobi/api/routes/filters.py`
- `src/mkobi/api/routes/graphs.py`
- `src/mkobi/api/routes/layouts.py`
- `src/mkobi/api/routes/processing_configs.py`
- `src/mkobi/api/routes/processing_logs.py`

---

### 3. Access Control & Security

Verify dashboard access validation, admin bypass, and 403/404 dual-signal.

| Check | Status | Evidence |
|-------|--------|----------|
| dashboard_access checked on every dashboard-related request | | |
| Editor/viewer/admin restrictions enforced | | |
| Direct object access vulnerabilities prevented | | |
| Admin bypass: admins have full access without explicit dashboard_access entries | | |
| 403/404 dual-signal: 404 for not-found, 403 for exists-but-no-access | | |
| UserRole StrEnum used for all role checks (NOT string literals) | | |
| DashboardPermission StrEnum used for permission checks | | |
| JWT expiration validation | | |
| Invalid/missing token handling (401 Unauthorized) | | |
| Secret key stored in env (JWT__SECRET_KEY) | | |
| Algorithm explicitly set (NOT default) | | |
| Payload contains: user_id, email, role | | |
| bcrypt used (NOT md5, SHA, plaintext) | | |
| Password hash stored in DB (NOT plaintext) | | |
| No password logging | | |
| Min 8 characters password (frontend Zod schema) | | |
| Temp password generated via secrets.token_urlsafe(16) on registration approval | | |
| Path traversal protection in upload | | |
| Unsafe filenames handling (secure filename) | | |
| Oversized files handling (limit via config) | | |
| MIME-type validation (client + server side) | | |
| Rate limiting on upload | | |
| No raw unsafe SQL | | |
| Parameterized queries (SQLAlchemy ORM/Core) | | |
| No SQL formation via f-strings or string concatenation | | |
| No hardcoded secrets | | |
| Env-based configuration (pydantic-settings) | | |
| Docker secrets support (_FILE suffix) | | |
| Nested env vars (DATABASE__HOST, JWT__SECRET_KEY) | | |
| .env file for development only | | |
| app.yaml for non-sensitive settings only | | |
| Production credential enforcement (refuses to start with default admin/admin) | | |
| CORS origins validated at startup in production mode | | |
| Redis-based sliding window rate limiting | | |
| Fail-open (default) vs fail-closed (production) via RATE_LIMITER_FAIL_CLOSED | | |
| Domain blocklist validated on backend via Pydantic | | |

**Files to Audit:**
- `src/mkobi/core/permissions.py`
- `src/mkobi/core/security.py`
- `src/mkobi/api/routes/upload.py`
- `src/mkobi/config.py`
- `src/mkobi/models/enums.py`

---

### 4. Data Processing Pipeline

Verify Polars usage, full recalculation, and temp file cleanup.

| Check | Status | Evidence |
|-------|--------|----------|
| Polars used (import polars as pl) | | |
| pandas NOT used (import pandas forbidden) | | |
| CSV reading via Polars read_csv | | |
| CSV.gz handling (gzip decompression) | | |
| Schema validation (validator.py) | | |
| Error handling for corrupted CSV, invalid schema, missing columns, empty files | | |
| GroupBy (Polars group_by) | | |
| YoY calculations with modes: absolute, percent | | |
| Shares (ratio computations) | | |
| Custom metrics formula parser supports +, -, *, / operators | | |
| Invalid formulas produce clear error messages with position and nature | | |
| Full recalculation on each upload (not incremental) | | |
| Temp files cleanup via platformdirs (both success and failure) | | |
| DB transaction handling (atomic processing, rollback on failure) | | |
| dims keys sorted recursively before writes (UPSERT determinism) | | |
| Unique index on (dashboard_id, graph_id, dims::text) for conflict detection | | |

**Files to Audit:**
- `src/mkobi/data/loaders/loader.py`
- `src/mkobi/data/processing/transformations.py`
- `src/mkobi/data/processing/registry.py`
- `src/mkobi/data/storage/manager.py`

---

### 5. Code Quality (Backend)

Verify typing, Pydantic models, StrEnum usage, async correctness, and logging.

| Check | Status | Evidence |
|-------|--------|----------|
| Type hints on all functions (parameters + return value) | | |
| Pydantic models for API (src/mkobi/models/) | | |
| SQLAlchemy models for ORM (src/mkobi/db/models/) | | |
| No Any types (except justified cases) | | |
| mypy passes without errors | | |
| All models inherit from BaseModel | | |
| Types used: EmailStr, UUID, datetime | | |
| Validators where needed (field_validator) | | |
| model_config configured on all models | | |
| All 17 StrEnum classes used, no string literals for role/status/type checks | | |
| No oversized functions (split into smaller ones) | | |
| No duplicated logic | | |
| Clear naming conventions | | |
| Comments only for non-trivial logic | | |
| Comments in English (NOT Russian) | | |
| Log messages in English (NOT Russian) | | |
| Exception messages in English | | |
| Docstrings in English | | |
| No broad except Exception: without re-raise | | |
| No swallowed exceptions (empty except blocks) | | |
| Consistent errors (always HTTPException with code) | | |
| Error logging (logger.error with context) | | |
| No blocking I/O in async endpoints | | |
| No sync DB calls in async endpoints (use async SQLAlchemy) | | |
| No time.sleep() in async (use asyncio.sleep) | | |
| Proper await usage | | |
| logger = logging.getLogger(__name__) used everywhere | | |
| Upload events logged (start, complete, failure) | | |
| Processing events logged (start, steps, complete, failure) | | |
| Auth events logged (login success/failure) | | |
| Errors logged with stack trace | | |
| Levels: INFO, WARNING, ERROR (NOT DEBUG in production) | | |

**Files to Audit:**
- `src/mkobi/models/*.py`
- `src/mkobi/db/models/*.py`
- `src/mkobi/models/enums.py`
- `src/mkobi/core/*.py`

---

## Findings

### BE-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | BE-{NN} |
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
| `id` | string | Unique identifier with `BE-` prefix (e.g., `BE-001`, `BE-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `src/mkobi/services/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements

---

**Report Format:** See `.ai/audit/templates/audit-findings.md` for full template.