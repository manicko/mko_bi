# Validation Report — Phase 04: Security

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/04-security/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted (unchanged) | Rejected | Reclassified | Merged |
|----------------|-------|----------------------|----------|--------------|--------|
| Mandatory | 4 | 3 | 0 | 1 | 0 |
| Advisory | 4 | 4 | 0 | 0 | 0 |
| **Total** | **8** | **7** | **0** | **1** | **0** |

---

## Reclassified Findings

### SEC-004: Reclassified `BEST-PRACTICE` → `SPEC-DEVIATION`

| Field | Original | Updated |
|-------|----------|---------|
| **ID** | SEC-004 | SEC-004 |
| **Severity** | MEDIUM | MEDIUM |
| **Type** | BEST-PRACTICE | SPEC-DEVIATION |
| **Classification** | mandatory | mandatory |
| **Status** | ACCEPTED (reclassified) | — |

**Rationale:** The finding describes returning plaintext `temp_password` in HTTP JSON responses. The SPEC.md (v3.2, line 164) explicitly documents this as a known design decision: "Registration approval ... returns `temp_password` in plaintext JSON. Security requirements: HTTPS must be enforced in production; the temp password is one-time use (user must change on first login)."

The current code (`auth_service.py:577-580`, `admin.py:255-258`) returns `temp_password` in the response body — this matches the documented spec. The finding recommends stopping this behavior, which would be a deviation from the current specification. However, the spec's own security note ("admin should communicate the password through a secure out-of-band channel") acknowledges this is suboptimal.

Reclassifying from BEST-PRACTICE to SPEC-DEVIATION because: the finding asks to change code to be *more secure than the documented spec requires*. This is a spec deviation the other way — the spec should be updated (or the code should implement a more secure channel). The fix target is ambiguous: either the code should be changed to not return the password (requiring a spec update), or the spec should be updated to acknowledge the plaintext response as acceptable with compensating controls. Classified as SPEC-DEVIATION because the proper fix direction (code vs docs) is unresolved.

**Recommendation adjusted:** Either (a) change both code and spec to not return `temp_password` (use one-time secure link instead), or (b) update spec to explicitly state that returning `temp_password` in the response is an accepted risk with compensating controls (HTTPS mandatory, force_password_change=True, one-time use). Either way, code and spec must be consistent.

---

## Rejected Findings

**None.** All 8 findings describe real, applicable issues in the codebase.

---

## Cross-Phase Conflicts

### 1. SEC-002 vs Phase 01 (BE-007) — Overlapping `get_session` deprecation

Not a direct conflict, but SEC-002 reports that `docker/.env` contains weak values and recommends startup validation for JWT secret key entropy. Phase 01 (BE-007) confirms that `utils/decorators.py` is dead code with zero imports. No conflict — these findings address separate concerns.

### 2. SEC-006 vs Phase 03 (DB-07) — Force password change column availability

SEC-006 recommends adding JWT secret key entropy validation at startup. Phase 03 (DB-07) reports that `force_password_change` column is missing from the test database. These are independent findings. No conflict.

### 3. SEC-003 vs Phase 01 (BE-002) — Dashboard access control

SEC-003 reports that `dashboards_crud.py` update/delete endpoints lack resource-level access control. Phase 01 (BE-002) reports that `data.py` uses raw `select(Graph)` instead of the repository pattern. Both findings relate to defense-in-depth in the data access layer but address different modules and different root causes. No conflict.

### 4. SEC-008 vs Phase 01 (BE-002/BE-003) — Service-layer access control

SEC-008 reports that `data_service.py` methods lack access control. Phase 01 (BE-003) reports a `PermissionError` import bug in `data.py`. Both touch the data layer but address different issues (missing access control vs incorrect exception handling). No conflict — they are complementary.

### 5. SEC-005 — No HSTS/CSP headers

No other phase reports on security headers. No conflict.

### 6. SEC-001 — Token revocation

No other phase addresses token revocation. No conflict.

### 7. SEC-007 — Cookie samesite

No other phase addresses cookie configuration. No conflict.

**Summary:** No cross-phase conflicts detected. All Phase 04 findings are independent of findings from Phases 01-03.

---

## Rollout Safety Assessment

### SEC-001 (Token revocation) — Rollout Risk: MEDIUM

- **Risk:** Adding a `jti` claim to tokens and Redis-based denylist requires changes to `create_access_token`, `create_refresh_token`, `decode_token`, `get_current_user_dependency`, and all token validation paths. This is a cross-cutting change affecting every authenticated endpoint.
- **Dependency:** Redis is already used for rate limiting (`AsyncRateLimiter` in `security.py:80-111`), so the infrastructure exists. However, adding a hard dependency on Redis for auth (not just rate limiting) means Redis downtime would block all authenticated requests unless a fail-open mode is implemented.
- **Mitigation:** Implement with a fail-open mode (if Redis is unavailable, skip revocation check and log a warning). Add `jti` to new tokens first (backward compatible — old tokens without `jti` still work). Then enable enforcement.

