# Security Audit Findings (Phase 04)

## Critical Issues

### [CRITICAL-01] Missing Dashboard Access Control in Processing Config Endpoints
**Location:** `src/mkobi/api/routes/processing_configs.py`, lines 35-56, 65-94, 97-120
**Severity:** CRITICAL

**Issue:** The processing config endpoints (`GET /{dashboard_id}`, `PUT /{dashboard_id}`, `DELETE /{dashboard_id}`) enforce role-level access (viewer/editor) but **do not verify dashboard-level access**. This allows any authenticated user with `require_viewer_role` to access processing configurations for any dashboard by ID, bypassing resource-level access controls.

**Evidence:**
- Lines 33-34: `dependencies=[Depends(require_viewer_role)]` - only checks user role, not dashboard ownership
- Lines 63-64: `dependencies=[Depends(require_editor_role)]` - same issue
- Lines 100-101: `dependencies=[Depends(require_editor_role)]` - same issue
- No call to `check_dashboard_access` in any of these endpoints

**Impact:** Any authenticated user can read, modify, or delete processing configurations for dashboards they don't own, leading to unauthorized data processing configuration manipulation.

---

### [CRITICAL-02] Missing Dashboard Access Control in Processing Log Endpoints (Admin Route)
**Location:** `src/mkobi/api/routes/processing_logs.py`, lines 32-69, 97-128
**Severity:** HIGH (downgraded from CRITICAL - admin-only access limits scope)

**Issue:** While marked as "admin only", the processing log endpoints allow filtering by any `dashboard_id` without verifying the requesting admin has access to that dashboard. If role-based admin access expands in the future, this could expose logs to unauthorized users.

**Evidence:**
- Lines 66-68: `_current_user: UserRead = Depends(require_admin_role)` - only checks system admin role
- No dashboard ownership verification for the filtered logs

**Impact:** Admin users can view processing logs for any dashboard regardless of their dashboard-level permissions. Future changes to admin scope could expose sensitive processing data.

---

## High Severity Issues

### [HIGH-01] Weak JWT Secret Key in Development Environment
**Location:** `.env`, line 15
**Severity:** HIGH

**Issue:** Development JWT secret key is hardcoded and predictable: `dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`. While the comment warns against production use, the key pattern is documented in source code and could be used in production by mistake.

**Evidence:**
```
JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars
```

**Impact:** If deployed to production, JWT tokens can be forged allowing complete authentication bypass.

---

### [HIGH-02] Predictable Admin Credentials in Configuration
**Location:** `.env`, lines 18-19
**Severity:** HIGH

**Issue:** Default admin credentials use email format that could be easily guessed: `admin@example.com` / `admin@example.com`

**Evidence:**
```
ADMIN_USERNAME=admin@example.com
ADMIN_PASSWORD=admin@example.com
```

**Impact:** Default admin password matches username, enabling easy unauthorized admin access if not changed.

---

## Medium Severity Issues

### [MEDIUM-01] Secrets Not Leveraging Docker Secrets File Pattern (_FILE Support)
**Location:** `docker-compose.yml` (lines 21-23, 67, 96, 70, 171)
**Severity:** MEDIUM

**Issue:** Docker Compose configuration expects secrets via environment variables but does not demonstrate or enable `_FILE` suffix support (Docker secrets pattern). While `SecretsFileSource` exists in `config.py`, the deployment configuration doesn't facilitate its use.

**Evidence:**
- `docker-compose.yml` uses `${JWT__SECRET_KEY:?JWT__SECRET_KEY is required}` without demonstrating `_FILE` alternative
- No secrets mounts configured in docker-compose.yml

**Impact:** Secrets must be passed via environment variables, increasing risk of accidental exposure through process listings, logs, or debug endpoints.

---

### [MEDIUM-02] Temp Password Retrieval Token Exposed in Response Body
**Location:** `src/mkobi/api/routes/admin.py`, lines 327-330
**Severity:** MEDIUM

**Issue:** The `retrieve_temp_password_admin_endpoint` returns the retrieval token in the response body after approving a registration request. While this is admin-only, it creates unnecessary audit trail exposure.

**Evidence:**
```python
return {
    "message": "Registration request approved",
    "user_id": str(user.id),
    "retrieval_token": retrieval_token,
}
```

**Impact:** Registration approval responses contain sensitive credential recovery tokens.

---

### [MEDIUM-03] File Upload - Rate Limiter Instantiated Per-Request Without Caching
**Location:** `src/mkobi/api/routes/upload.py`, lines 123-139
**Severity:** MEDIUM

**Issue:** Rate limiter is instantiated fresh on every request. While functional, this creates unnecessary overhead and could cause issues under high load.

**Evidence:**
```python
rate_limiter = AsyncRateLimiter(
    redis_client.get_async_redis_client(),
    fail_closed=config.rate_limiter_fail_closed,
)
```

**Impact:** Potential performance degradation and inconsistent rate limiting behavior under load.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 3 |
| Medium | 3 |

**Total Issues: 7**

The most critical issue is the missing resource-level access control in processing config endpoints, where role-based authentication is present but dashboard ownership verification is absent.