# Phase 05 Audit Findings — Infrastructure & Runtime Environment

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INF-001: Init Script SQL Syntax Error — GRANT CONNECT Statement Invalid

| Field | Value |
|-------|-------|
| **ID** | INF-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | docker/init-scripts/01-create-app-role.sh |
| **Classification** | mandatory |

**Description:** The PostgreSQL initialization script has a SQL syntax error in the GRANT CONNECT statement. The psql variable syntax `:'dbname'` quotes the value as an SQL string literal (`'bidb'`), but the GRANT CONNECT ON DATABASE command expects an identifier, not a quoted string. PostgreSQL rejects `'bidb'` as an invalid database name because the quotes are part of the literal value, not SQL string delimiters.

**Evidence:** 
- File: `docker/init-scripts/01-create-app-role.sh`, line 29
- Log excerpt from container `docker-db-1`:
```
2026-06-11 12:58:04.583 UTC [76] ERROR:  syntax error at or near "'bidb'" at character 27
LINE 1: GRANT CONNECT ON DATABASE 'bidb' TO mkobi_app;
```

**Recommendation:** The psql `:'variable'` syntax produces a quoted string literal. For identifiers like database names, use `:variable` (unquoted) or use the shell variable directly via `${POSTGRES_DB}`:
```sql
GRANT CONNECT ON DATABASE :dbname TO mkobi_app;
```
Or replace the line entirely with:
```sql
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO mkobi_app;
```
since this value is already available as a shell variable and doesn't require psql substitution.

---

### INF-002: PostgreSQL 18+ Volume Mount Path Incompatibility

| Field | Value |
|-------|-------|
| **ID** | INF-002 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | docker/docker-compose.yml, docker/docker-compose.test.yml |
| **Classification** | mandatory |

**Description:** PostgreSQL 18+ changed its internal data directory structure. When mounting a volume at `/var/lib/postgresql`, existing data from older PostgreSQL versions or different mount configurations causes startup failures. The container logs show: "PostgreSQL 18+ these Docker images are configured to store database data in a format which is compatible with pg_ctlcluster... There appears to be PostgreSQL data in /var/lib/postgresql/data which is incompatible with the current version."

**Evidence:** 
- Log excerpt from container `docker-db-1`:
```
Error: in 18+, these Docker images are configured to store database data in a format which is compatible with "pg_ctlcluster"...
PostgreSQL Database directory appears to contain a database; Skipping initialization
```
- PostgreSQL 18 now stores data in `/var/lib/postgresql/18/docker` subdirectory when properly configured
- Volume mount in compose: `postgres_data:/var/lib/postgresql` conflicts with new structure

**Recommendation:** Update the PostgreSQL volume mount path to align with PostgreSQL 18+ structure. Either:
1. Mount to `/var/lib/postgresql/18/data` (version-specific path) - but this requires updating on version changes
2. Mount to `/var/lib/postgresql` but ensure the volume is empty/fresh for new installations
3. Add documentation about the incompatibility and require `--remove-orphans` or volume cleanup when upgrading

This issue is documented in the project's own deployment docs as a known PostgreSQL 18 issue, but the root cause is the volume mount configuration.

---

### INF-003: Frontend Vite Dev Server Crashes on Windows with SIGBUS

| Field | Value |
|-------|-------|
| **ID** | INF-003 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | docker/docker-compose.override.yml (frontend service) |
| **Classification** | mandatory |

**Description:** The frontend development server (Vite) crashes with SIGBUS signal when run in Docker on Windows. This is a known issue with Node.js file watching and filesystem polling on Docker Desktop for Windows. The container restarts repeatedly and never becomes healthy.

**Evidence:**
- Log excerpt from container `docker-frontend-1`:
```
npm error command failed
npm error signal SIGBUS
npm error command sh -c vite --host 0.0.0.0
```
- Container status shows `Exited (1)` after repeated restart attempts

**Recommendation:** Add Windows-specific environment configuration for the frontend service in `docker-compose.override.yml`:
```yaml
frontend:
  environment:
    - CHOKIDAR_USEPOLLING=true  # Already present
    - UV_USE_SYSTEM_PYTHON=1  # May help with compatibility
```
Consider also adding platform-specific documentation or switching to WSL2-based Docker for development on Windows.

