# Phase 05 Audit Findings — Infrastructure & Runtime Environment

**Executor:** audit-executor
**Template:** `.ai/audit/templates/audit-findings.md`
**Status:** complete
**Validated:** no

---

## Findings

### INF-001: Missing explicit network definition in production docker-compose.yml

| Field | Value |
|-------|-------|
| **ID** | INF-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/docker-compose.yml` |
| **Classification** | advisory |

**Description:** The production docker-compose.yml does not define an explicit network section. Services rely on Docker's default bridge network instead of a named, explicitly configured network. This reduces operational control over service-to-service communication and makes it harder to implement network segmentation policies for production deployments.

**Evidence:** File `docker/docker-compose.yml` lines 1-184 define 5 services (db, migrate, app, redis, rq-worker, nginx) but no `networks:` section. The test compose file properly defines `test_network: driver: bridge` at lines 122-124 of `docker-compose.test.yml`, but the production compose file lacks this configuration.

**Recommendation:** Add explicit network definition to `docker/docker-compose.yml`:
```yaml
networks:
  app_network:
    driver: bridge
```
And add `networks: [app_network]` to each service that requires network access.

---

### INF-002: Floating version specifiers in frontend package.json

| Field | Value |
|-------|-------|
| **ID** | INF-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/package.json` |
| **Classification** | advisory |

**Description:** The frontend package.json uses caret (`^`) version specifiers for all dependencies, which are floating versions that resolve to any compatible semver version. This violates the reproducibility principle that "dependencies should be pinned to specific versions" for deterministic builds, although this is mitigated by the committed package-lock.json.

**Evidence:** File `frontend/package.json` uses caret versions throughout:
- Line 15: `"@emotion/react": "^11.14.0"`
- Line 26: `"react": "^19.2.5"`
- Line 45: `"vite": "^8.0.10"`
- All 24 dependencies use `^` prefix instead of exact versions

**Recommendation:** For stricter reproducibility, use exact versions in package.json or implement a lockfile verification step in CI/CD to ensure package-lock.json is always in sync and used for production builds.

---

### INF-005: Development secrets in docker/.env template file

| Field | Value |
|-------|-------|
| **ID** | INF-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/.env` |
| **Classification** | advisory |

**Description:** The `docker/.env` file contains hardcoded placeholder values for sensitive credentials including `DATABASE__PASSWORD=1234` (line 11), `JWT__SECRET_KEY=dev-secret-key-for-local-development` (line 19), and `ADMIN_PASSWORD=admin@example.com` (line 52). While `.env` is in `.gitignore` (line 151), the file could inadvertently be used in production if copied without modification.

**Evidence:** File `docker/.env` lines 11, 19, 21, 49, 52 show:
```
DATABASE__PASSWORD=1234
JWT__SECRET_KEY=dev-secret-key-for-local-development
ADMIN_PASSWORD=admin@example.com
```

**Recommendation:** Rename `docker/.env` to `docker/.env.example` to make it clear this is a template, similar to the root `.env.example` file. Update documentation to reference the example file.

---

### INF-006: Frontend node_modules volume without explicit configuration

| Field | Value |
|-------|-------|
| **ID** | INF-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.override.yml` |
| **Classification** | advisory |

**Description:** The frontend development service defines a named volume `frontend_node_modules` (line 33) but the volume is declared without any explicit driver or configuration options. While this works, explicit configuration improves clarity and portability.

**Evidence:** File `docker/docker-compose.override.yml` lines 96-97:
```yaml
volumes:
  frontend_node_modules:
```

**Recommendation:** Consider adding explicit configuration for clarity:
```yaml
volumes:
  frontend_node_modules:
    driver: local
```

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

None - no CRITICAL or HIGH severity mandatory findings identified.

## Advisory Recommendations

- INF-001: Add explicit network definition to production docker-compose.yml
- INF-002: Consider exact version pinning in frontend package.json for stricter reproducibility
- INF-005: Rename docker/.env to docker/.env.example to clarify it is a template
- INF-006: Add explicit driver configuration for frontend_node_modules volume