### SEC-002 (Weak default secrets) — Rollout Risk: LOW

- **Risk:** Removing weak defaults from `docker/.env` and `docker-compose.override.yml` could break local development if developers don't have their own `.env` overrides.
- **Mitigation:** The `docker-compose.yml` already uses `${JWT__SECRET_KEY:?JWT__SECRET_KEY is required}` (enforced). Only the `.override.yml` has fallbacks. Removing fallbacks from `.override.yml` is safe — developers must provide their own `.env`.

### SEC-003 (Dashboard resource-level access control) — Rollout Risk: LOW

- **Risk:** Minimal. The `require_dashboard_admin_access` dependency already exists in `deps.py:699-740`. The fix is to add it to the route dependencies in `dashboards_crud.py:282,351` and pass `current_user.id` to the service. The service methods (`update_dashboard`, `delete_dashboard`) need to accept user context.
- **Dependency:** The service layer changes (`update_dashboard` and `delete_dashboard` need `user_id` and `user_role` parameters) are straightforward but require updating the service interface.

### SEC-004 (Plaintext temp passwords) — Rollout Risk: LOW

- **Risk:** Removing `temp_password` from the response requires an alternative delivery mechanism (email, one-time link). If the spec is updated instead (accepting the current behavior), no code change is needed.
- **Dependency:** If implementing a secure channel, depends on email infrastructure.

### SEC-005 (HSTS and CSP headers) — Rollout Risk: LOW

- **Risk:** Adding headers is a configuration-only change. Risk of breaking existing behavior is minimal.
- **Dependency:** None. Self-contained change to `app.py:67-71` and `nginx.conf:17-20`.

### SEC-006 (JWT entropy validation) — Rollout Risk: LOW

- **Risk:** Adding a validator to `JWTSettings` could prevent startup in development if developers have weak keys. This is intentional — it forces developers to use strong keys.
- **Dependency:** None. Self-contained change to `config.py:124-130`.

### SEC-007 (Cookie samesite) — Rollout Risk: LOW

- **Risk:** Changing `COOKIE_SAMESITE` from `"strict"` to `"lax"` is a one-line change in `security.py:42`. No breaking changes expected.
- **Dependency:** None.

### SEC-008 (Data service access control) — Rollout Risk: MEDIUM

- **Risk:** Adding access control to `data_service.py` methods requires adding `user_id`/`user_role` parameters to `get_aggregated_data`, `get_available_metrics`, `get_available_dimensions`, and their internal methods. This changes the service interface and all callers must be updated.
- **Dependency:** The route handler (`data.py:86-100`) already checks access. The service-layer check is defense-in-depth. If the service interface changes, the `IDataService` interface and all tests must be updated.
- **Mitigation:** Add optional parameters with defaults (`user_id: UUID | None = None`) to avoid breaking existing callers. Only enforce the check when `user_id` is provided.

---

## Mandatory Fixes (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| SEC-001 | HIGH | BEST-PRACTICE | No token revocation mechanism — deactivated users can use valid tokens until expiry |
| SEC-002 | HIGH | SPEC-DEVIATION | Weak default secrets in `docker/.env` and `docker-compose.override.yml` fallbacks |
| SEC-003 | HIGH | SPEC-DEVIATION | Dashboard update/delete endpoints lack resource-level access control |
| SEC-004 | MEDIUM | SPEC-DEVIATION | Plaintext temp passwords returned in HTTP responses (reclassified from BEST-PRACTICE) |

## Advisory Recommendations (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| SEC-005 | MEDIUM | BEST-PRACTICE | Missing HSTS and CSP security headers |
| SEC-006 | MEDIUM | BEST-PRACTICE | JWT secret key has no entropy or strength validation |
| SEC-007 | LOW | BEST-PRACTICE | Cookie samesite set to "strict" instead of "lax" |
| SEC-008 | LOW | BEST-PRACTICE | Data service layer missing defense-in-depth access control |

---

## Summary

- **8 findings validated**, 0 rejected, 1 reclassified (SEC-004: BEST-PRACTICE → SPEC-DEVIATION).
- **No cross-phase conflicts** with Phases 01-03.
- **No merges** — no findings share duplicate root causes.
- **4 mandatory fixes** (SEC-001 through SEC-004), **4 advisory recommendations** (SEC-005 through SEC-008).
- **Highest rollout risk:** SEC-001 (token revocation — cross-cutting auth change) and SEC-008 (service interface changes).
- **Lowest rollout risk:** SEC-002, SEC-005, SEC-006, SEC-007 (configuration-only or single-file changes).
