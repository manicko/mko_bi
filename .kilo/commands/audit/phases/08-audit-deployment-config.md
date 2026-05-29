---
name: 08-deployment-config
description: Configuration and startup audit covering config management, lifecycle, and production readiness
agent: audit-executor
alwaysApply: false
---

# Phase 08 Audit — Configuration & Lifecycle

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's configuration architecture:

1. **Configuration Discovery**
   - Identify configuration sources (env, files, secrets)
   - Map configuration priority order
   - Discover configuration validation strategy
   - Find production vs development configuration differences

2. **Startup Discovery**
   - Identify application entry point
   - Map startup sequence and dependencies
   - Discover health check endpoints and readiness
   - Find initialization tasks (DB, migrations, admin user)

3. **Shutdown Discovery**
   - Identify graceful shutdown handling
   - Map resource cleanup on shutdown
   - Discover connection pool disposal
   - Find background task termination

4. **Environment Discovery**
   - Identify environment detection mechanism
   - Map environment-specific behavior
   - Discover production safety checks
   - Find test environment isolation

---

## Audit Dimensions

### 1. Configuration Management

Verify configuration is robust and secure:

| Check | Status | Evidence |
|-------|--------|----------|
| Configuration centralized in single module | | |
| Secrets derived from environment variables | | |
| Secret injection supports multiple sources | | |
| Production refuses insecure defaults | | |
| Configuration validated at startup | | |
| No hardcoded values in configuration | | |

---

### 2. Startup Lifecycle

Verify application starts correctly:

| Check | Status | Evidence |
|-------|--------|----------|
| Dependency check on startup (imports succeed) | | |
| Database connectivity verified before accepting requests | | |
| Schema existence verified on startup | | |
| Migrations run automatically when configured | | |
| Admin user creation is idempotent | | |
| Stale temp files cleaned on startup | | |
| Test database recreated when configured | | |

---

### 3. Production Readiness

Verify production deployment is safe:

| Check | Status | Evidence |
|-------|--------|----------|
| Production debug mode disabled | | |
| Logging level appropriate for production | | |
| Production credentials enforced | | |
| CORS origins validated in production | | |
| No development features in production mode | | |

---

### 4. Overengineering Check

Verify simplicity is maintained:

| Check | Status | Evidence |
|-------|--------|----------|
| No unnecessary abstraction layers | | |
| Configuration matches project complexity | | |
| No duplicated configuration patterns | | |
| Libraries used have clear justification | | |

---

## Report Output

Write findings to: `.ai/audit/08-deployment-config/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `DC-` for finding IDs.