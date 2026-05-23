# Validated Audit Findings — Cookie-Based Refresh Token Flow (PLAN_01)

**Date:** 2026-05-23
**Source Audit:** `.ai/audit/problems/implementation_audit_001.md`
**Scope:** Tasks 022–041 (PLAN_01, Waves 1–5) — Cookie-based refresh token implementation
**Validator:** validator agent

---

## Validation Summary

| Category | Count |
|----------|-------|
| Total findings in source audit | 10 |
| Validated (confirmed) | 5 |
| Rejected (already resolved / stale) | 0 |
| Merged (overlapping) | 0 |
| Downgraded (lower severity) | 0 |
| Upgraded (higher severity) | 0 |
| Informational (no action needed) | 5 |

**Overall verdict:** All 5 actionable findings are **VALIDATED** — confirmed against source code. 5 informational notes require no code changes.

---

## Validated Findings

---

### VF-001: Token Payload Key Mismatch in Refresh Endpoint

- **Finding ID:** VF-001
- **Original Severity:** Critical
- **Validated Severity:** Critical
- **Status:** VALIDATED — CONFIRMED BUG
- **Title:** Refresh endpoint creates access token with `"sub"` instead of `"user_id"`
- **Description:**
  The refresh endpoint at `src/mkobi/api/routes/auth.py:307-308` creates a new access token using `"sub"` as the user identifier key:
  ```python
  access_token = create_access_token(
      data={"sub": str(user.id), "email": user.email, "role": user.role}
  )
  ```
  However, `get_current_user_dependency` in `src/mkobi/api/deps.py:429` reads `payload.get("user_id")`:
  ```python
  user_id_raw = payload.get("user_id")
  ```
  The login endpoint correctly uses `"user_id"` (via `auth_service.py:198-201`).

- **Impact:** All access tokens issued by the refresh endpoint will fail subsequent authentication. After a token refresh, the new access token payload contains `sub` but not `user_id`. Any subsequent API call will fail with HTTP 401 "Token missing user_id". This is a **blocking production bug**.

- **Root Cause:** Copy-paste error — the refresh endpoint used the JWT standard `"sub"` claim name instead of the project's established `"user_id"` key used everywhere else.

- **Affected Modules:**
  - `src/mkobi/api/routes/auth.py` (line 307-308) — the bug
  - `src/mkobi/api/deps.py` (line 429) — the consumer expecting `"user_id"`
  - `src/mkobi/services/auth_service.py` (line 198-201) — correct implementation for reference

- **Affected Symbols:**
  - `create_access_token()` call in `auth.py:307`
  - `get_current_user_dependency()` in `deps.py:429`

- **Dependency Notes:** No dependency conflicts. This is a standalone one-line fix.

- **Rollout Considerations:** Must be fixed before production rollout. No migration needed. The fix is a single key name change in a dict literal.

- **Validation Notes:** Confirmed by reading source code at all three locations. The bug is real and will cause 401 errors on every request after a token refresh. Existing tests (`test_auth.py:test_refresh_valid_token`, `test_auth_api.py:test_refresh_reads_from_cookie`) do not catch this because they only check the refresh response, not subsequent authenticated requests with the refreshed token.

- **Required Fix:** Change `auth.py:308` from `{"sub": str(user.id), ...}` to `{"user_id": str(user.id), ...}`.

---

### VF-002: Inconsistent Cookie Setting Pattern in Login Endpoint

- **Finding ID:** VF-002
- **Original Severity:** Major
- **Validated Severity:** Major
- **Status:** VALIDATED — CONFIRMED
- **Title:** Login endpoint sets cookie inline instead of using `set_secure_cookie()` utility
- **Description:**
  The `_handle_login` function at `src/mkobi/api/routes/auth.py:99-106` sets the refresh token cookie directly via `response.set_cookie()` with inline security constants:
  ```python
  response.set_cookie(
      key=COOKIE_NAME,
      value=refresh_token,
      httponly=COOKIE_HTTPONLY,
      secure=COOKIE_SECURE,
      samesite=COOKIE_SAMESITE,
      max_age=get_config().jwt.refresh_token_expire_minutes * 60,
  )
  ```
  Meanwhile, the logout endpoint correctly uses the `delete_secure_cookie()` utility. The `set_secure_cookie()` function exists in `security.py:381-404` but is not imported in `auth.py`.

