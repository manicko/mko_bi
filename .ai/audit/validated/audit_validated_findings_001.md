# Validated Audit Findings — Docker & Runtime Environment

**Date:** 2026-05-25
**Source Reports:** audit_report_001.md, audit_report_002.md
**Scope:** Dockerfile, docker-compose files, nginx config, init scripts, .dockerignore, application config
**Validator:** System Integrity Validation Agent

---

## Validation Summary

| Metric | Count |
|--------|-------|
| Total findings in source reports | 19 |
| Validated (confirmed) | 14 |
| Rejected (invalid/stale/speculative) | 4 |
| Merged (duplicates across reports) | 2 unique findings merged |
| Severity escalations confirmed | 3 (HIGH→CRITICAL) |
| New findings from runtime analysis | 1 |

---

## Architecture Consistency Notes

The audit scope is purely **infrastructure/deployment** — Docker, Compose, Nginx. No application-layer architecture changes are proposed. All validated findings are confined to the `docker/` directory and `src/mkobi/app.py` (one finding). The findings do not cross architectural boundaries (API → Service → Repository) and do not require dependency graph changes.

**Rollout safety:** All validated findings are independent configuration changes. No circular dependencies detected. Changes can be applied in any order, with one exception: the `AUTO_MIGRATE` finding (FINDING-004) should be applied together with verification that the advisory lock mechanism works correctly.

---

## CRITICAL Findings

### FINDING-001: Default JWT Secret Key in Docker Compose

- **ID:** FINDING-001
- **Title:** Default JWT__SECRET_KEY hardcoded in docker-compose.yml
- **Severity:** CRITICAL
- **Source:** audit_report_001.md (HIGH), audit_report_002.md (CRITICAL)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.yml` lines 56, 92, 149 use `${JWT__SECRET_KEY:-dev-secret-key-for-local-development}`. If the environment variable is not set externally, all environments (including production) sign JWT tokens with a publicly known secret. No `${VAR:?error}` enforcement exists.

**Impact:**
- Complete authentication bypass in production if `.env` is not configured
- Attackers can forge valid JWT tokens using the known default secret
- Affects all services: app, migrate, rq-worker

**Root Cause:**
Missing enforcement pattern for production-critical secrets in the base compose file.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 56, 92, 149
- `docker/docker-compose.override.yml` — line 60 (also hardcoded, not templated)

**Recommendation:**
Change to `${JWT__SECRET_KEY:?JWT__SECRET_KEY is required}` in the base compose file. In the override file, use `${JWT__SECRET_KEY:-dev-secret-key-for-local-development}` to allow `.env` override.

**Rollout Considerations:**
- Must be coordinated with deployment process — ensure `.env` or CI/CD pipeline provides the secret
- Zero-downtime: can be applied before next deployment
- Rollback: revert to previous compose file

**Validation Notes:**
Confirmed by direct source inspection. The finding is technically correct and operationally critical. Severity escalation from HIGH to CRITICAL is justified — this is a direct security vulnerability.

---

### FINDING-002: Default Database Password in Docker Compose

- **ID:** FINDING-002
- **Title:** Default DATABASE__PASSWORD hardcoded in docker-compose.yml
- **Severity:** CRITICAL
- **Source:** audit_report_001.md (HIGH), audit_report_002.md (CRITICAL)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.yml` lines 21, 53, 85 use `${DATABASE__PASSWORD:-postgres}`. If not overridden, production uses a well-known database password.

**Impact:**
- Database compromise if exposed to network
- Affects both the postgres superuser and application-level access

**Root Cause:**
Missing enforcement pattern for database credentials.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 21, 53, 85

**Recommendation:**
Change to `${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}`.

**Rollout Considerations:**
- Must ensure production deployment pipeline provides the password
- No application code changes needed

**Validation Notes:**
Confirmed by direct source inspection. Severity escalation to CRITICAL is justified.

---

### FINDING-003: Default Admin Credentials in Docker Compose

