---
name: 04-security-validated
description: Validated security audit findings with feasibility, consistency, and applicability assessment
agent: validator
alwaysApply: false
---

# Phase 04 Validated Findings — Security

**Source:** .ai/audit/04-security/findings.md
**Validator:** validator agent
**Date:** 2026-05-29
**Status:** complete

---

## Validation Summary

| Finding | Verdict | Classification | Severity | Notes |
|---------|---------|----------------|----------|-------|
| SEC-001 | **VALIDATED** | mandatory | MEDIUM | Confirmed: no password validation at registration |
| SEC-002 | **VALIDATED** | advisory | LOW ↓ | Defense-in-depth exists; actual risk minimal |
| SEC-003 | **VALIDATED** | mandatory | MEDIUM | Confirmed: MIME validation skipped on None content_type |
| SEC-004 | **VALIDATED** | advisory | LOW | Confirmed but mitigated by nginx in production |
| SEC-005 | **VALIDATED** | advisory | LOW | Existing entropy is adequate; recommendation is marginal |

**Rejected:** 0
**Merged:** 0
**Downgraded:** SEC-002 (MEDIUM → LOW)

---

## Validated Findings

### SEC-001: Missing Minimum Password Length Enforcement in Registration

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Title** | Missing Minimum Password Length Enforcement in Registration |
| **Type** | SPEC-DEVIATION |
| **Severity** | MEDIUM |
| **Classification** | **mandatory** |
| **Affected Modules** | `src/mkobi/models/auth.py`, `src/mkobi/services/auth_service.py` |
| **Validation** | CONFIRMED — finding is technically accurate and the vulnerability is real |

**Description:**
The `RegisterRequest` model (`auth.py:99`) declares `password: str` with no Pydantic field validator. The `register_user()` method (`auth_service.py:115-168`) passes the raw password directly to `hash_password()` without any strength validation. While `validate_password()` exists in `utils/validators.py:145-180`, it is never imported or called in the auth service flow. This allows registration with passwords of any length, including single-character passwords or passwords missing digits/letters.

**Evidence (verified):**
- `src/mkobi/models/auth.py:99` — `password: str` with no `field_validator` or `StringConstraints`
- `src/mkobi/services/auth_service.py:143-144` — `hash_password(password)` called without prior validation
- `src/mkobi/utils/validators.py:145-180` — `validate_password()` exists but is unused in registration path
- `src/mkobi/services/auth_service.py:7` — no import of `validate_password`

**Impact:**
Users can register with trivially weak passwords, increasing vulnerability to credential-based attacks, especially if rate limiting is bypassed or misconfigured.

**Root Cause:**
Validation logic was implemented in `utils/validators.py` but never wired into the registration flow. The `RegisterRequest` Pydantic model relies on type-only annotation without constraints.

**Recommendation:**
Add a `@field_validator('password')` to `RegisterRequest` or add explicit `validate_password()` call in `register_user()` before hashing. Prefer the Pydantic validator approach as it validates at the trust boundary (API layer) and returns a proper 422 response.

**Dependency Notes:**
- No dependencies on other findings or phases
- Requires `validate_password` import from `mkobi.utils.validators` or equivalent logic

**Rollout Considerations:**
- Safe to implement independently
- No database migration needed
- Backward compatible for existing users
- Should also apply to admin user creation (`admin.py:188`) and password change flows

**Semantic Stability:**
- Anchor: `RegisterRequest` class at `auth.py:95-111` — stable, low change frequency
- Anchor: `register_user()` method at `auth_service.py:115-168` — stable service method
- Both anchors are function/class-level, resilient to minor code shifts

---

### SEC-003: MIME Type Validation Can Be Bypassed by Missing Content-Type

| Field | Value |
|-------|-------|
| **ID** | SEC-003 |
| **Title** | MIME Type Validation Can Be Bypassed by Missing Content-Type Header |
| **Type** | SPEC-DEVIATION |
| **Severity** | MEDIUM |
| **Classification** | **mandatory** |
| **Affected Modules** | `src/mkobi/services/file_processing.py` |
| **Validation** | CONFIRMED — the bypass is real and exploitable |

