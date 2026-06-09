# Phase 04 Audit Findings — Security

**Executor:** audit-executor  
**Template:** .ai/audit/templates/audit-findings.md  
**Status:** complete  
**Validated:** no  

---

## Findings

### SEC-001: Registration Request Endpoint Missing Rate Limiter Dependency Injection

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/auth.py |
| **Classification** | mandatory |

**Description:** The `/auth/register-request` endpoint applies rate limiting but accesses the Redis client directly via `redis_client.get_async_redis_client()` instead of using the injected `get_redis_client_dependency()` pattern. This creates inconsistency with other endpoints and may cause issues with Redis connection management in multi-worker deployments. The rate limit key construction also has a potential edge case (line 542) where if both `client_ip` and `request_data.email` are None/falsy, the key could be malformed.

**Evidence:** `src/mkobi/api/routes/auth.py` lines 537-553 show rate limiting logic that:
1. Uses `redis_client.get_async_redis_client()` directly instead of dependency injection
2. Has conditional key construction: `f"register-request:{client_ip}" if client_ip else f"register-request:{request_data.email}"` - if both are None/empty, this could create issues

**Recommendation:** Refactor to use `redis_client: Any = Depends(get_redis_client_dependency)` consistently with other endpoints. Add validation for key construction edge cases.

---

### SEC-002: Processing Config Endpoints Lack Dashboard IDOR Protection

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/processing_configs.py |
| **Classification** | mandatory |

**Description:** The processing configs endpoints (`GET /{dashboard_id}`, `PUT /{dashboard_id}`, `DELETE /{dashboard_id}`) apply `require_viewer_role` and `require_editor_role` dependencies but do NOT verify that the requesting user has access to the specific dashboard identified in the path parameter. This is an IDOR (Insecure Direct Object Reference) vulnerability - any authenticated viewer can read processing configurations for any dashboard, and any authenticated editor can modify/delete configurations for any dashboard.

**Evidence:** `src/mkobi/api/routes/processing_configs.py` shows:
- GET (lines 33-56): Uses `require_viewer_role` but never calls `check_dashboard_access`
- PUT (lines 63-94): Uses `require_editor_role` but never calls `check_dashboard_access`  
- DELETE (lines 97-120): Uses `require_editor_role` but never calls `check_dashboard_access`

In contrast, `src/mkobi/api/routes/dashboards_crud.py` lines 326-341 properly check dashboard access before updates.

**Recommendation:** Add dashboard access verification using `require_dashboard_read_access` for GET and `require_dashboard_write_access` for PUT/DELETE endpoints, similar to how other dashboard-scoped resources are protected in `dashboards_crud.py` and `graphs.py`.

---

### SEC-003: Temp Password Retrieval Lacks Audit Trail

| Field | Value |
|-------|-------|
| **ID** | SEC-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/api/routes/admin.py |
| **Classification** | mandatory |

**Description:** The temp password retrieval endpoint (`/admin/temp-passwords/{retrieval_token}`) returns passwords in plaintext but does not log which admin retrieved them. The current implementation deletes passwords after retrieval (one-time use) but lacks audit logging for security monitoring and compliance purposes.

**Evidence:** `src/mkobi/api/routes/admin.py` lines 397-415 show the temp password retrieval endpoint. While it requires admin role, it only logs the first 8 characters of the token (`token[:8]`) without recording which admin performed the retrieval.

**Recommendation:** Add audit logging for temp password retrieval including the admin user ID, retrieval token (partial), timestamp, and target user ID for security monitoring.

---

### SEC-004: .env File Contains Actual Development Credentials

| Field | Value |
|-------|-------|
| **ID** | SEC-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | .env |
| **Classification** | advisory |

**Description:** The `.env` file in the repository root contains actual credential values (not placeholders) for development including `DATABASE__PASSWORD=postgres`, `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`, and `ADMIN_PASSWORD=admin@example.com`. While marked as development, these are real credentials that could be accidentally used in production.

**Evidence:** `.env` lines 10, 15, 19 show actual credentials that are functional values, not placeholder templates.

**Recommendation:** Rename `.env` to `.env.example` or use only placeholder values like `CHANGE_ME` in committed configuration files. Ensure real `.env` files are in `.gitignore`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 0 |

## Mandatory Fixes

1. SEC-001: Registration request endpoint rate limiting needs dependency injection refactor
2. SEC-002: Processing configs endpoints missing dashboard IDOR protection

## Advisory Recommendations

1. SEC-003: Temp password retrieval lacks audit trail
2. SEC-004: Environment file contains real credentials that could be misused