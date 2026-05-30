---
id: security-overview
domain: security
tags:
  - rate-limiting
  - file-upload-security
  - sql-injection
  - cors
  - credentials
  - secrets-management
  - jwt-security
related:
  - access-control
  - auth-api
  - configuration
  - frontend-security
  - processing-api
---

# Security Overview

## Overview

This document describes the security constraints and measures implemented across the system. Security is enforced at multiple layers: network (CORS), application (rate limiting, input validation), and data (parameterized queries, credential management).

> **[HIGH-RISK]** Security constraints are enforced on the **backend**. Frontend validation is a UX convenience only and must never be relied upon as a security boundary.

---

## Rate Limiting

### Overview

Rate limiting is applied to sensitive endpoints to prevent brute-force attacks and abuse. The rate limiter is Redis-based and uses a sliding window algorithm.

### Protected Endpoints

| Endpoint | Rate Limit | Scope |
| --- | --- | --- |
| `POST /api/v1/auth/login` | 5 attempts per 5 minutes | Per IP |
| `POST /api/v1/auth/login/form` | 5 attempts per 5 minutes | Per IP |
| `POST /api/v1/auth/register-request` | 3 attempts per hour | Per IP/email |
| `POST /api/v1/upload/:dashboard_id` | Configured via env | Per user |
| `POST /api/v1/upload/:dashboard_id/process` | Configured via env | Per user |

### Email Enumeration Mitigation

Login rate limiting uses **per-IP** keys (not per-email) to prevent email enumeration attacks. An attacker can determine whether an email is registered by observing which keys are rate-limited. By scoping rate limits to the client IP address, the system prevents this side-channel while maintaining effective brute-force protection.

### Rate Limiter Failure Behavior [HIGH-RISK]

The rate limiter depends on Redis. When Redis is unavailable, the system operates in one of two modes, configurable via the `RATE_LIMITER_FAIL_CLOSED` environment variable:

| Mode | Config Value | Behavior | Log Level | Use Case |
| --- | --- | --- | --- | --- |
| **Fail-open** (default) | `RATE_LIMITER_FAIL_CLOSED=false` | Requests are allowed through when Redis is down | WARNING | Development, availability-first deployments |
| **Fail-closed** | `RATE_LIMITER_FAIL_CLOSED=true` | Requests are rejected with HTTP 429 when the rate limiter cannot be initialized | CRITICAL | Production — prevents rate limit bypass during Redis outages |

**Health tracking:** Rate limiter health is tracked internally. When the rate limiter is disabled due to Redis unavailability, an error-level log is emitted with exception details.

> **Recommendation:** Use **fail-closed** mode in production to prevent attackers from exploiting Redis outages to bypass rate limits.

---

## File Upload Security

### Allowed Formats

| Format | MIME Type | Extension |
| --- | --- | --- |
| CSV | `text/csv` | `.csv` |
| Gzip-compressed CSV | `application/gzip`, `application/x-gzip` | `.csv.gz` |

### Validation Chain

1. **Frontend (UX):** `react-dropzone` filters by MIME type; extension check on filename.
2. **Backend (security boundary):**
   - MIME type validation against whitelist (`text/csv`, `application/gzip`, `application/x-gzip`)
   - File extension validation (`.csv`, `.csv.gz`)
   - Maximum file size enforcement
   - Rate limiting on upload endpoints

### File Lifecycle

1. File is uploaded to a temporary directory (via `platformdirs`)
2. File is parsed and processed (Polars)
3. Aggregated data is saved to PostgreSQL
4. **Temporary file is deleted** after processing (success or failure)

> **Critical:** Temporary files MUST always be deleted after processing. Failure to clean up may expose sensitive data on disk.

---

## SQL Injection Prevention

### Rules

- **All SQL queries** must be executed through parameterized queries (SQLAlchemy ORM/Core)
- **String interpolation** for SQL is strictly forbidden (no f-strings, no `.format()`, no concatenation)
- SQLAlchemy models and query builders are the only permitted interface to the database

### Enforcement

This is enforced at the code review level and by the project's linting/type-checking pipeline. The use of raw SQL via f-strings is flagged in `AGENTS.md` as a forbidden practice.

---

## CORS Configuration [HIGH-RISK]

CORS is configured on the backend with explicit allowed methods and headers. Wildcards are **not** used.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,  # From env var or app.yaml (default: localhost)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

### Constraints

- **`allow_origins`** must be explicitly configured in production — the application validates CORS configuration at startup and raises an error if origins are not set in production mode
- **No wildcard origins** (`*`) in production
- **Explicit method list:** Only `GET`, `POST`, `PUT`, `DELETE`, `PATCH`
- **Explicit header list:** Only `Authorization`, `Content-Type`, `Accept`

---

## Production Credential Enforcement [HIGH-RISK]

The application **refuses to start** in production mode if default credentials are detected:

| Variable | Default (dev) | Production Requirement |
| --- | --- | --- |
| `ADMIN_USERNAME` | `admin` | Must be explicitly set via environment variable |
| `ADMIN_PASSWORD` | `admin` | Must be explicitly set; default `admin`/`admin` combination is rejected |
| `JWT__SECRET_KEY` | — | Must be explicitly set; Docker Compose uses `${JWT__SECRET_KEY:?...}` fail-if-unset syntax |
| `DATABASE__PASSWORD` | — | Must be explicitly set; same fail-if-unset pattern |

In development mode, default credentials are permitted but a **warning** is logged.

---

## Secrets Management

### Configuration Priority

Configuration is loaded from multiple sources (highest priority first):

1. Environment variables
2. Docker secrets (`_FILE` suffix)
3. `.env` file (development only)
4. `app.yaml` (non-sensitive settings only)
5. Defaults

### Secret Variables

| Variable | Description | Docker Secrets Support |
| --- | --- | --- |
| `DATABASE__PASSWORD` | Database password | `DATABASE__PASSWORD_FILE=/run/secrets/db_password` |
| `JWT__SECRET_KEY` | JWT signing key | `JWT__SECRET_KEY_FILE=/run/secrets/jwt_secret` |

- Nested variables use double underscore format: `DATABASE__HOST`, `DATABASE__PORT`, `JWT__SECRET_KEY`
- `app.yaml` contains **only non-sensitive** settings (hosts, ports, paths)

---

## Email Domain Blocklist

Registration requests are checked against a configurable email domain blocklist:

- Configured in `app.yaml` (backend)
- Validated on the backend via Pydantic (security boundary)
- Also validated on the frontend via Zod (UX convenience)
- Example blocked domains: `tempmail.com`, `throwawaymail.com`

---

## Password Security

- Passwords are stored as **bcrypt hashes** (never plaintext)
- Minimum length: 8 characters (enforced by frontend Zod schema)
- Password change requires current password verification
- Users remain logged in after password change (token is not invalidated)
- Registration approval generates a cryptographically random temporary password via `secrets.token_urlsafe(16)`

---

## JWT Security

- Tokens are signed and contain expiration (`exp` claim)
- Payload contains: `user_id`, `email`, `role`
- **Access tokens:** 15-minute expiration, stored in memory on the frontend (not in `localStorage` or cookies — XSS-safe)
- **Refresh tokens:** 7-day expiration, stored in httpOnly cookies (`mkobi_refresh_token`), set with `Secure`, `HttpOnly`, and `SameSite=Strict` attributes
- Axios interceptors attach the access token to every request and handle `401` responses by attempting a silent refresh

---

## Cookie Security

The `mkobi_refresh_token` cookie is the cornerstone of the refresh token security model. It is used exclusively for storing the refresh token and has the following attributes:

| Attribute | Value | Purpose |
| --- | --- | --- |
| `HttpOnly` | `true` | Prevents JavaScript access, mitigating XSS-based token theft |
| `Secure` | `true` | Cookie is only sent over HTTPS, preventing interception on plaintext connections |
| `SameSite` | `Strict` | Cookie is not sent on cross-site requests, mitigating CSRF attacks |
| `Max-Age` | `604800` (7 days) | Refresh token lifetime |
| `Path` | `/` | Available to all API routes |

### Cookie Lifecycle

1. **Set on login:** `POST /api/v1/auth/login` sets the cookie via `Set-Cookie` header
2. **Read on refresh:** `POST /api/v1/auth/refresh` reads the cookie to obtain the refresh token
3. **Cleared on logout:** `POST /api/v1/auth/logout` sets `Max-Age=0` to clear the cookie
4. **Not accessible to JS:** The `HttpOnly` flag ensures client-side JavaScript cannot read or manipulate the cookie

### Backend Cookie Utilities

The `core/security.py` module provides `set_cookie()` and `delete_cookie()` helper functions that enforce consistent cookie attributes across all auth endpoints. All auth routes use these utilities instead of calling `Response.set_cookie()` directly.

---

## Cross-References

- [Authentication API](../01-auth/auth-api.md) — Auth endpoint security, rate limiting details
- [Access Control](access-control.md) — Dashboard-level permission enforcement model
- [Frontend Security](../07-frontend/frontend-security.md) — JWT handling, CORS, file upload, role-based access
- [Configuration](../06-backend/configuration.md) — Secrets management, environment variables
- [Processing API](../03-processing/processing-api.md) — Upload security constraints and rate limiting
- [Client Error Reporting](client-error-reporting.md) — Frontend error logging endpoint for React Error Boundary and uncaught exceptions