**Description:**
The `validate_mime_type()` function in `file_processing.py:22-33` silently returns (skips validation) when `content_type is None`, logging only a warning. Since the upload endpoint (`upload.py:170`) passes `file.content_type` directly from the uploaded file, an attacker can craft a request with no `Content-Type` header to bypass MIME type validation entirely. The file extension check at `file_processing.py:81-94` still runs but is a weaker defense that can be bypassed with double extensions or misleading filenames.

**Evidence (verified):**
- `src/mkobi/services/file_processing.py:31-33` — early return on `content_type is None`:
  ```python
  if content_type is None:
      logger.warning("MIME-type not specified, skipping check")
      return
  ```
- `src/mkobi/services/file_processing.py:78` — called without checking return value:
  ```python
  validate_mime_type(content_type)
  ```
- `src/mkobi/api/routes/upload.py:170` — passes `file.content_type` which can be `None`
- Note: standalone `validate_mime_type()` in `data/loaders/validator.py:324-325` is a different function (module-level, takes non-optional `str`)

**Impact:**
An attacker can upload files with arbitrary content (e.g., executable scripts) by omitting the Content-Type header. While file extension validation still applies, MIME type is a critical defense-in-depth check that should not be silently skipped.

**Root Cause:**
The function was designed to be lenient for cases where Content-Type is unavailable, treating it as a non-blocking check rather than a security boundary. The warning-level log indicates the original author considered this an informational event, not a security issue.

**Recommendation:**
Change `validate_mime_type()` to raise `ValueError` when `content_type is None`, consistent with the existing pattern of raising on invalid types (line 42). This will propagate up through `validate_file()` → `_handle_value_error()` as a 415 Unsupported Media Type response.

**Dependency Notes:**
- No dependencies on other findings
- May overlap with SEC-004 conceptually (both relate to HTTP header security), but implementation is independent

**Rollout Considerations:**
- Safe to implement independently
- No database migration needed
- Changes validation behavior: requests previously accepted (with warning) will now be rejected
- Consider whether any legitimate clients send uploads without Content-Type (e.g., curl with `-F` flag does include it; most HTTP clients do)

**Semantic Stability:**
- Anchor: `validate_mime_type()` function at `file_processing.py:22-42` — stable private function
- Anchor: `validate_file()` function at `file_processing.py:45-112` — stable validation entry point
- Both are in the file processing service layer, unlikely to move without explicit refactoring

---

### SEC-002: JWT Secret Key Accepts Default Algorithm Without Explicit Validation

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Title** | JWT Secret Key Accepts Default Algorithm Without Explicit Validation |
| **Type** | BEST-PRACTICE |
| **Severity** | **LOW** (downgraded from MEDIUM) |
| **Classification** | **advisory** |
| **Affected Modules** | `src/mkobi/config.py`, `src/mkobi/core/security.py` |
| **Validation** | CONFIRMED but with caveats — existing defense-in-depth is adequate |

**Description:**
The `JWTSettings.algorithm` defaults to `"HS256"` in `config.py:128`. The audit finding claims there is no validation against weak algorithms (e.g., "none"), and that `validate_refresh_token()` at `security.py:355-358` silently returns None when `secret_key` is None instead of raising. However, investigation reveals:

1. The `_get_config()` function at `security.py:19-33` already raises `ValueError` if `config.jwt.secret_key is None` is falsy — this is the primary guard. The `validate_refresh_token()` None check is a secondary defensive measure.
2. The algorithm value originates from a Pydantic model default, not from direct user input. Setting `JWT__ALGORITHM=none` in production would be a configuration error, not an application vulnerability.
3. `jose.jwt.decode()` at `security.py:325-329` uses `algorithms=[config.jwt.algorithm]` explicitly, preventing algorithm confusion.

**Evidence (verified):**
- `src/mkobi/config.py:125-129` — `JWTSettings` with `algorithm: str = "HS256"` default
- `src/mkobi/core/security.py:19-33` — `_get_config()` raises `ValueError` if secret_key is None
- `src/mkobi/core/security.py:354-358` — secondary None guard with warning log (adequate behavior)
- `src/mkobi/core/security.py:325-329` — `jwt.decode()` uses explicit `algorithms` parameter
- `src/mkobi/app.py:121-123` — startup validation requires JWT secret key to be configured

