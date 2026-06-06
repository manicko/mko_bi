# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DC-001: App Port 8000 Exposed to Host in Production, Bypassing Nginx Security

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/docker-compose.yml` (app service) |
| **Classification** | mandatory |

**Description:** The `app` service publishes port 8000 to the host (`"8000:8000"`) in the main `docker-compose.yml`. When the production profile is active (`--profile production`), nginx serves as the reverse proxy on port 80 with security headers, rate limiting, and request size controls. However, because port 8000 is also exposed directly, clients can bypass nginx entirely by connecting to `http://host:8000`, circumventing all nginx-enforced security. This violates the deployment architecture where nginx is the sole entry point in production.

**Evidence:** `docker/docker-compose.yml`, lines 68-69:
```yaml
  app:
    ports:
      - "8000:8000"
```
The nginx service is defined with `profiles: [production]` and listens on port 80, intended as the single production entry point. But the app port remains unconditionally exposed.

**Recommendation:** Remove the `ports` mapping from the `app` service in the base `docker-compose.yml`. Instead, expose port 8000 only in the development override (`docker-compose.override.yml`) where nginx is not used. In production, the app should only be reachable via the Docker internal network (nginx → app:8000), never directly from the host.

---

### DC-002: mkobi_app Role Granted CREATEDB Privilege, Violating Least-Privilege Principle

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/init-scripts/01-create-app-role.sh`, `docs/10-deployment/deployment.md` |
| **Classification** | mandatory |

**Description:** The database initialization script grants `CREATEDB` privilege to the `mkobi_app` role (`ALTER ROLE mkobi_app CREATEDB`). The deployment documentation (`deployment.md`) explicitly states that `mkobi_app` should only have `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on tables and `USAGE` on sequences. CREATEDB allows the application runtime user to create and drop arbitrary databases — a significant escalation beyond documented privileges. This privilege is not needed in production: the `recreate_test_database()` function in `starter.py` already uses admin credentials (`postgres` superuser via `test_admin_database_url`) for all CREATE/DROP DATABASE operations. The CREATEDB grant on mkobi_app is redundant and violates the documented least-privilege model.

**Evidence:** `docker/init-scripts/01-create-app-role.sh`, line 28:
```sql
ALTER ROLE mkobi_app CREATEDB;
```
`docs/10-deployment/deployment.md` documents mkobi_app privileges as:
> `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on tables; `USAGE` on sequences

`src/mkobi/db/starter.py` `recreate_test_database()` uses `admin_url` (postgres superuser) for CREATE DATABASE, confirming mkobi_app does not need CREATEDB.

**Recommendation:** Remove `ALTER ROLE mkobi_app CREATEDB;` from `01-create-app-role.sh`. If CREATEDB is needed for test environments, add a conditional grant or a separate init script scoped to test configurations only.

---

### DC-003: /health/detailed Endpoint Exposed Without Authentication in Production

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/app.py` |
| **Classification** | mandatory |

**Description:** The `/health/detailed` endpoint is registered unconditionally in all environments, including production, without any authentication or authorization check. It exposes infrastructure details: database type, connection status with error messages on failure, and static file paths. While the basic `/health` endpoint (returning only `{"status": "healthy", "database": "connected"}`) is standard for load balancer probes, the detailed endpoint leaks internal state that aids reconnaissance. The `/docs` and `/redoc` endpoints are correctly disabled in production, but `/health/detailed` lacks the same environment guard.

**Evidence:** `src/mkobi/app.py`, lines ~170-200:
```python
@application.get("/health/detailed", tags=["health"])
async def detailed_health_check() -> dict[str, Any]:
    # Returns: database type, connection status, error messages, file paths
    components["database"] = {
        "status": "connected",
        "type": "postgresql",
    }
    components["static_files"] = {
        "status": "available",
        "path": "frontend/dist",
    }
```
No authentication dependency, no `if config.environment == PRODUCTION` guard.

**Recommendation:** Either (a) disable `/health/detailed` in production (similar to how `/docs` and `/redoc` are disabled), or (b) require admin authentication for this endpoint. Example: `include_in_schema=config.environment != EnvironmentEnum.PRODUCTION`.

---

### DC-004: SQL Injection Risk in Init Script via Unsanitized Password Interpolation

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/init-scripts/01-create-app-role.sh` |
| **Classification** | mandatory |

**Description:** The PostgreSQL initialization script uses bash variable interpolation directly inside a SQL string literal: `PASSWORD '${MKOBI_APP_PASSWORD}'`. If the password value contains a single quote character, the SQL string literal is broken, causing either a syntax error or, in the worst case, SQL injection. While the env var is typically set by an operator using `openssl rand -hex 32` (which produces only hex characters), there is no validation or escaping. If a secret management system supplies a password containing special characters (e.g., from HashiCorp Vault, AWS Secrets Manager), the init script will fail or produce unintended SQL execution. PostgreSQL provides dollar-quoting (`$$...$$`) to avoid this class of issue entirely.

**Evidence:** `docker/init-scripts/01-create-app-role.sh`, line inside heredoc:
```sql
CREATE ROLE mkobi_app WITH LOGIN PASSWORD '${MKOBI_APP_PASSWORD}';
```
Shell expansion occurs before psql receives the SQL, so any single quote in `MKOBI_APP_PASSWORD` breaks the `PASSWORD '...'` string literal.

**Recommendation:** Use PostgreSQL dollar-quoting to eliminate the SQL injection surface:
```sql
CREATE ROLE mkobi_app WITH LOGIN PASSWORD $$${MKOBI_APP_PASSWORD}$$;
```
This ensures single quotes and other special characters in the password are treated as literal values, not SQL syntax.

---

### DC-005: CORS Origins Not Validated as Proper URLs in Production

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/config.py`, `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** In production, `create_app()` validates that `cors_origins` is non-empty and does not contain `"*"`. However, it does not validate that each origin is a well-formed URL. A misconfigured value like `CORS_ORIGINS=["your-domain.com"]` (missing `https://`) or `CORS_ORIGINS=[""]` (empty string) would be silently accepted, effectively allowing cross-origin requests from unintended sources or no sources. The `field_validator` in `Settings` only converts values to strings without URL format checking.