- **Impact:** Inconsistency. If cookie security defaults change, the login endpoint must be updated separately. Currently functionally correct but violates DRY. The `set_secure_cookie` utility function exists but is unused anywhere in the codebase.

- **Root Cause:** The `set_secure_cookie()` utility was created (TASK_030) but the login endpoint was not updated to use it. The import block in `auth.py:31-41` imports `delete_secure_cookie` but not `set_secure_cookie`.

- **Affected Modules:**
  - `src/mkobi/api/routes/auth.py` (lines 31-41 for imports, 99-106 for inline cookie)
  - `src/mkobi/core/security.py` (lines 381-404 for unused utility)

- **Affected Symbols:**
  - `_handle_login()` in `auth.py`
  - `set_secure_cookie()` in `security.py` (defined but unused)

- **Dependency Notes:** No dependency conflicts. This is a self-contained refactoring.

- **Rollout Considerations:** Low risk. Purely a code quality improvement. The functional behavior remains identical since the same constants are used.

- **Validation Notes:** Confirmed by reading the import block at `auth.py:31-41` (only `delete_secure_cookie` imported, not `set_secure_cookie`) and the inline `response.set_cookie()` call at `auth.py:99-106`. The `set_secure_cookie` function at `security.py:381-404` is confirmed to exist and produce equivalent output.

- **Required Fix:** Import `set_secure_cookie` in `auth.py` and use it in `_handle_login` instead of inline `response.set_cookie()`.

---

### VF-003: Duplicate Test Coverage for Cookie Setting on Login

- **Finding ID:** VF-003
- **Original Severity:** Major (test quality)
- **Validated Severity:** Major (test quality)
- **Status:** VALIDATED — CONFIRMED
- **Title:** Near-identical tests verify login cookie behavior in two test files
- **Description:**
  `test_auth.py:63-88` (`TestLogin.test_login_sets_refresh_token_cookie`) and `test_auth_api.py:35-60` (`TestCookieAuthFlow.test_login_sets_refresh_cookie`) are near-identical tests verifying the same functionality. Both check that login sets the `mkobi_refresh_token` cookie with httponly, secure, and samesite attributes.

- **Impact:** Maintenance burden. If the cookie behavior changes, both tests must be updated. Violates DRY principle for test code.

- **Root Cause:** Tests were written in different phases — `test_auth.py` for basic auth tests, `test_auth_api.py` for dedicated cookie auth flow tests — without deduplication.

- **Affected Modules:**
  - `tests/test_auth.py` (line 63-88)
  - `tests/test_auth_api.py` (line 35-60)

- **Affected Symbols:**
  - `TestLogin.test_login_sets_refresh_token_cookie` in `test_auth.py`
  - `TestCookieAuthFlow.test_login_sets_refresh_cookie` in `test_auth_api.py`

- **Dependency Notes:** No dependency conflicts. Removing one test does not affect any production code.

- **Rollout Considerations:** Zero risk. Test-only change.

- **Validation Notes:** Confirmed by grep — both test methods exist at the specified locations. The `test_auth_api.py` version is preferred for retention since it's part of the dedicated cookie auth flow test suite.

- **Required Fix:** Remove the duplicate from `test_auth.py:63-88` and keep the one in `test_auth_api.py:35-60`.

---

### VF-004: Redundant `removeToken()` Call in `useAuth.logout`

- **Finding ID:** VF-004
- **Original Severity:** Minor
- **Validated Severity:** Minor
- **Status:** VALIDATED — CONFIRMED
- **Title:** `logout()` calls `removeToken()` explicitly before `logoutClient()` which also calls `removeToken()`
- **Description:**
  The `logout` function in `frontend/src/features/auth/model/useAuth.ts:39-48` calls `removeToken()` on line 45, then calls `logoutClient()` on line 46, which internally also calls `removeToken()` (confirmed at `authApi.ts:29-31`):
  ```typescript
  const logout = useCallback(async () => {
      try {
          await apiLogout()
      } catch { /* ... */ }
      removeToken()      // line 45
      logoutClient()     // line 46 — calls removeToken() again internally
      setUser(null)
  }, [])
  ```

- **Impact:** No functional bug (idempotent operation), but unnecessary double-call. Reduces code clarity and could confuse future maintainers.

- **Root Cause:** The `logoutClient()` function was created to encapsulate client-side logout logic (including `removeToken()`), but the explicit `removeToken()` call was not removed from `logout()`.

- **Affected Modules:**
  - `frontend/src/features/auth/model/useAuth.ts` (lines 45-46)
  - `frontend/src/features/auth/api/authApi.ts` (lines 29-31 for `logoutClient`)

- **Affected Symbols:**
  - `logout()` in `useAuth.ts`
  - `logoutClient()` in `authApi.ts`

- **Dependency Notes:** No dependency conflicts.

- **Rollout Considerations:** Zero risk. `removeToken()` is idempotent.

- **Validation Notes:** Confirmed by reading both files. `logoutClient()` at `authApi.ts:29-31` calls `removeToken()`. The explicit call at `useAuth.ts:45` is redundant.

- **Required Fix:** Remove the explicit `removeToken()` call on line 45 of `useAuth.ts`, keep only `logoutClient()` which handles token removal.

---

### VF-005: `COOKIE_SECURE` Hardcoded to `True`

- **Finding ID:** VF-005
- **Original Severity:** Minor (developer experience)
- **Validated Severity:** Minor (developer experience)
- **Status:** VALIDATED — CONFIRMED
- **Title:** `COOKIE_SECURE` is hardcoded with no environment-based override
- **Description:**
  `COOKIE_SECURE: bool = True` is hardcoded at `src/mkobi/core/security.py:47` with no environment-based override. In local development without HTTPS, the browser will refuse to set the cookie, silently breaking the refresh token flow.

- **Impact:** Developers working without HTTPS (local dev without reverse proxy) will experience silent auth failures. No indication in logs. This is a developer experience issue, not a production issue (production should always use HTTPS).

- **Root Cause:** Security constants were defined as module-level constants without considering the development environment use case.

- **Affected Modules:**
  - `src/mkobi/core/security.py` (line 47)

- **Affected Symbols:**
  - `COOKIE_SECURE` constant in `security.py`

- **Dependency Notes:** No dependency conflicts. Would require adding an environment variable and reading it in the constant definition or making it a config-driven value.

- **Rollout Considerations:** Low risk. Should default to `True` for production safety. Only affects development environments without HTTPS.

- **Validation Notes:** Confirmed at `security.py:47`. The constant is used by both `set_secure_cookie()` and `delete_secure_cookie()` utilities, and also by the inline `response.set_cookie()` in the login endpoint.

- **Required Fix:** Consider making `COOKIE_SECURE` configurable via environment variable, defaulting to `True` for production safety but allowing `False` for development. This is optional and can be deferred to a follow-up.

---

## Informational Notes (No Action Required)

---

### INFO-001: `set_secure_cookie` Not Imported in `auth.py`

- **Severity:** Informational
- **Status:** VALIDATED — NO ACTION NEEDED
- **Description:** The import block in `auth.py:31-41` imports `delete_secure_cookie` but not `set_secure_cookie`. The function exists in `security.py` but is unused. This is noted for consistency. Will be resolved if VF-002 is implemented.
- **Affected Modules:** `src/mkobi/api/routes/auth.py`

---

### INFO-002: Frontend `index.ts` Doesn't Export `logout` API Function

- **Severity:** Informational
- **Status:** VALIDATED — NO ACTION NEEDED
- **Description:** The auth feature's barrel export at `frontend/src/features/auth/index.ts:2` exports `logoutClient` but not the async `logout` API function from `authApi.ts`. All consumers import directly from `../api/authApi` instead of from the feature index.
- **Affected Modules:** `frontend/src/features/auth/index.ts`

---

### INFO-003: Circular Import Between `axiosInstance.ts` and `authApi.ts`

- **Severity:** Informational
- **Status:** VALIDATED — NO ACTION NEEDED (ACCEPTABLE PATTERN)
- **Description:** `axiosInstance.ts` imports `refreshToken` from `authApi.ts`, which imports `axiosInstance` from `axiosInstance.ts`. This is a circular ES module dependency. However, the `refreshToken` function is only called inside the response interceptor (at request time, not module load time), so the `axiosInstance` export is already resolved. This is a common and acceptable pattern in axios interceptor setups.
- **Affected Modules:** `frontend/src/shared/api/axiosInstance.ts`, `frontend/src/features/auth/api/authApi.ts`

---

### INFO-004: Missing Test Coverage for Refreshed Token Usage