**Impact:**
Low. The defense-in-depth already in place (startup validation, `_get_config()` guard, explicit `algorithms` parameter in `jwt.decode()`) provides adequate protection. Algorithm confusion attacks require both a misconfigured algorithm AND a missing secret key, which is prevented at multiple layers.

**Root Cause:**
The finding is technically correct that algorithm validation does not exist — but the actual attack surface is negligible given the existing layered defenses.

**Recommendation (adjusted):**
Acceptable to add algorithm allowlist validation (e.g., reject `"none"`, `"None"`, `"NONE"`) as a defense-in-depth measure, but this is LOW priority. The existing architecture is sound. **_get_config()** already prevents the most dangerous scenario (no secret key).

**Dependency Notes:**
- No dependencies on other findings

**Rollout Considerations:**
- If implemented: add to `JWTSettings` model validator
- Low priority — no urgency
- No migration needed

**Semantic Stability:**
- Anchor: `JWTSettings` class at `config.py:124-130` — stable configuration model
- Anchor: `_get_config()` function at `security.py:19-33` — stable utility function

---

### SEC-004: Security Headers Missing in FastAPI Response

| Field | Value |
|-------|-------|
| **ID** | SEC-004 |
| **Title** | Security Headers Missing in FastAPI Response (Present Only in nginx) |
| **Type** | BEST-PRACTICE |
| **Severity** | LOW |
| **Classification** | **advisory** |
| **Affected Modules** | `src/mkobi/app.py` |
| **Validation** | CONFIRMED — but risk is mitigated by nginx in standard deployments |

**Description:**
The FastAPI application (`app.py`) configures CORS and GZip middleware but does not include any security header middleware. Headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, and `Content-Security-Policy` are configured only in the nginx reverse proxy (`docker/nginx/nginx.conf:17-20`). If the application is served directly without nginx (development, testing, alternative deployments), these headers are absent.

**Evidence (verified):**
- `src/mkobi/app.py:148-164` — Only CORS and GZip middleware registered
- `docker/nginx/nginx.conf:17-20` — Security headers present in nginx config
- No imports of `secure`, `starlette.middleware.base` for custom headers, or similar

**Impact:**
Low. In standard Docker Compose production deployments, nginx is the first point of contact and provides all security headers. The risk exists only for:
- Direct access to the FastAPI container (development, debugging)
- Custom deployments without nginx
- Health check endpoints hit directly (though these are low-risk)

**Root Cause:**
Design decision to rely on the reverse proxy for security headers, which is a common and generally acceptable pattern. The nginx configuration provides defense-in-depth for the standard deployment.

**Recommendation:**
Consider adding security header middleware to FastAPI for defense-in-depth, using a lightweight approach (e.g., custom middleware class or `starsessions`/`secure` library). Priority is LOW since nginx covers production. If implemented, ensure headers don't duplicate or conflict with nginx headers when both are present.

**Dependency Notes:**
- No dependencies on other findings

**Rollout Considerations:**
- Safe to implement independently
- If headers are added at both nginx and application level, test for duplicate headers
- No migration needed

**Semantic Stability:**
- Anchor: `create_app()` function at `app.py:108-286` — stable application factory
- Middleware registration area (lines 150-164) is the insertion point

---

### SEC-005: Temporary Passwords Generated with Acceptable Entropy

| Field | Value |
|-------|-------|
| **ID** | SEC-005 |
| **Title** | Temporary Passwords Generated with Acceptable Entropy |
| **Type** | BEST-PRACTICE |
| **Severity** | LOW |
| **Classification** | **advisory** |
| **Affected Modules** | `src/mkobi/api/routes/admin.py` |
| **Validation** | CONFIRMED — but current implementation is adequate |

**Description:**
Temporary passwords for newly approved users are generated using `secrets.token_urlsafe(16)` (`admin.py:188`), which produces ~128 bits of entropy (16 bytes → ~22 URL-safe base64 characters). The audit finding suggests increasing to 32 bytes for "modern best practices." However, 128 bits of cryptographic entropy is more than sufficient for temporary credentials — it exceeds the entropy of most user-chosen passwords by orders of magnitude. `secrets.token_urlsafe` uses `os.urandom()` which is cryptographically secure.