- **ID:** FINDING-003
- **Title:** Default admin credentials in docker-compose.yml
- **Severity:** CRITICAL
- **Source:** audit_report_001.md (HIGH), audit_report_002.md (CRITICAL)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.yml` lines 59, 95-96, 152-153 use `${ADMIN_USERNAME:-admin@example.com}` and `${ADMIN_PASSWORD:-admin@example.com}`. While `config.py` validates against weak credentials in production (via `validate_admin_credentials`), the compose file provides these as defaults, creating a false sense of safety.

**Impact:**
- Production starts with known admin credentials if not overridden
- The app-level validation in `config.py` (lines 17-18, `WEAK_USERNAMES`/`WEAK_PASSWORDS`) blocks `admin`/`admin` but NOT `admin@example.com`/`admin@example.com` — the default values bypass the weak credential check

**Root Cause:**
Default admin credentials exist in compose, and the app-level validation does not catch the specific default values.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 59, 95-96, 152-153
- `docker/docker-compose.override.yml` — lines 62-63 (hardcoded, not templated)
- `src/mkobi/config.py` — `WEAK_USERNAMES`, `WEAK_PASSWORDS`, `validate_admin_credentials`

**Recommendation:**
Remove default admin credentials from compose files. Use `${ADMIN_USERNAME:?ADMIN_USERNAME is required}` pattern. Additionally, extend `validate_admin_credentials` in `config.py` to reject `admin@example.com` as a username in production.

**Rollout Considerations:**
- Must ensure production deployment provides admin credentials via secrets
- The `config.py` validation enhancement is a separate small change that should be bundled

**Validation Notes:**
Confirmed by direct source inspection. Severity escalation to CRITICAL is justified. The interaction between compose defaults and incomplete app-level validation creates a real security gap.

---

### FINDING-003B: mkobi_app Role Not Created or Password Out of Sync — Application Cannot Start

- **ID:** FINDING-003B
- **Title:** mkobi_app database role missing or password mismatch — app fails to connect to PostgreSQL
- **Severity:** CRITICAL
- **Source:** Runtime log analysis (new finding, not in original audit reports)
- **Status:** VALIDATED — CONFIRMED by runtime evidence

**Description:**
The application fails to start with `password authentication failed for user "mkobi_app"`. The error chain is:

1. `docker-compose.yml` configures the app with `DATABASE__USER: mkobi_app` and `DATABASE__PASSWORD: ${MKOBI_APP_PASSWORD:-secure_password_placeholder}`
2. The `mkobi_app` role is created by `docker/init-scripts/01-create-app-role.sh` which runs only on **first-time** PostgreSQL initialization (empty volume)
3. If the `postgres_data` volume already exists (e.g., after `docker compose down` without `-v`, or after a restart), the init script does NOT run
4. The role `mkobi_app` either does not exist in the database, or exists with a different password from a previous run
5. The application has no retry/wait logic — it attempts one connection and crashes

**Observed error:**
```
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "mkobi_app"
→ DatabaseNotFoundError: Main database not accessible
→ Application startup failed. Exiting.
```

**Impact:**
- Application cannot start — complete service outage
- Occurs in any scenario where the PostgreSQL volume persists but the role is missing or has a wrong password
- Common scenarios: volume recreated, password changed, first deployment to a new environment, Docker volume cleanup
- No self-healing mechanism — requires manual intervention (drop volume, recreate role, or fix password)

**Root Cause:**
The init script pattern (`/docker-entrypoint-initdb.d/`) is inherently fragile:
- Scripts run only on first container initialization with an empty volume
- No mechanism to update the role password when `MKOBI_APP_PASSWORD` changes
- No idempotency on subsequent starts — the app assumes the role exists with the correct password
- The app has no connection retry or role-creation fallback

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 84-85 (DATABASE__USER/DATABASE__PASSWORD for app)
- `docker/docker-compose.yml` — lines 16-23 (db service: POSTGRES_PASSWORD, MKOBI_APP_PASSWORD)
- `docker/init-scripts/01-create-app-role.sh` — entire file (role creation logic)
- `src/mkobi/db/starter.py` — `_check_db_connection()` (no retry, no role creation)
- `src/mkobi/config.py` — `DatabaseSettings` (user defaults to `mkobi_app`)

**Recommendation:**

The fix should address both the immediate startup failure and the long-term reliability:

**Short-term (immediate):** Add retry logic with exponential backoff to `_check_db_connection()` in `starter.py`. The app should retry 5-10 times with increasing delays before giving up. This handles the race condition where the app starts before the migrate service has completed.

**Medium-term (robust):** Replace the init script pattern with an application-level role management approach:
- On startup, the app (using admin credentials) should check if `mkobi_app` role exists and create/update it with the correct password
- This is idempotent and works regardless of volume state
- The init script can be kept as a fallback but should not be the sole mechanism

**Long-term (best):** Use a proper database migration tool for role management (e.g., a dedicated migration script that runs before Alembic, or integrate role setup into the Alembic migration pipeline).

**Rollout Considerations:**
- Short-term fix (retry logic) is low-risk and can be deployed immediately
- Medium-term fix requires the app to have admin credentials at startup (already available via `DATABASE__ADMIN_USER`/`DATABASE__ADMIN_PASSWORD`)
- Must ensure the retry logic doesn't mask real connection issues (log each retry attempt)
- The init script should NOT be removed until the application-level role management is in place and tested

**Validation Notes:**
Confirmed by runtime log analysis. The error `password authentication failed for user "mkobi_app"` is a direct consequence of the fragile init script pattern. This is a **blocking issue** — the application cannot start in the current configuration. The finding is CRITICAL because it represents a complete service outage that requires manual intervention to resolve.

---

## HIGH Findings

### FINDING-004: AUTO_MIGRATE=false Creates Fragile Migration Pattern

- **ID:** FINDING-004
- **Title:** AUTO_MIGRATE=false in production creates fragile two-step migration process
- **Severity:** HIGH
- **Source:** audit_report_001.md (HIGH), audit_report_002.md (HIGH)
- **Status:** VALIDATED — CONFIRMED (with nuance)

**Description:**
`docker-compose.yml` line 101 sets `AUTO_MIGRATE: "false"` for the app service. The deployment documentation (`docs/10-deployment/deployment.md` line 194) states `AUTO_MIGRATE=true` as the default. While line 196 of the same doc describes the separate migrate service pattern as valid, the current implementation creates unnecessary complexity.

**Impact:**
- If the migrate service fails silently, the app starts without migrations — no safety net
- Two migration mechanisms (migrate service + AUTO_MIGRATE) create double responsibility
- Operational complexity: operators must monitor both the migrate service exit code AND the app's migration state
- The advisory lock mechanism (already implemented in `DatabaseStarter`) makes the separate migrate service redundant for single-instance deployments

**Root Cause:**
The separate migrate service pattern was adopted without considering that `AUTO_MIGRATE=true` with advisory lock provides the same safety with simpler operations.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 101, 157
- `src/mkobi/db/starter.py` — `DatabaseStarter` class (already has advisory lock)

**Recommendation:**
Set `AUTO_MIGRATE: "true"` in the app service. The advisory lock in `DatabaseStarter` prevents race conditions. This simplifies the deployment to a single migration mechanism while maintaining safety. The separate migrate service can be kept as a no-op or removed.

**Rollout Considerations:**
- Low risk: the advisory lock already exists in the codebase
- Should be tested in staging to verify the advisory lock works correctly with concurrent startup
- The migrate service can be kept (it will simply succeed immediately if migrations are already applied)

**Validation Notes:**
The audit reports state the spec "requires" AUTO_MIGRATE=true. The actual documentation (deployment.md) describes both patterns as valid. However, from a **maintainability and operational simplicity** perspective, `AUTO_MIGRATE=true` with advisory lock is strictly better: fewer moving parts, no silent failure mode, same safety guarantees. The finding is validated not because the spec mandates it, but because it is the architecturally superior approach.

---

### FINDING-005: Swagger UI and ReDoc Always Enabled

- **ID:** FINDING-005
- **Title:** Swagger UI (/docs) and ReDoc (/redoc) always enabled, even in production
- **Severity:** HIGH
- **Source:** audit_report_002.md (HIGH) — new finding not in report 001
- **Status:** VALIDATED — CONFIRMED

**Description:**
`src/mkobi/app.py` lines 138-139 set `docs_url="/docs"` and `redoc_url="/redoc"` unconditionally in the `create_app()` function. These endpoints expose the full API schema, endpoint structure, parameter details, and data models to anyone who can reach the server.

**Impact:**
- Information disclosure: attackers can map the entire API surface
- Exposes internal data model names, field types, and validation rules
- No authentication required on docs endpoints

**Root Cause:**
No environment-based conditional for documentation endpoints.

**Affected Modules/Symbols:**
- `src/mkobi/app.py` — `create_app()` function, lines 133-141

**Recommendation:**
Conditionally disable in production:
```python
docs_url=None if config.environment == EnvironmentEnum.PRODUCTION else "/docs",
redoc_url=None if config.environment == EnvironmentEnum.PRODUCTION else "/redoc",
```

**Rollout Considerations:**
- Isolated change in `create_app()` — no dependencies
- `EnvironmentEnum.PRODUCTION` already exists in `src/mkobi/models/enums.py`
- Zero risk: only affects documentation endpoint availability

**Validation Notes:**
Confirmed by direct source inspection. This is a clear security issue with a simple, safe fix. The `EnvironmentEnum` is already imported and used in the same function (line 126), so the fix is minimal and idiomatic.

---

### FINDING-006: No HEALTHCHECK Instruction in Dockerfile

- **ID:** FINDING-006
- **Title:** No HEALTHCHECK instruction in Dockerfile
- **Severity:** HIGH (escalated from MEDIUM)
- **Source:** audit_report_001.md (MEDIUM), audit_report_002.md (HIGH)
- **Status:** VALIDATED — CONFIRMED

**Description:**
The Dockerfile has no `HEALTHCHECK` instruction in any stage. Health checks are only configured at the compose level (`docker-compose.yml` lines 107-112). If the image is run without compose (Kubernetes, ECS, manual `docker run`), no health check exists.

**Impact:**
- Image is not self-contained for non-compose orchestrators
- Kubernetes/ECS deployments cannot determine container health
- Limits deployment portability

**Root Cause:**
Health check was only added at the compose level, not in the Dockerfile itself.

**Affected Modules/Symbols:**
- `docker/Dockerfile` — prod stage (line 138)

**Recommendation:**
Add to the prod stage:
```
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
```
Note: requires `curl` in the prod image (already installed in base stage).

**Rollout Considerations:**
- Requires `curl` in prod image (already present via base stage)
- No application changes needed
- Compose-level health check can be removed or kept (Dockerfile HEALTHCHECK takes precedence)

**Validation Notes:**
Confirmed by direct source inspection. Severity escalation to HIGH is justified — this limits deployment portability and is a standard Dockerfile best practice.

---

## MEDIUM Findings

### FINDING-007: Dev Dependencies in Production Image

- **ID:** FINDING-007
- **Title:** build-essential and libpq-dev installed in base stage, inherited by prod
- **Severity:** MEDIUM
- **Source:** audit_report_001.md (MEDIUM), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker/Dockerfile` lines 42-46 install `build-essential` and `libpq-dev` in the `base` stage, which is inherited by `prod`. These are compile-time dependencies. The prod stage only needs `libpq5` (runtime shared library).

