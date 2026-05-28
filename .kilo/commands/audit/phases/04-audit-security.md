---
name: 04-security
description: Security audit covering authentication, access control, JWT, password security, upload safety, SQL safety, secrets/config, rate limiting, email domain blocklist, StrEnum enforcement
agent: audit-executor
alwaysApply: false
---

# Phase 04 Audit â€” Security

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

### 1. Access Control

Verify `src/mkobi/core/permissions.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| `dashboard_access` checked on every dashboard-related request | | |
| Editor/viewer/admin restrictions enforced | | |
| Direct object access vulnerabilities prevented | | |
| Admin bypass: admins have full access without explicit `dashboard_access` entries | | |
| 403/404 dual-signal: 404 for not-found, 403 for exists-but-no-access | | |

### 2. User Roles (StrEnum)

Verify `UserRole` StrEnum usage:

```python
class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
```

| Check | Status | Evidence |
|-------|--------|----------|
| UserRole StrEnum used (NOT string literals) | | |
| All role checks use enum values | | |

### 3. Dashboard Permissions (StrEnum)

Verify `DashboardPermission` StrEnum:

```python
class DashboardPermission(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"
```

| Check | Status | Evidence |
|-------|--------|----------|
| DashboardPermission StrEnum used | | |
| Permission checks use enum values | | |

---

### 4. JWT Security

Verify `src/mkobi/core/security.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| Token expiration validation | | |
| Invalid token handling (401 Unauthorized) | | |
| Missing token handling (401 Unauthorized) | | |
| Secret key stored in env (JWT__SECRET_KEY) | | |
| Algorithm explicitly set (NOT default) | | |
| Payload contains: user_id, email, role | | |

**Files to Audit:**
- `src/mkobi/core/security.py`
- `src/mkobi/api/deps.py`

---

### 5. Password Security

Verify password handling:

| Check | Status | Evidence |
|-------|--------|----------|
| bcrypt used (NOT md5, SHA, plaintext) | | |
| Password hash stored in DB (NOT plaintext) | | |
| No password logging | | |
| Minimum 8 characters password (frontend Zod schema) | | |
| Temp password generated via `secrets.token_urlsafe(16)` on registration approval | | |

**Files to Audit:**
- `src/mkobi/api/routes/auth.py`
- `src/mkobi/api/routes/admin.py`

---

### 6. Upload Security

Verify `src/mkobi/api/routes/upload.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| Path traversal protection (`../../file.csv`) | | |
| Unsafe filenames handling (secure filename) | | |
| Oversized files handling (limit via config) | | |
| MIME-type validation (client + server side) | | |
| UTF-8 encoding validation | | |
| Temp file cleanup (platformdirs, both success and failure) | | |
| Rate limiting on upload | | |

---

### 7. SQL Safety

Verify repositories (`src/mkobi/db/repositories/`):

| Check | Status | Evidence |
|-------|--------|----------|
| No raw unsafe SQL | | |
| Parameterized queries (SQLAlchemy ORM/Core) | | |
| No SQL formation via f-strings or string concatenation | | |
| ORM used for all operations | | |

---

### 8. Secrets & Configuration

Verify `src/mkobi/config.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| No hardcoded secrets | | |
| Env-based configuration (pydantic-settings) | | |
| Docker secrets support (_FILE suffix) | | |
| Nested env vars (DATABASE__HOST, DATABASE__PORT, JWT__SECRET_KEY) | | |
| .env file for development only | | |
| app.yaml for non-sensitive settings only | | |
| Production credential enforcement (refuses to start with default admin/admin) | | |
| CORS origins validated at startup in production mode | | |

---

### 9. Rate Limiting

Verify rate limiting implementation:

| Check | Status | Evidence |
|-------|--------|----------|
| Redis-based sliding window algorithm | | |
| Fail-open (default) vs fail-closed (production) via RATE_LIMITER_FAIL_CLOSED | | |
| Protected endpoints: login (5/5min), register-request (3/hour), upload (configured) | | |
| Health tracking when Redis unavailable | | |

**Files to Audit:**
- `src/mkobi/core/rate_limiter.py`
- `src/mkobi/api/routes/auth.py`
- `src/mkobi/api/routes/upload.py`

---

### 10. Email Domain Blocklist

Verify email domain validation:

| Check | Status | Evidence |
|-------|--------|----------|
| Configurable domain blocklist in app.yaml | | |
| Validated on backend via Pydantic (security boundary) | | |
| Validated on frontend via Zod (UX convenience) | | |

**Files to Audit:**
- `src/mkobi/models/auth.py`
- `frontend/src/features/auth/model/useAuth.ts`

---

### 11. StrEnum Enforcement

Verify `src/mkobi/models/enums.py`:

All constants must be StrEnum, NOT dict or list. All 17 classes required:

`UserRole`, `DashboardPermission`, `GraphType`, `FilterType`, `RegistrationStatus`, `UploadMode`, `ProcessingStatus`, `EnvironmentEnum`, `MimeTypeEnum`, `FileExtensionEnum`, `AggregationFunctionEnum`, `FilterOperatorEnum`, `OrientationEnum`, `BarmodeEnum`, `YoyModeEnum`, `ButtonVariant`, `ComponentSize`

| Check | Status | Evidence |
|-------|--------|----------|
| All 17 StrEnum classes present | | |
| No string literal comparisons for role/status/type checks | | |
| Bad: `if user.role == "admin":` â€” NOT present | | |
| Good: `if user.role == UserRole.ADMIN:` â€” used | | |

---

### 12. Frontend Security

Verify frontend security implementation:

| Check | Status | Evidence |
|-------|--------|----------|
| JWT stored in memory (production) or sessionStorage (development) â€” NOT localStorage | | |
| Axios interceptors add token to requests | | |
| ProtectedRoute component works correctly | | |
| RoleBasedAccess component works correctly | | |
| Email validation (Zod regex + blacklist domains) | | |
| UI-level role checks are for UX only (backend enforces authorization) | | |

**Files to Audit:**
- `frontend/src/shared/api/axiosInstance.ts`
- `frontend/src/shared/components/ProtectedRoute.tsx`
- `frontend/src/shared/components/RoleBasedAccess.tsx`

---

## Findings

### SEC-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | SEC-{NN} |
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
| `id` | string | Unique identifier with `SEC-` prefix (e.g., `SEC-001`, `SEC-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/core/`, `frontend/src/shared/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, access control violations, data loss risks, correctness issues requiring immediate fix
- **advisory**: Best practice enhancements, security hardening suggestions

---

**Report Format:** See `.ai/audit/templates/audit-findings.md` for full template.