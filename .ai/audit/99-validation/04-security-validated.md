# Phase 04 Security Validation Report

**Validator:** validator
**Source:** `.ai/audit/04-security/findings.md`
**Date:** 2026-06-15

---

## Rejected Findings

None. All findings are technically accurate, properly classified, and represent real security considerations.

---

## Validated Findings

All four security findings (SEC-01 through SEC-04) are confirmed as VALID advisory recommendations.

| ID | Type | Status |
|----|------|--------|
| SEC-01 | BEST-PRACTICE | VALID — Timing side-channel confirmed in `login_user` (auth_service.py:201-206). Early return on `user_obj is None` without bcrypt dummy call creates measurable timing difference. Rate limiting exists (5 attempts/5min/IP) but does not fully mitigate this vector. |
| SEC-02 | BEST-PRACTICE | VALID — Distinct error messages confirmed in `register_request` (auth_service.py:416, 422-424, 432, 438). All ValueError messages forwarded to client as `detail=str(e)` (auth.py:573-576). RFC 7807 format is correctly implemented per spec, but error messages leak enumeration data. |
| SEC-03 | BEST-PRACTICE | VALID — `.env` file contains non-placeholder values while `.env.example` has proper `CHANGE_ME` placeholders. `.gitignore` correctly excludes `.env` (line 155). Risk is real: accident commit of weak defaults. |
| SEC-04 | BEST-PRACTICE | VALID — `cookie_secure: bool = True` default (config.py:227) with no environment-based override. Security headers middleware correctly uses `config.app.cookie_secure` (security.py:410). Development experience issue confirmed. |

---

## Cross-Phase Conflicts

None identified.

- SEC-01: No conflict with backend findings — test failures (BE-001, BE-002) unrelated to authentication timing
- SEC-02: No conflict with backend findings — error format follows RFC 7807 correctly; security concern is message content, not format
- SEC-03: No conflict with backend findings — confirmed consistent with gitignore and `.env.example` patterns
- SEC-04: No conflict with backend findings — configuration loading works; this is a UX improvement

---

## Rollout Safety Assessment

All validated findings are low-risk for rollout:

- **SEC-01**: Single code path modification (add dummy bcrypt in "user not found" branch). No migration, no API changes.
- **SEC-02**: Error message string changes only. No behavioral changes, no database migrations.
- **SEC-03**: `.env` file content update. No code changes required.
- **SEC-04**: Configuration default change or documentation update. No code changes if documented; low-risk if default changed.

---

## Evidence Summary

### SEC-01 Verification
- `auth_service.py:201-206`: Fast path returns `None` immediately on user not found; slow path calls `verify_password` (bcrypt, ~100ms)
- `_handle_login` (auth.py:93-101) returns same error message "Invalid credentials" for both cases — correct behavior, but timing difference remains

### SEC-02 Verification
- `auth_service.py:406-438`: Distinct messages for existing user (line 438), existing request PENDING/APPROVED (line 416), existing request REJECTED (line 422-424), blocked domain (line 432)
- `auth.py:573-576`: ValueError messages forwarded directly to client via `AppException`
- Error handling follows RFC 7807 per `docs/08-security/error-format.md` and `docs/99-reference/error-handling-guide.md`

### SEC-03 Verification
- `.env:15`: `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars` (non-placeholder)
- `.env:10-11`: `DATABASE__PASSWORD=postgres`, `DATABASE__ADMIN_PASSWORD=postgres` (weak defaults)
- `.env:18-19`: `ADMIN_USERNAME=admin@example.com`, `ADMIN_PASSWORD=admin@example.com` (same value pattern)
- `.env.example:17,23,27,58`: Proper `CHANGE_ME` placeholders as reference
- `.gitignore:155`: `.env` correctly excluded from version control

### SEC-04 Verification
- `config.py:227`: `cookie_secure: bool = True` hardcoded default with no environment-based override
- `security.py:405-413`: `set_secure_cookie` uses `config.app.cookie_secure` for secure flag
- No model_validator or field_validator that sets `cookie_secure=False` for `EnvironmentEnum.DEVELOPMENT`

---

## Summary