**Evidence (verified):**
- `src/mkobi/api/routes/admin.py:188` — `temp_password = secrets.token_urlsafe(16)`
- `secrets` module documentation: token_urlsafe uses the most secure random source available
- 16 bytes = 128 bits of entropy; 2^128 is computationally infeasible to brute-force

**Impact:**
Negligible. 128-bit random tokens are standard practice for temporary passwords and password reset tokens. The recommendation to increase to 32 bytes provides no practical security benefit.

**Root Cause:**
The audit finding applies overly aggressive standards. 128-bit CSPRNG tokens are widely accepted as secure (e.g., Django's password reset tokens use similar entropy).

**Recommendation (adjusted):**
No change required. Current implementation is secure. If organizational policy demands longer tokens, 24 bytes is a reasonable middle ground (produces ~32 characters, still manageable for users). This is LOWEST priority.

**Dependency Notes:**
- No dependencies on other findings

**Rollout Considerations:**
- If changed: no migration needed, only affects new temporary passwords
- Ensure any new length produces passwords within bcrypt's 72-byte limit (32 bytes → ~43 chars, well within limit)

**Semantic Stability:**
- Anchor: `approve_registration_request_admin_endpoint()` at `admin.py:163-218` — stable route handler

---

## Rejected Findings

**None.** All 5 findings were validated. SEC-002 was downgraded in severity but not rejected.

---

## Dependency Validation

```
SEC-001 ──► (no dependencies)
SEC-003 ──► (no dependencies)
SEC-002 ──► (no dependencies)
SEC-004 ──► (no dependencies)
SEC-005 ──► (no dependencies)
```

**Analysis:** No cross-finding dependencies detected. All findings are independently addressable. No circular dependencies. No hidden dependency chains.

**Safe parallel execution groups:**
- Group A: SEC-001, SEC-003 (both mandatory, no shared code beyond auth.py/app.py)
- Group B: SEC-002, SEC-004, SEC-005 (all advisory, independent modules)

**Execution order recommendation:**
1. SEC-001 first (mandatory, touches auth model + service)
2. SEC-003 second (mandatory, touches file processing service)
3. Advisory findings in any order after mandatory fixes

---

## Rollout Safety Analysis

| Finding | Risk Level | Rollback Feasibility | Coupling |
|---------|-----------|---------------------|----------|
| SEC-001 | Low | Revert validator addition | Isolated to auth model/service |
| SEC-003 | Low | Revert to lenient behavior | Isolated to file_processing.py |
| SEC-002 | Very Low | Remove algorithm check | Isolated to config model |
| SEC-004 | Low | Remove middleware | Isolated to app.py middleware stack |
| SEC-005 | Very Low | Change constant | Single line change |

**No rollout conflicts detected.** All findings affect independent modules with clear boundaries.

---

## Architectural Consistency Warnings

1. **SEC-001 + SEC-003 Pattern:** Both mandatory findings share a root cause pattern — validation logic exists but is not integrated into the execution path. Recommend a review of all `utils/validators.py` functions to ensure each is actually called where intended. This is a systematic issue, not an isolated bug.

2. **SEC-004 Defense-in-Depth:** The application relies on nginx for security headers, which violates the principle of defense-in-depth at the application layer. While acceptable for the current deployment model, this creates risk if deployment topology changes. Consider documenting this as an accepted architectural decision with a clear constraint.

---

## Mandatory Fixes

| ID | Finding | Priority |
|----|---------|----------|
| SEC-001 | Missing minimum password length enforcement in registration | **HIGH** |
| SEC-003 | MIME type validation can be bypassed by missing Content-Type header | **HIGH** |

## Advisory Recommendations

| ID | Finding | Priority |
|----|---------|----------|
| SEC-002 | JWT algorithm validation (defense-in-depth) | LOW |
| SEC-004 | Security headers middleware in FastAPI | LOW |
| SEC-005 | Temporary password entropy increase | LOWEST |

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `SEC-001`, `SEC-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction |
| `classification` | enum | `mandatory` or `advisory` |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements
