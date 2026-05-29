---
name: 05-docker
description: Infrastructure audit covering reproducibility, secrets management, isolation, resilience, and deployment safety
agent: audit-executor
alwaysApply: false
---

# Phase 05 Audit — Infrastructure & Runtime Environment

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's infrastructure architecture:

1. **Container Discovery**
   - Identify container definition files and their purposes
   - Map service separation and responsibilities
   - Discover volume/mount configurations
   - Locate health check configurations

2. **Build Discovery**
   - Identify multi-stage build strategy
   - Map dependency management approach
   - Discover artifact optimizations (slim vs full images)
   - Find build caching strategies

3. **Secrets Discovery**
   - Identify secret injection mechanisms
   - Map configuration priority (env > secrets > files > defaults)
   - Discover secrets never baked into images
   - Find production vs development configuration differences

4. **Runtime Discovery**
   - Identify restart policies and failure handling
   - Map service dependencies and startup order
   - Discover resource limits and constraints
   - Find backup/restore procedures

---

## Audit Dimensions

### 1. Reproducibility

Verify builds and deployments are deterministic:

| Check | Status | Evidence |
|-------|--------|----------|
| Base images use pinned versions (no `latest`) | | |
| Dependencies pinned to specific versions | | |
| Build produces reproducible artifacts | | |
| Configuration files version-controlled | | |
| No manual steps required for deployment | | |

---

### 2. Secrets Management

Verify sensitive data isolation:

| Check | Status | Evidence |
|-------|--------|----------|
| Secrets injected via environment/files, not hardcoded | | |
| No secrets baked into container images | | |
| Secret injection supports multiple sources (.env, _FILE, etc.) | | |
| Production credentials enforced at startup | | |
| Development credentials not used in production | | |

---

### 3. Isolation

Verify environment and service isolation:

| Check | Status | Evidence |
|-------|--------|----------|
| Development environment isolated from production | | |
| Test environment uses separate database | | |
| Service-to-service communication via defined network | | |
| No unnecessary port exposure | | |
| File system isolation (volumes for data only) | | |

---

### 4. Resilience

Verify failure handling and recovery:

| Check | Status | Evidence |
|-------|--------|----------|
| Health checks verify service liveness | | |
| Health check intervals appropriate | | |
| Services restart on failure | | |
| Graceful shutdown implemented | | |
| Resource cleanup on startup (stale files) | | |
| Error handling prevents cascade failures | | |

---

### 5. Container Security

Verify container isolation and user privileges:

| Check | Status | Evidence |
|-------|--------|----------|
| Containers run as non-root user | | |
| No unnecessary system packages in production images | | |
| Multi-stage builds separate build from runtime | | |
| Development dependencies excluded from production | | |

---

### 6. Deployment Safety

Verify production readiness:

| Check | Status | Evidence |
|-------|--------|----------|
| Debug mode disabled in production | | |
| Logging level appropriate for production | | |
| Production refuses insecure defaults | | |
| Migration strategy defined and tested | | |
| Rollback procedure documented | | |

---

## Report Output

Write findings to: `.ai/audit/05-infrastructure/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `INF-` for finding IDs.