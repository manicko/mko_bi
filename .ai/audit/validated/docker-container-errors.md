# Docker Container Error Report - Analysis & Recommendations

**Date:** 2026-06-14
**Auditor:** Architecture Audit
**Status:** CRITICAL issues affecting development environment

---

## Executive Summary

After deleting and recreating the `test` and `dev` Docker containers, **3 critical errors** were identified that prevent proper development environment operation:

| Container | Status | Severity | Impact |
|-----------|--------|----------|--------|
| docker-app-1 | Crashed worker | CRITICAL | File logging fails, hot reload worker cannot start |
| docker-frontend-1 | Exited (SIGBUS) | HIGH | Vite dev server crashes, frontend development blocked |
| docker-app-1 | Warning (watchfiles) | LOW | Hot reload exclusion patterns not applied |

**Key Finding:** The test environment works correctly because it uses `tail -f /dev/null` as the entrypoint and doesn't attempt file logging at runtime. The production service works because tmpfs mounts are properly configured. Only the development override lacks proper tmpfs configuration for writable paths.

---

## Error 1: dev-app Permission Error (CRITICAL)

### Problem Description

```
PermissionError: [Errno 13] Permission denied: '/app/data/logs/app.log'
```

The development app container crashes when the uvicorn hot reload worker (SpawnProcess) attempts to initialize file logging. The error occurs during `logging.config.dictConfig()` at application startup.

### Deep Root Cause Analysis

#### 1. Permission Architecture Mismatch

**Production Configuration (docker-compose.yml:112-120):**
- Uses `read_only: true` with `tmpfs` mounts for writable paths
- tmpfs mounts are created by Docker at runtime with correct ownership
- No persistent volume mount for `/app/data`

**Development Override (docker-compose.override.yml):**
- **Missing** `read_only: true` configuration
- **Missing** `tmpfs` mounts for `/app/data/logs`
- Mounts source code as volumes (`../src:/app/src`) but this doesn't affect `/app/data`
- Inherits `LOGGING__LOG_FILE` from base compose without override

#### 2. Volume State Persistence Issue

When the `app_data` volume was created previously:
1. Docker creates anonymous volumes with root:root ownership by default
2. The `chown -R app:app /app/data` in Dockerfile (line 116) runs at **build time**, not runtime
3. At **runtime**, the `app_data` volume is mounted with existing ownership
4. The `app` user (uid 1000) cannot write to `/app/data/logs/app.log`

**Critical architectural flaw:** Development override inherits production volume mount but lacks the security-hardened tmpfs configuration that makes production work.

#### 3. Why This Affects Hot Reload Workers Specifically

The error occurs in `multiprocessing/process.py` → `uvicorn/_subprocess.py`. Uvicorn's hot reload spawns worker processes:
1. Main process starts, inherits `/app/data` volume permissions
2. SpawnProcess creates child process for hot reload
3. Child process attempts to configure logging (file handler initialization)
4. Permission denied on file creation → worker crash
5. Application appears "running" but reload functionality is broken

### Recommended Fix

Disable file logging in development — aligns with 12-factor principles and eliminates permission issues entirely.

```yaml
# docker-compose.override.yml
services:
  app:
    environment:
      LOGGING__LOG_FILE: ""
```

---

## Error 2: dev-frontend SIGBUS Crash (HIGH)

### Problem Description

```
npm error signal SIGBUS
npm error command sh -c vite --host 0.0.0.0
```

The frontend development container crashes with SIGBUS (bus error), indicating invalid memory access during Vite startup.

### Deep Root Cause Analysis

#### 1. Insufficient Diagnostic Data

Current evidence is limited to the npm error message alone. SIGBUS in Node.js/Vite can stem from multiple sources:

| Possible Cause | Evidence Required |
|---------------|-----------------|
| Corrupted Vite cache | Full stack trace, cache inspection |
| Memory exhaustion | `docker stats frontend`, host memory |
| Windows Docker Desktop volume mount | WSL2 backend status, volume consistency |
| Vite package incompatibility | npm install clean, version check |

**Note:** Diagnosis requires full stack trace (`docker logs docker-frontend-1`).

#### 2. Windows Docker Desktop Volume Mount Issues

Current configuration (docker-compose.override.yml:31-36):
```yaml
volumes:
  - ../frontend:/app          # Windows path -> Linux mount point
  - frontend_node_modules:/app/node_modules
```

Potential Windows-specific issues:
1. `../frontend:/app` mounts Windows directory to Linux container
2. Cross-OS file system semantics differences (NTFS vs ext4)
3. Docker Desktop's gRPC FUSE or SMB sharing limitations

---

## Error 3: watchfiles Missing Warning (LOW)

### Problem Description

```
WARNING: --reload-include and --reload-exclude have no effect unless watchfiles is installed.
```

The `--reload-exclude` flag in docker-compose.override.yml:79 requires the `watchfiles` package for optimal hot reload performance. Without it, uvicorn falls back to `StatReload`.

### Recommended Fix

Add `watchfiles` to dev dependencies:

```bash
uv add --group dev watchfiles
```

---

## Concrete Recommendations

### Priority 1: Fix File Logging Permission Error (CRITICAL)

```yaml
# docker-compose.override.yml
services:
  app:
    environment:
      LOGGING__LOG_FILE: ""
```

### Priority 2: Fix Frontend SIGBUS (HIGH)

Make frontend opt-in via profiles, run `npm run dev` on host:

```yaml
# docker-compose.override.yml
services:
  frontend:
    profiles: ["frontend"]
```

### Priority 3: Add watchfiles (LOW)

```bash
uv add --group dev watchfiles
```

---

## Files Requiring Changes

| File | Change | Priority |
|------|--------|----------|
| docker-compose.override.yml | Add `LOGGING__LOG_FILE: ""` | CRITICAL |
| docker-compose.override.yml | Add `profiles: ["frontend"]` | HIGH |
| pyproject.toml | Add `watchfiles` to dev dependencies | LOW |
| docker.md | Document host-based frontend workflow | MEDIUM |

---

## Investigation Required Before Fixing Frontend

```bash
docker logs docker-frontend-1 2>&1 | head -100
docker stats --no-stream docker-frontend-1
docker compose -f docker/docker-compose.yml down -v
```

---

## Cross-References

- [Docker Guide](../../docs/11-guides/docker.md)
- [Deployment Guide](../../docs/10-deployment/deployment.md)
- [Security Overview](../../docs/08-security/security-overview.md)