- **Severity:** Informational (test quality)
- **Status:** VALIDATED — NO ACTION NEEDED (RECOMMENDED ADDITION)
- **Description:** No test verifies that a refreshed access token works for subsequent authenticated requests. This would have caught the critical VF-001 bug. Recommended to add an integration test that: (1) logs in, (2) refreshes the token, (3) uses the refreshed token to make an authenticated API call.
- **Affected Modules:** `tests/test_auth_api.py`

---

### INFO-005: Missing Tests for Cookie Utility Functions

- **Severity:** Informational (test quality)
- **Status:** VALIDATED — NO ACTION NEEDED (RECOMMENDED ADDITION)
- **Description:** No direct unit tests for `set_secure_cookie()` and `delete_secure_cookie()` utility functions. No test for `create_refresh_token` expiration (verifying the 7-day TTL is encoded correctly). No frontend unit tests for `useAuth` hook (silent refresh, logout, loading states).
- **Affected Modules:** `tests/`, `frontend/src/features/auth/model/__tests__/`

---

## Architectural Consistency Assessment

### Clean Architecture Compliance: PASS

The implementation correctly maintains layer boundaries:
- **Route layer** (`auth.py`): Handles HTTP concerns (cookies, request/response)
- **Service layer** (`auth_service.py`): Pure business logic, no cookie/HTTP awareness
- **Core layer** (`security.py`): Reusable security utilities
- **Model layer** (`auth.py` models): Pure Pydantic models

No cross-layer leakage detected. The `AuthService` does not import or reference any cookie-related code.

### Dependency Direction: PASS

Correct: Routes → Services → Repositories. No reverse dependencies detected.

### Semantic Stability: PASS

All semantic anchors used in the implementation are stable:
- Function definitions (`create_access_token`, `decode_token`, `validate_refresh_token`)
- Class definitions (`AuthService`, `JWTSettings`)
- Route definitions (`@router.post`)
- Module-level constants (cookie security constants)

No fragile line-based or pattern-based anchors were used.

---

## Rollout Safety Analysis

### Deployment Safety: LOW RISK (after VF-001 fix)

The changes are additive (new endpoints, new cookie behavior) with minimal modification of existing flows:
- Login endpoint: Added cookie setting to existing flow (backward compatible — old clients ignore cookies)
- Refresh endpoint: Changed from body-based to cookie-based (breaking change for old clients, but old clients would need to be updated anyway)
- Logout endpoint: New endpoint (no existing behavior to break)

### Migration Considerations

1. **Token payload change (VF-001):** After fixing VF-001 and deploying, users with active sessions will need to re-login once. The refresh endpoint previously read from request body; now it reads from cookies. This is a clean break.

2. **Cookie security:** `COOKIE_SECURE=True` requires HTTPS. Ensure the production environment terminates HTTPS before the FastAPI app, or the `X-Forwarded-Proto` header is properly handled.

3. **Access token lifetime reduction:** Changed from 30 to 15 minutes. Users will refresh more frequently. Ensure the refresh flow works correctly before rollout.

### Rollback Feasibility: EASY

All changes are confined to:
- `src/mkobi/config.py` (one field change + one new field)
- `src/mkobi/core/security.py` (new functions + constants)
- `src/mkobi/api/routes/auth.py` (modified login/refresh + new logout)
- `src/mkobi/services/auth_service.py` (new method)
- Frontend files (new API functions, modified interceptors)

No database migrations required.

---

## Execution Applicability

All validated findings are immediately actionable. No dependency ordering required — all fixes are independent and can be applied in any order or in parallel.

| Finding | Effort | Risk | Priority |
|---------|--------|------|----------|
| VF-001 (token key fix) | Trivial (1 line) | None | **BLOCKING** |
| VF-002 (cookie utility) | Trivial (import + replace) | None | Recommended |
| VF-003 (duplicate test) | Trivial (delete test) | None | Recommended |
| VF-004 (redundant call) | Trivial (delete 1 line) | None | Recommended |
| VF-005 (configurable secure) | Small (env var) | Low | Optional |

---

## Final Verdict

**REQUIRES FIXES BEFORE PRODUCTION**

The implementation is architecturally sound and well-structured. One critical bug (VF-001: token payload key mismatch in the refresh endpoint) **must** be fixed before production rollout — it will cause 100% failure rate on authenticated requests after token refresh. Four additional validated findings (VF-002 through VF-005) improve code quality and maintainability. No architectural redesign needed.

All findings were validated against actual source code. No stale, duplicate, or speculative findings were identified in the source audit.