**Impact:**
- Increased prod image size (~100-200MB)
- Increased attack surface (compilers, headers)
- Slower image pulls and deployments

**Root Cause:**
System dependencies are installed in the shared `base` stage rather than being split between build-time and runtime needs.

**Affected Modules/Symbols:**
- `docker/Dockerfile` — base stage (lines 42-46), prod stage (line 115)

**Recommendation:**
Split system deps: keep `build-essential`/`libpq-dev` only in `base` for dev/test. Create a `prod-base` stage (or modify `prod`) that starts from a clean python:3.12-slim-bookworm and installs only `libpq5` and `curl`.

**Rollout Considerations:**
- Requires Dockerfile restructuring — moderate complexity
- Must verify all prod dependencies work with `libpq5` only (they should — SQLAlchemy/asyncpg only need the runtime library)
- Test the rebuilt image thoroughly before production deployment

**Validation Notes:**
Confirmed by direct source inspection. This is a well-known Docker best practice. The fix is straightforward but requires careful testing.

---

### FINDING-008: uv Installed via Unpinned curl | sh

- **ID:** FINDING-008
- **Title:** uv installed via unpinned curl pipe to shell
- **Severity:** MEDIUM
- **Source:** audit_report_001.md (LOW), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker/Dockerfile` line 49: `curl -LsSf https://astral.sh/uv/install.sh | sh`. The version is not pinned, so builds are not reproducible. Piping curl to sh is a security anti-pattern.

**Impact:**
- Non-reproducible builds: different uv versions may be installed at different times
- Security risk: the installer script is executed without verification
- Potential for supply chain attacks

**Root Cause:**
No version pinning and no checksum verification for the uv installer.

**Affected Modules/Symbols:**
- `docker/Dockerfile` — line 49

**Recommendation:**
Pin uv version and use checksum verification:
```dockerfile
ARG UV_VERSION=0.7.12
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh
```
Or use `pip install uv==${UV_VERSION}` in a prior step.

**Rollout Considerations:**
- Low risk: only affects build-time tooling
- Should verify the pinned version is compatible with the current `uv.lock` format

**Validation Notes:**
Confirmed by direct source inspection. Severity escalation from LOW to MEDIUM is justified — non-reproducible builds are a real operational concern.

---

### FINDING-009: CORS_ORIGINS Hardcoded in Production Compose

- **ID:** FINDING-009
- **Title:** CORS_ORIGINS hardcoded to localhost in production compose
- **Severity:** MEDIUM (escalated from LOW)
- **Source:** audit_report_001.md (LOW), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.yml` line 99: `CORS_ORIGINS: '["http://localhost:3000", "http://localhost:5173"]'`. This is hardcoded, not templated. If deployed to production without overriding, the API rejects all cross-origin requests from real frontends.

**Impact:**
- Production deployment will have broken CORS unless explicitly overridden
- No deployment-time enforcement

**Root Cause:**
CORS_ORIGINS was hardcoded for development convenience without a template variable.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — line 99

**Recommendation:**
Use `${CORS_ORIGINS:?CORS_ORIGINS is required}` for production, or at minimum `${CORS_ORIGINS:["http://localhost:3000"]}`.

**Rollout Considerations:**
- Must ensure production deployment provides CORS_ORIGINS
- The app already validates CORS in `app.py` lines 126-131 (raises ValueError if not set in production), which provides a safety net

**Validation Notes:**
Confirmed by direct source inspection. Severity escalation to MEDIUM is justified — this will break production deployments.

---

### FINDING-010: MKOBI_APP_PASSWORD Placeholder Not Enforced

- **ID:** FINDING-010
- **Title:** MKOBI_APP_PASSWORD defaults to placeholder value
- **Severity:** MEDIUM (escalated from LOW)
- **Source:** audit_report_001.md (LOW), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.yml` lines 23-24: `MKOBI_APP_PASSWORD: ${MKOBI_APP_PASSWORD:-secure_password_placeholder}`. The placeholder name suggests it should be changed, but nothing enforces this.