**Evidence:** `src/mkobi/app.py` — CORS validation in `create_app()`:
```python
if config.environment == EnvironmentEnum.PRODUCTION:
    if not config.cors_origins:
        raise ValueError("CORS origins must be configured for production")
    if "*" in config.cors_origins:
        raise ValueError("CORS wildcard (*) is not allowed in production...")
```
No URL format validation exists. `src/mkobi/config.py` `validate_cors_origins` only converts to `list[str]`.

**Recommendation:** Add URL format validation in the production CORS check:
```python
from urllib.parse import urlparse
for origin in config.cors_origins:
    parsed = urlparse(origin)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"Invalid CORS origin: {origin}")
```

---

### DC-006: Nginx Config Missing HTTPS/SSL, HSTS Header Sent Over HTTP

| Field | Value |
|-------|-------|
| **ID** | DC-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/nginx/nginx.conf` |
| **Classification** | advisory |

**Description:** The nginx configuration listens exclusively on port 80 (HTTP) and sends `Strict-Transport-Security` (HSTS) headers. Per RFC 6797, browsers ignore HSTS headers received over HTTP, making the header ineffective. The config lacks: (1) HTTPS listener on port 443, (2) SSL/TLS certificate configuration, (3) HTTP-to-HTTPS redirect. For production deployments, nginx should either terminate TLS itself or include a comment/placeholders documenting that TLS is handled by an upstream load balancer. The current config gives the impression that HTTPS is handled, but it is not.

**Evidence:** `docker/nginx/nginx.conf`:
```nginx
server {
    listen 80;
    # ...
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```
No `listen 443 ssl`, no `ssl_certificate` directive, no `return 301 https://...` redirect.

**Recommendation:** Add an HTTPS server block with SSL configuration, or at minimum add an HTTP→HTTPS redirect and document that TLS termination is expected at an upstream proxy. Remove HSTS from the HTTP-only block (move it to the HTTPS block) to avoid misleading security posture. Consider adding a placeholder config:
```nginx
server {
    listen 80;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    # ... existing location blocks
}
```

---

### DC-007: Nginx Config Missing client_max_body_size for Upload API

| Field | Value |
|-------|-------|
| **ID** | DC-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/nginx/nginx.conf`, `docker/docker-compose.yml` |
| **Classification** | advisory |

**Description:** The nginx configuration does not set `client_max_body_size`. The default is 1MB, which will cause nginx to reject any file upload larger than 1MB with a 413 error before the request reaches FastAPI. The application accepts uploads up to 100MB (`UPLOAD__MAX_FILE_SIZE_MB=100`), but nginx's default 1MB limit makes uploads impossible through the nginx path. Conversely, if the default were larger, huge requests would be proxied to the backend before being rejected. The nginx `/api` location block should have `client_max_body_size` aligned with the application's upload limit.

**Evidence:** `docker/nginx/nginx.conf` — No `client_max_body_size` directive in the server or location blocks. Default nginx `client_max_body_size` is 1MB.
`src/mkobi/config.py` — `UploadSettings.max_file_size_mb: int = 100` (100MB).
`docker/.env.production` — `UPLOAD__MAX_FILE_SIZE_MB=100`.

**Recommendation:** Add `client_max_body_size` to the nginx `/api` location block:
```nginx
location /api {
    client_max_body_size 100m;
    proxy_pass http://app:8000;
    # ... existing proxy_set_header directives
}
```
Consider making this value configurable via an environment variable to stay in sync with the backend's `UPLOAD__MAX_FILE_SIZE_MB`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 5 |
| LOW | 0 |

## Mandatory Fixes

- **DC-001** — App port 8000 exposed to host in production, bypassing nginx security layer
- **DC-002** — mkobi_app role granted CREATEDB privilege, violating documented least-privilege principle
- **DC-003** — /health/detailed endpoint exposed without authentication in production
- **DC-004** — SQL injection risk in init script via unsanitized password interpolation

## Advisory Recommendations

- **DC-005** — CORS origins not validated as proper URLs in production
- **DC-006** — Nginx config missing HTTPS/SSL; HSTS header ineffective over HTTP
- **DC-007** — Nginx config missing client_max_body_size, blocking uploads >1MB through nginx path

## Doc Updates Needed

No doc-update type findings in this phase.