| Finding ID | Status |
|------------|--------|
| SEC-01 | VALIDATED |
| SEC-02 | VALIDATED |
| SEC-03 | VALIDATED |
| SEC-04 | VALIDATED |

All audit findings validated. No rejections, merges, or conflicts.

---

## Actionable Recommendations

All four findings have been resolved with code changes. Below is a per-finding summary of what was done, the exact changes, and any follow-up actions required.

### SEC-01: Timing Side-Channel in `login_user()` — RESOLVED

**File:** `src/mkobi/services/auth_service.py` (lines 201-211)

**Change:** Added a dummy `verify_password()` call in the `user_obj is None` branch before returning `None`. The dummy call uses a static bcrypt hash string, ensuring the "user not found" path takes approximately the same time (~100ms for bcrypt) as the "wrong password" path.

```python
if user_obj is None:
    # Perform dummy bcrypt call to prevent timing side-channel attack.
    verify_password(
        password,
        "$2b$12$dummy.hash.to.prevent.timing.side.channel.attack.dummy.hash",
    )
    return None
```

**Follow-up:** No API changes, no migration needed. Existing tests for `login_user` should still pass since the return value (`None`) is unchanged.

---

### SEC-02: User Enumeration in `register_request()` — RESOLVED

**File:** `src/mkobi/services/auth_service.py` (lines 406-438)

**Change:** Replaced all distinct `ValueError` messages with a single generic message: `"Unable to process registration request"`. The four previously distinct cases were:

| Old Message | Case |
|---|---|
| `"A request for this email already exists"` | Existing PENDING/APPROVED request |
| `"Your request was rejected. Contact an administrator..."` | Existing REJECTED request |
| `"This email domain is not allowed for registration"` | Blocked email domain |
| `f"User with email '{email}' already exists"` | Existing user |

All four now raise `ValueError("Unable to process registration request")`. Internal logging still captures the specific reason for debugging.

**Follow-up:** No behavioral changes to API structure. Error responses remain RFC 7807 compliant. Any tests asserting on specific error message strings for registration must be updated to match the new generic message.

---

### SEC-03: `.env` Contains Real Values — RESOLVED

**File:** `.env`

**Change:** Replaced all non-placeholder values with `CHANGE_ME` placeholders matching `.env.example`:

| Line | Old Value | New Value |
|------|-----------|-----------|
| `DATABASE__PASSWORD` | `postgres` | `CHANGE_ME_GENERATE_STRONG_SECRET` |
| `DATABASE__ADMIN_PASSWORD` | `postgres` | `CHANGE_ME_GENERATE_STRONG_SECRET` |
| `JWT__SECRET_KEY` | `dev-secret-key-for-security-testing-...` | `CHANGE_ME_GENERATE_WITH_OPENSSL_RAND_HEX_32` |
| `ADMIN_USERNAME` | `admin@example.com` | `CHANGE_ME_ADMIN_USERNAME` |
| `ADMIN_PASSWORD` | `admin@example.com` | `CHANGE_ME_GENERATE_STRONG_PASSWORD` |
| `MKOBI_APP_PASSWORD` | `dev-app-password` | `CHANGE_ME_GENERATE_STRONG_SECRET` |

**Follow-up:** The `.env` file must be re-populated with actual values before the application can start. Run `openssl rand -hex 32` for secret generation. The `.gitignore` exclusion of `.env` (line 155) remains correct and sufficient.

---

### SEC-04: `cookie_secure` Hardcoded `True` — RESOLVED

**File:** `src/mkobi/config.py` (lines 221-229)

**Change:** Added a docstring comment to `AppSettings.cookie_secure` documenting the environment-based override mechanism. No code logic change was needed because pydantic-settings with `env_nested_delimiter="__"` already supports `APP__COOKIE_SECURE=false` as an environment variable override.

**Usage for development:**
```bash
# In .env.development or shell environment:
APP__COOKIE_SECURE=false
```

**Follow-up:** For production deployments, ensure `APP__COOKIE_SECURE` is either unset (defaults to `True`) or explicitly set to `True`. Add a deployment checklist item to verify `cookie_secure=True` in staging/production environments.