**Impact:**
- Production may run with a known placeholder password for the application database role

**Root Cause:**
Missing enforcement pattern for the application database password.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 23-24

**Recommendation:**
Use `${MKOBI_APP_PASSWORD:?MKOBI_APP_PASSWORD is required}`.

**Rollout Considerations:**
- Must ensure production deployment provides this value
- No application changes needed

**Validation Notes:**
Confirmed by direct source inspection.

---

### FINDING-011: Test Compose Race Condition — Dual Migration Mechanism

- **ID:** FINDING-011
- **Title:** Both test-migrate service and AUTO_MIGRATE=true in test-app
- **Severity:** MEDIUM
- **Source:** audit_report_001.md (MEDIUM), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.test.yml` has both a `test-migrate` service (line 45-75) that runs `alembic upgrade head` AND `test-app` with `AUTO_MIGRATE: "true"` (line 102). This creates a potential race condition and wastes time.

**Impact:**
- Potential race condition if test-app starts before test-migrate completes (though `depends_on` mitigates this)
- Wasted CI time running migrations twice
- Confusing: which mechanism is the "real" migration path?

**Root Cause:**
Redundant migration mechanisms in the test compose file.

**Affected Modules/Symbols:**
- `docker/docker-compose.test.yml` — lines 45-75 (test-migrate), line 102 (AUTO_MIGRATE)

**Recommendation:**
Remove `AUTO_MIGRATE: "true"` from `test-app` since `test-migrate` already handles it. The `depends_on: test-migrate: condition: service_completed_successfully` ensures migrations run first.

**Rollout Considerations:**
- Low risk: only affects test environment
- May slightly speed up test container startup

**Validation Notes:**
Confirmed by direct source inspection.

---

### FINDING-012: Hardcoded Values in Dev Override

- **ID:** FINDING-012
- **Title:** Hardcoded JWT__SECRET_KEY and admin credentials in dev override
- **Severity:** MEDIUM
- **Source:** audit_report_001.md (MEDIUM), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED (with nuance)

**Description:**
`docker-compose.override.yml` line 60 hardcodes `JWT__SECRET_KEY: dev-secret-key-for-local-development` (not templated), always overriding any `.env` value. Lines 62-63 hardcode admin credentials.

**Impact:**
- Dev override always overrides `.env` values — cannot use a different dev secret via `.env`
- Inconsistency: base compose uses `${VAR:-default}`, override uses hardcoded values

**Root Cause:**
Inconsistent templating approach between base compose and override.

**Affected Modules/Symbols:**
- `docker/docker-compose.override.yml` — lines 60, 62-63

**Recommendation:**
Use `${JWT__SECRET_KEY:-dev-secret-key-for-local-development}` and `${ADMIN_USERNAME:-admin@example.com}` patterns for consistency.

**Rollout Considerations:**
- Zero risk: only affects development environment
- Improves consistency and allows `.env` override in development

**Validation Notes:**
Confirmed by direct source inspection. Severity is MEDIUM (not HIGH/CRITICAL) because this is development-only and the hardcoded values are acceptable defaults for local dev.

---

### FINDING-013: Nginx SSL Mismatch

- **ID:** FINDING-013
- **Title:** Nginx listens on port 80 only, no HTTPS despite compose mapping port 443
- **Severity:** MEDIUM
- **Source:** audit_report_001.md (LOW), audit_report_002.md (MEDIUM)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker-compose.yml` maps port 443 (line 172: `- "443:443"`) but `nginx.conf` has no SSL server block — only a `listen 80` server block (line 14). Port 443 is mapped but nothing listens there with TLS.

**Impact:**
- Port 443 mapping is misleading — connections will fail or hang
- No TLS termination capability despite the infrastructure being partially set up

**Root Cause:**
Incomplete nginx SSL configuration — port mapping was added without the corresponding server block.

**Affected Modules/Symbols:**
- `docker/nginx/nginx.conf` — line 14
- `docker/docker-compose.yml` — line 172

**Recommendation:**
Either:
1. Add SSL server block to nginx.conf (requires SSL certificates), OR
2. Remove the 443 port mapping from docker-compose.yml

Option 2 is preferred for now — SSL should be added intentionally with proper certificate management, not as a partial configuration.