---

### INF-004: PostgreSQL Collation Version Error (Cosmetic but Misleading)

| Field | Value |
|-------|-------|
| **ID** | INF-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml, docker/docker-compose.test.yml |
| **Classification** | advisory |

**Description:** PostgreSQL 18 logs contain repeated `ERROR: syntax error at or near "COLLATION_VERSION"` messages. The project documentation acknowledges this is caused by a Debian postgresql-common package incompatibility with PostgreSQL 18's stricter parser. While documented as harmless, these errors clutter logs and may trigger false alerts in monitoring systems.

**Evidence:**
- Log excerpt from test-db container:
```
ERROR:  syntax error at or near "COLLATION_VERSION" at character 34
STATEMENT:  ALTER DATABASE template1 REFRESH COLLATION_VERSION
```

**Recommendation:** While documented as harmless, consider adding log filtering or upgrading to a newer PostgreSQL image that resolves this incompatibility. The builtin locale provider with `C.UTF-8` already provides immutable collation, making this error unnecessary.

---

### INF-005: Production Compose Uses Development Target by Default

| Field | Value |
|-------|-------|
| **ID** | INF-005 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | mandatory |

**Description:** The production docker-compose.yml uses `target: ${DOCKER_TARGET:-prod}` but the default value in the `.env` file is `ENV=development`. When running `docker compose up -d` without explicitly setting `DOCKER_TARGET`, the build uses the default `prod` target correctly. However, the environment variable `ENV` in the `.env` file is set to `development`, which causes the application to use development settings even in a production container build. This creates confusion between build target and runtime environment.

**Evidence:**
- File: `docker/docker-compose.yml`, line 82: `target: ${DOCKER_TARGET:-prod}`
- File: `.env`, line 10: `ENV=development`
- The production profile services inherit this development ENV value

**Recommendation:** Separate build-time target variables from runtime environment variables. Either:
1. Use `ENV=production` in `.env` for production deployments
2. Or make the compose file more explicit about the expected environment configuration
The decoupling of `DOCKER_TARGET` (build) from `ENV` (runtime) is correct, but the `.env` file having `ENV=development` while used for production compose creates misconfiguration risk.

---

### INF-006: Test Compose Exposes Internal Ports to Host

| Field | Value |
|-------|-------|
| **ID** | INF-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.test.yml |
| **Classification** | advisory |

**Description:** The test Docker Compose file exposes database (5433) and Redis (6380) ports to the host machine. While documented as a LOW severity risk because test data is non-production, this still represents a deviation from production isolation principles and could allow unintended cross-talk on shared machines.

**Evidence:**
- File: `docker/docker-compose.test.yml`, lines 41-42 and 64-65:
```yaml
ports:
  - "5433:5432"  # test-db
ports:
  - "6380:6379"  # test-redis
```
- File: `docker/docker-compose.test.yml`, line 147-148:
```yaml
ports:
  - "8001:8000"  # test-app
```

**Recommendation:** The exposure is intentional for development workflow convenience. However, consider:
1. Binding to `127.0.0.1` instead of default `0.0.0.0` to restrict access
2. Adding a note in the documentation about the security implications for CI/CD environments where this should be avoided

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 1 |

## Mandatory Fixes

- INF-001: Init Script SQL Syntax Error causing authentication failures
- INF-002: PostgreSQL 18+ volume mount incompatibility causing container startup failures
- INF-003: Frontend Vite dev server crash on Windows (SIGBUS)
- INF-005: Production compose uses development ENV setting

## Advisory Recommendations

- INF-004: PostgreSQL Collation Version error (cosmetic, documented)
- INF-006: Test compose port exposure (documented design decision, LOW risk)

---

## Notes on Investigation Limitations

The audit was performed with a development `.env` file containing placeholder values. The production profile (nginx, rq-worker) could not be fully tested because the base app service failed to start due to INF-001. The test environment services started successfully but with the documented port exposure behavior.