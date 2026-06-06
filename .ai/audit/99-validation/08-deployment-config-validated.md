# Phase 08 Validation Report — Configuration & Lifecycle

**Validator:** validator-agent
**Source:** .ai/audit/08-deployment-config/findings.md
**Validation Date:** 2026-06-06

---

## Rejected Findings

### DC-003: REJECTED — Conflicts with Documented API Contract

| Field | Value |
|-------|-------|
| **Original ID** | DC-003 |
| **Original Type** | SPEC-DEVIATION |
| **Original Classification** | mandatory |

**Rejection Reason:** This finding conflicts with the documented API specification in `docs/05-health/health-api.md`. Lines 77-78 explicitly state:

> **Path** | `/health/detailed`
> **Auth level** | Public (no authentication required)

Additionally, line 182 documents the intended use:

> **Admin dashboards:** Use `/health/detailed` for a component-level status overview

The health-api.md documentation designates `/health/detailed` as PUBLIC with no authentication, and SPEC.md (via the health-api cross-reference) supports this. Unlike `/docs` and `/redoc` which are specifically documented as disabled in production, `/health/detailed` is documented as a public monitoring endpoint. The code correctly implements the documented specification.

**Cross-phase conflict:** SEC-005 (Phase 04 Security) also identifies this as an issue, but recommends authentication for `/health/detailed` without acknowledging the documented public API contract. Recommendation: SEC-005 should also be rejected for the same reason — the current behavior matches documented spec.

This finding should be either: (1) reclassified as a DOC-UPDATE to change the documented auth level, or (2) the documentation should be updated to reflect that the security concern is intentional design for monitoring integrations.

---

## Validated Findings (No Changes)

| ID | Type | Classification | Status |
|----|------|----------------|--------|
| DC-001 | SPEC-DEVIATION | mandatory | VALIDATED |
| DC-002 | SPEC-DEVIATION | mandatory | VALIDATED |
| DC-004 | BEST-PRACTICE | advisory | VALIDATED |
| DC-005 | BEST-PRACTICE | advisory | VALIDATED |
| DC-006 | BEST-PRACTICE | advisory | VALIDATED |
| DC-007 | BEST-PRACTICE | advisory | VALIDATED |

**Validation Notes:**

- **DC-001**: Port 8000 is exposed unconditionally in `docker-compose.yml` line 104. The `docker-compose.override.yml` does not override the `ports` directive for the `app` service, so the port remains exposed in production mode, allowing bypass of the nginx security layer. This violates the documented deployment architecture where nginx is the entry point in production. Valid SPEC-DEVIATION.

- **DC-002**: `ALTER ROLE mkobi_app CREATEDB` is present in `docker/init-scripts/01-create-app-role.sh` line 28. The `recreate_test_database()` function in `starter.py` uses `admin_url` (postgres superuser) for database creation operations. The documentation in `deployment.md` lines 207-209 specifies mkobi_app should have only `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on tables and `USAGE` on sequences. Valid SPEC-DEVIATION with confirmed code evidence.

- **DC-004**: Password interpolation in SQL string literal without escaping. While the typical password generation pattern (`openssl rand -hex 32`) produces safe values, dollar-quoting would be PostgreSQL best practice. Valid BEST-PRACTICE advisory.

- **DC-005**: No URL format validation for CORS origins despite production validation for empty/wildcard. Valid BEST-PRACTICE advisory.

- **DC-006**: nginx.conf listens only on port 80 and includes HSTS header which is ineffective over HTTP. Valid BEST-PRACTICE advisory.

- **DC-007**: No `client_max_body_size` in nginx config while backend allows 100MB uploads. Valid BEST-PRACTICE advisory.

---

## Cross-Phase Conflicts

### Conflict: DC-003 and SEC-005 Both Flag /health/detailed Authentication

| Field | Value |
|-------|-------|
| **Conflicting IDs** | DC-003, SEC-005 |
| **Conflict Type** | SPEC-CONFLICT |
| **Resolution Required** | REJECT BOTH or DOCUMENT CHANGE |

**Analysis:** Both findings identify the same issue (unauthenticated `/health/detailed`) but:

1. **DC-003** (Phase 08) claims this is a SPEC-DEVIATION because `/docs` and `/redoc` are disabled in production but `/health/detailed` is not.

2. **SEC-005** (Phase 04) classifies this as BEST-PRACTICE advisory, recommending admin authentication.

However, `docs/05-health/health-api.md` line 78 explicitly documents:

> **Auth level** | Public (no authentication required)

The current behavior matches the documented specification. If authentication is desired for `/health/detailed`, the documentation must be updated first, then the code can be changed. Both findings should be rejected until the specification is clarified.

**Recommended Resolution Options:**

1. **Keep as-is (recommended)**: The endpoint is intentionally public for monitoring integrations. Both findings remain REJECTED.

2. **Change specification**: Update `docs/05-health/health-api.md` to require authentication, change both findings to mandatory.

---

## Rollout Safety Issues

### Dependency Between DC-001 and DC-007

| Field | Value |
|-------|-------|
| **Related IDs** | DC-001, DC-007 |
| **Issue Type** | Ordering Dependency |

**Analysis:** Both findings affect the nginx reverse proxy in production:

- **DC-001** (port exposure) affects the `app` service definition and requires modifying `docker-compose.yml`
- **DC-007** (client_max_body_size) affects `nginx.conf`

If both changes are implemented, they should be deployed together to avoid partial fix scenarios (e.g., removing port exposure but nginx still blocks large uploads). Changes are in separate files with separate deployment steps, but operational coordination is recommended.

---

## Summary

| Category | Count |
|----------|-------|
| Rejected | 1 (DC-003 - conflicts with documented API contract) |
| Validated (No Change) | 6 |
| Mandatory Fixes | 2 (DC-001, DC-002) |
| Advisory Recommendations | 4 (DC-004, DC-005, DC-006, DC-007) |

**Note:** DC-003 and SEC-005 represent a spec-design tension rather than actionable code changes. The documented public health endpoint is by design; adding authentication would require updating the health-api.md documentation to reflect the change.