**Rollout Considerations:**
- If removing 443 mapping: zero risk, immediate improvement in clarity
- If adding SSL: requires certificate management strategy (Let's Encrypt, self-signed, etc.)

**Validation Notes:**
Confirmed by direct source inspection. Severity escalation to MEDIUM is justified — the misleading port mapping could cause operational confusion.

---

### FINDING-014: Missing Security Headers in Nginx

- **ID:** FINDING-014
- **Title:** No security headers in nginx configuration
- **Severity:** MEDIUM (LOW in report 002, escalated)
- **Source:** audit_report_002.md (LOW)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker/nginx/nginx.conf` lacks security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`.

**Impact:**
- Missing defense-in-depth against XSS, clickjacking, MIME-type sniffing
- The app sets some headers via FastAPI middleware, but nginx should also set them for static files

**Root Cause:**
Basic nginx configuration without security hardening.

**Affected Modules/Symbols:**
- `docker/nginx/nginx.conf` — server block (lines 13-39)

**Recommendation:**
Add security headers to the server block:
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Rollout Considerations:**
- Low risk: additive change, no breaking effects
- Should verify headers don't conflict with any frontend requirements

**Validation Notes:**
Confirmed by direct source inspection. Severity escalated from LOW to MEDIUM because these are standard security headers that should be present by default.

---

## LOW Findings

### FINDING-015: Nginx Service in Base Compose File

- **ID:** FINDING-015
- **Title:** Nginx service uses profiles but is defined in base compose
- **Severity:** LOW
- **Source:** audit_report_001.md (LOW), audit_report_002.md (LOW)
- **Status:** VALIDATED — CONFIRMED

**Description:**
`docker/docker-compose.yml` lines 165-178 define the nginx service with `profiles: [production]`. The service is always parsed but only activated with `--profile production`. The nginx.conf mounts `../frontend/dist` which is only available after a frontend build.

**Impact:**
- Minor: base compose file contains production-only services
- nginx.conf references frontend build output that may not exist

**Root Cause:**
Structural organization choice — nginx is in the base file behind a profile.

**Affected Modules/Symbols:**
- `docker/docker-compose.yml` — lines 165-178

**Recommendation:**
Consider moving nginx to a separate `docker-compose.prod.yml` for cleaner separation. At minimum, add a comment documenting that nginx requires a prior frontend build.

**Rollout Considerations:**
- Low priority: current approach works, just not ideal organizationally
- Moving to a separate file would require updating deployment scripts

**Validation Notes:**
Confirmed by direct source inspection. This is a minor structural issue, not a functional problem.

---

### FINDING-016: Dev Command Import Path Inconsistency

- **ID:** FINDING-016
- **Title:** Dev command uses src.mkobi.main:app instead of mkobi.main:app
- **Severity:** LOW
- **Source:** audit_report_001.md (LOW), audit_report_002.md (LOW)
- **Status:** VALIDATED — CONFIRMED (with nuance)

**Description:**
`docker-compose.override.yml` line 73 uses `src.mkobi.main:app` while the spec shows `mkobi.main:app`. The prod stage in Dockerfile also uses `src.mkobi.main:app` (line 138), so this is actually consistent with prod.

**Impact:**
- Minimal: the import path works correctly due to PYTHONPATH and directory structure
- Minor inconsistency with documentation examples

**Root Cause:**
The `src/` layout requires `src.mkobi.main:app` when PYTHONPATH includes `/app` (the working directory). The documentation examples assume a different layout.

**Affected Modules/Symbols:**
- `docker/docker-compose.override.yml` — line 73
- `docker/Dockerfile` — line 138 (prod, same pattern)

**Recommendation:**
No code change needed. Update documentation to reflect the actual `src/` layout import path. Both prod and dev use the same path, which is correct.

**Rollout Considerations:**
- Documentation-only change
- No functional impact

**Validation Notes:**
Confirmed by direct source inspection. The audit report's concern about inconsistency is partially valid (docs don't match code) but the code itself is consistent between dev and prod. This is a documentation fix, not a code fix.

---

## Rejected Findings

### REJECTED-001: Missing prod-slim Build Target

- **Source:** audit_report_001.md (MEDIUM), audit_report_002.md (HIGH)
- **Reason:** The audit reports claim "the spec defines a prod-slim target." However, the actual deployment documentation (`docs/10-deployment/deployment.md` lines 176-181) lists only 4 targets: `base`, `dev`, `test`, `prod`. There is no `prod-slim` target in the specification. The finding references a non-existent requirement.
- **Decision:** REJECTED — no spec requirement exists. If a prod-slim target is desired, it should be proposed as a new feature, not treated as a missing implementation.

---

### REJECTED-002: Prod CMD Should Use `uv run uvicorn` Per Spec

- **Source:** audit_report_001.md (MEDIUM), audit_report_002.md (mentioned in recommendations)
- **Reason:** The audit claims the spec requires `uv run uvicorn mkobi.main:app` for the prod Dockerfile CMD. The actual documentation (`docs/10-deployment/deployment.md` line 55) shows `uv run uvicorn mkobi.main:app` for **local development**, not for Docker production. The Dockerfile prod stage uses `uv sync --frozen --no-dev` which installs into a virtual environment, and the PATH includes `/app/.venv/bin`. Using `uvicorn` directly is the correct approach for a Docker container — `uv run` would add unnecessary overhead and require uv to remain installed in the production image. The current approach follows Docker best practices.
- **Decision:** REJECTED — the spec does not require `uv run` for Docker prod, and using it would be worse for production (larger image, unnecessary dependency).

---

### REJECTED-003: .dockerignore Needs Changes

- **Source:** audit_report_001.md, audit_report_002.md
- **Reason:** Both audit reports explicitly state: "No problems identified. Well-structured, excludes .env, .git, caches, and IDE files." and "No changes needed."
- **Decision:** REJECTED — no finding to validate. Included here for completeness to show all audit sections were reviewed.

---

### REJECTED-004: Init Script Needs Changes

- **Source:** audit_report_001.md, audit_report_002.md
- **Reason:** Both audit reports explicitly state: "No problems identified. Properly implements least-privilege role creation with DROP IF EXISTS for idempotency." and "No changes needed."
- **Decision:** REJECTED — no finding to validate. Included here for completeness.

---

## Dependency Validation

### Dependency Graph

```
FINDING-001 (JWT secret) ──┐
FINDING-002 (DB password) ──┤
FINDING-003 (Admin creds) ──┤── Independent, no inter-dependencies
FINDING-010 (App password) ─┤
FINDING-009 (CORS) ─────────┘

FINDING-003B (mkobi_app role) ── CRITICAL: Must be fixed first, blocks all other fixes
  └─ Depends on: FINDING-002 (DB password) and FINDING-010 (App password) for correct credentials
  └─ Blocks: Everything — app cannot start until this is resolved

FINDING-004 (AUTO_MIGRATE) ── Independent, but verify advisory lock first

FINDING-005 (Swagger/ReDoc) ── Independent, isolated to app.py

FINDING-006 (HEALTHCHECK) ── Independent, Dockerfile-only

FINDING-007 (Dev deps) ── Independent, Dockerfile restructuring

FINDING-008 (uv pin) ── Independent, Dockerfile-only

FINDING-011 (Test race) ── Independent, test-compose-only

FINDING-012 (Dev override) ── Independent, dev-compose-only

FINDING-013 (Nginx SSL) ── Independent, nginx-only

FINDING-014 (Security headers) ── Independent, nginx-only

FINDING-015 (Nginx profile) ── Independent, compose structure

FINDING-016 (Import path) ── Documentation-only, no code dependency
```

### Circular Dependencies
**None detected.** All findings are independent configuration changes.

### Safe Parallel Execution
- FINDING-003B (mkobi_app role) MUST be fixed first — app cannot start without it
- All CRITICAL findings (001-003, 010) can be applied in a single compose file edit
- FINDING-005 (Swagger) is isolated to `app.py` — can be done independently
- FINDING-006, 007, 008 are Dockerfile changes — can be bundled together
- FINDING-013, 014 are nginx changes — can be bundled together
- FINDING-011 is test-only — can be done independently

---

## Rollout Safety Analysis

### Recommended Rollout Order

**Phase 0 — Unblock Application (immediate, blocking):**
0. FINDING-003B: Fix mkobi_app role — add retry logic + application-level role management
   - Without this fix, the application cannot start at all
   - Short-term: add retry with backoff to `_check_db_connection()`
   - Medium-term: add role creation/update to `DatabaseStarter.startup()`

**Phase 1 — Security Critical (immediate, after Phase 0):**
1. FINDING-001: JWT__SECRET_KEY enforcement
2. FINDING-002: DATABASE__PASSWORD enforcement
3. FINDING-003: Admin credentials enforcement (+ config.py validation enhancement)
4. FINDING-010: MKOBI_APP_PASSWORD enforcement
5. FINDING-005: Swagger/ReDoc conditional disable

**Phase 2 — Infrastructure Hardening (next sprint):**
6. FINDING-006: Dockerfile HEALTHCHECK
7. FINDING-007: Dev deps removal from prod
8. FINDING-008: uv version pin
9. FINDING-009: CORS_ORIGINS templating
10. FINDING-013: Nginx SSL fix
11. FINDING-014: Nginx security headers

**Phase 3 — Operational Improvement (when convenient):**
12. FINDING-004: AUTO_MIGRATE=true (verify advisory lock first)
13. FINDING-011: Test compose race condition
14. FINDING-012: Dev override templating
15. FINDING-015: Nginx service organization
16. FINDING-016: Documentation update

### Rollback Feasibility
All changes are configuration-only (compose files, Dockerfile, nginx.conf, app.py). Each can be rolled back independently by reverting the specific file. No database migrations or schema changes are required.

---

## Semantic Targeting Stability

### Anchor Stability Assessment

| Finding | Anchor Type | Stability | Notes |
|---------|------------|-----------|-------|
| FINDING-001 | env var reference in compose | HIGH | Variable name `JWT__SECRET_KEY` is stable |
| FINDING-002 | env var reference in compose | HIGH | Variable name `DATABASE__PASSWORD` is stable |
| FINDING-003 | env var reference in compose | HIGH | Variable names `ADMIN_USERNAME`/`ADMIN_PASSWORD` are stable |
| FINDING-003B | method in `DatabaseStarter` | HIGH | `_check_db_connection()` and `startup()` are stable anchors |
| FINDING-004 | env var in compose | HIGH | Variable name `AUTO_MIGRATE` is stable |
| FINDING-005 | function parameter in `create_app()` | HIGH | `docs_url`/`redoc_url` params are stable FastAPI API |
| FINDING-006 | Dockerfile stage boundary | HIGH | `prod` stage is a stable anchor |
| FINDING-007 | Dockerfile RUN instruction | MEDIUM | Line-based; may shift if base stage changes |
| FINDING-008 | Dockerfile RUN instruction | MEDIUM | Line-based; may shift if base stage changes |
| FINDING-009 | env var in compose | HIGH | Variable name `CORS_ORIGINS` is stable |
| FINDING-010 | env var in compose | HIGH | Variable name `MKOBI_APP_PASSWORD` is stable |
| FINDING-011 | env var in test compose | HIGH | Variable name `AUTO_MIGRATE` is stable |
| FINDING-012 | env var in override | HIGH | Variable names are stable |
| FINDING-013 | nginx server block | HIGH | Server block is a stable structural anchor |
| FINDING-014 | nginx server block | HIGH | Server block is a stable structural anchor |
| FINDING-015 | compose service definition | HIGH | Service name `nginx` is stable |
| FINDING-016 | compose command value | HIGH | Command string is stable |

**No fragile anchors detected.** All findings target stable semantic anchors (environment variable names, function parameters, service names, stage names). No line-based assumptions are required for execution.

---

## Execution Applicability

### Pre-Execution Checklist

Before executing any finding fix:
1. [ ] Verify Docker services are running (`docker compose -f docker/docker-compose.yml ps`)
2. [ ] Create a backup of current compose files and Dockerfile
3. [ ] For FINDING-003B: check if `mkobi_app` role exists in PostgreSQL (`psql -U postgres -c "\du mkobi_app"`)
4. [ ] For Phase 1: ensure production `.env` or CI/CD secrets are configured BEFORE applying enforcement
5. [ ] For FINDING-004: verify advisory lock mechanism in `DatabaseStarter` works correctly
6. [ ] For FINDING-007: test rebuilt prod image before deployment

### Post-Execution Verification

After applying fixes:
1. [ ] `docker compose -f docker/docker-compose.yml config` — validate compose file syntax
2. [ ] `docker compose -f docker/docker-compose.yml up -d` — verify services start
3. [ ] `curl http://localhost:8000/health` — verify health check works
4. [ ] For FINDING-003B: verify app can connect to database (check logs for `DatabaseNotFoundError`)
5. [ ] For FINDING-005: verify `/docs` returns 404 in production mode
6. [ ] For FINDING-001/002/003: verify services fail to start without required env vars

---

## Positive Findings (Preserved from Audit)

The following positive findings from the audit reports are confirmed and should be maintained:

1. Multi-stage build with clear separation
2. Non-root user in all runtime stages
3. No `.env` copied into image
4. No hardcoded secrets in Dockerfile
5. `uv.lock` copied for reproducible installs
6. Docker secrets support via `SecretsFileSource`
7. Least-privilege DB role concept via init script (NOTE: implementation has fragility issues — see FINDING-003B. The init script pattern only runs on first volume creation, causing role to be missing on subsequent starts. The concept is correct but needs application-level role management as a reliable mechanism.)
8. Health check endpoint implemented in app
9. Stale temp file cleanup via `DatabaseStarter`
10. CORS validation in app code
11. Admin credential validation in config
12. Separate migration service pattern
13. Redis persistence via named volume
14. PostgreSQL 16 pinned version
15. Redis 7-alpine pinned version
16. Standalone test compose with isolated services

---

## Document Metadata

- **Created:** 2026-05-25
- **Source Audits:** audit_report_001.md, audit_report_002.md
- **Validation Method:** Direct source code inspection against all findings
- **Next Review:** After all Phase 1 findings are applied
