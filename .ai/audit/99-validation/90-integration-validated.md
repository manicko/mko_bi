# Validation Report — Phase 90: Integration

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/90-integration/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted (unchanged) | Rejected | Reclassified | Merged |
|----------------|-------|----------------------|----------|--------------|--------|
| Mandatory | 5 | 4 | 0 | 0 | 1 |
| Advisory | 5 | 4 | 1 | 0 | 0 |
| **Total** | **10** | **8** | **1** | **0** | **1** |

---

## Merged Findings

### INT-007 → Merged into SEC-001 (Phase 04)

**Original ID:** INT-007
**Merged into:** SEC-001 (Phase 04 — Security)

**Rationale:** INT-007 and SEC-001 identify the same root cause: no server-side refresh token revocation mechanism after logout. Both findings point to `auth.py:362` (only `delete_secure_cookie`, no blacklist) and `security.py` (no token revocation logic). The conclusion and recommendation are identical: implement token versioning or Redis-based jti blacklist.

SEC-001 was already validated as a mandatory BEST-PRACTICE finding by Phase 04 validation. Merging INT-007 into SEC-001 eliminates duplicate tracking of the same security gap.

| Field | INT-007 | SEC-001 |
|-------|---------|---------|
| **Severity** | HIGH | HIGH |
| **Type** | SPEC-DEVIATION | BEST-PRACTICE |
| **Classification** | mandatory | mandatory |

**Resolution:** SEC-001 takes precedence (already validated). INT-007 is closed as a merge. The combined finding should note both the security implication (stolen refresh tokens) and the integration symptom (logout only clears client cookie).

---

## Rejected Findings

### INT-003: Layout `updated_at` field potentially missing — REJECTED

**Rejection reason:** The finding speculates that the `updated_at` field might be `None` on layout creation because `create_layout_endpoint` only calls `layout_service.create_layout()` which creates the ORM model. However, direct evidence confirms the field **does exist and is populated**:

1. **ORM model:** `src/mkobi/db/models/layout.py:56-60` defines `updated_at: Mapped[datetime]` with `server_default=text("now()")`.
2. **Pydantic model:** `src/mkobi/models/layout.py:87-92` defines `LayoutRead` with `updated_at: datetime` (required).
3. **Layout service:** `layout_service.py:70` calls `LayoutRead.model_validate(layout_obj)` which reads from the ORM model that has `server_default` populated by PostgreSQL.
4. The `DashboardRead` example at `dashboard.py:123` also demonstrates `updated_at` in JSON schema output.

The backend **does** return `updated_at` for layouts. The frontend `LayoutRead` type (`adminApi.ts:15-21`) correctly declares `updated_at: string`. There is no mismatch. The finding is **stale** — the concern was valid as speculation but the evidence confirms the field works correctly.

---

## Cross-Phase Conflicts

### 1. INT-001 vs Phase 01 (BE-001) — Route mounting overlap

**INT-001** reports that `POST /{dashboard_id}/process` exposes an orphaned endpoint with `task_id` as an implicit query parameter. Phase 01 (BE-001) flagged the architectural pattern of dual-mounting sub-routers (both in composite `dashboards` router and individually in `app.py`).

These findings address different aspects of the same structural issue: the upload router at `app.py:205` is mounted individually at `prefix="/api/v1"`, making its routes available at `/api/v1/upload/...`. The `/process` endpoint is part of this individually-mounted upload router. The BE-001 finding (validated as SPEC-DEVIATION about fragile mounting patterns) provides architectural context for why orphaned endpoints like INT-001 exist.

**No direct conflict** — the findings are complementary. However, resolving BE-001's architectural smell (cleaner route mounting) should be coordinated with INT-001's fix (remove or properly wire the `/process` endpoint) to avoid accidentally breaking route registration.

### 2. INT-005 vs Phase 02 (Frontend) — ProcessingStatusResponse type mismatch

**INT-005** reports `completed_at` (backend) vs `finished_at` (frontend) field name mismatch. Phase 02 frontend audit did not flag this specific type mismatch (it was not in scope for the frontend architecture phase — Phase 02 covered component patterns, not API contract alignment).

**No conflict.** Phase 02 validation did not examine the `ProcessingStatusResponse` frontend type. The finding stands on its own.

### 3. INT-006 — `DashboardSummary.permission` not in backend response

No other phase examined the `GET /dashboards/my` contract. **No conflict.**

### 4. INT-009 — Missing `force_password_change` check in login callback

No other phase examined the `useAuth` hook's login flow for `force_password_change` handling. **No conflict.**

### 5. INT-002 — Orphaned `/api/v1/filters` endpoints

Phase 01 (BE-001) noted that `filters.py` and `dashboards_filters.py` are separately mounted routers with different prefix structures and no path collision. INT-002 reports the *integration* symptom: the frontend never calls the global filter endpoints. These findings are complementary — BE-001 describes the route architecture, INT-002 describes the integration gap.

**No conflict**, but fixing INT-002 (removing orphaned endpoints) could simplify the architecture flagged by BE-001.

---

## Rollout Safety Assessment

### INT-001 — Orphaned `/process` endpoint

- **Risk:** LOW
 - Removing the endpoint is a clean delete of dead code.
 - Confirmation: no frontend code calls this endpoint (`grep` for `/process` across `frontend/src` returns no matches for upload processing).
 - **Mitigation:** Verify no external scripts or documentation reference this endpoint before removal.
- **Dependency:** None. Self-contained removal.

### INT-002 — Orphaned `/api/v1/filters` CRUD endpoints

- **Risk:** LOW to MEDIUM
 - Removing `filters.py` router and its registration in `app.py:208` is straightforward.
 - **Risk:** If filter management is planned for a future sprint, removing these endpoints creates rework. The `Filter` type in `api.types.ts:53-58` and the `FilterService` / `FilterRepository` infrastructure all exist, suggesting this was intended to be wired up.
 - **Mitigation:** Before removal, confirm with the team that filter management UI is not in the immediate roadmap. If it is, wire it up instead of removing.
- **Dependency:** Removing the router from `app.py:208` also requires removing the `get_filter_service` dependency from `deps.py` if no other consumer exists.

### INT-005 — ProcessingStatusResponse type alignment

- **Risk:** LOW
 - Renaming `finished_at` to `completed_at` in the frontend type is a breaking change for any code reading `finished_at`.
 - Adding missing fields (`progress`, `task_id`, `filename`, `dashboard_id`) is additive and safe.
 - **Mitigation:** Search for all usages of `finished_at` from `ProcessingStatusResponse` across the frontend before renaming.
- **Dependency:** None. Frontend-only type change.

### INT-006 — `DashboardSummary.permission` field mismatch

- **Risk:** LOW
 - Making `permission` optional in the frontend type is a safe relaxation.
 - Alternatively, adding `permission` to the backend `DashboardRead` response requires a service-layer change to compute the permission from the user's access record.
 - **Mitigation:** Making `permission` optional (`permission?: DashboardPermission`) is the lowest-risk fix and maintains backward compatibility.
- **Dependency:** None for the frontend-only fix.

### INT-008 — Error response format standardization

- **Risk:** MEDIUM
 - Standardizing error responses across all endpoints requires changes to `app.py` exception handlers, `exceptions.py`, and potentially individual route handlers that return raw dicts.
 - The frontend `axiosInstance.ts` error handler (`105-107`) only checks `status === 403` — updating it to display `error.response.data.detail` is a small change but must be tested for all error scenarios.
 - **Mitigation:** Standardize backend first (add `response_model` to all endpoints that return raw dicts), then update frontend error display. The `change_password` endpoint (`auth.py:372-433`) and `register-request` endpoint (`auth.py:442-521`) are the primary offenders returning raw dicts without `response_model`.
- **Dependency:** Backend changes must be deployed before frontend changes to avoid the frontend expecting a structured format that the old backend doesn't provide.

### INT-009 — `force_password_change` in login callback

- **Risk:** LOW
 - Adding a `force_password_change` check in the `login` callback (`useAuth.ts:24-38`) is a small, isolated change.
 - The check pattern already exists in the `useEffect` block (lines 65 and 84) — it just needs to be replicated after `setUser(response.user)` in the login callback.
 - **Mitigation:** Extract the redirect logic into a shared helper to avoid duplication.
- **Dependency:** None. Frontend-only change.

### INT-010 — `CreateDashboardRequest` missing `config` field

- **Risk:** LOW
 - Adding `config` to `CreateDashboardRequest` and passing it through `createDashboard()` is additive.
 - The backend already accepts `config` in `DashboardCreate` (`dashboard.py:55`) with a default value.
 - **Mitigation:** This is advisory — the default config works. Only implement if admin dashboard creation with custom config types is a user requirement.
- **Dependency:** None.

---

## Mandatory Fixes (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| INT-001 | CRITICAL | RUNTIME-ERROR | `POST /{dashboard_id}/process` has `task_id` as implicit query param, no frontend call — orphaned endpoint with runtime error if called |
| INT-002 | CRITICAL | RUNTIME-ERROR | `/api/v1/filters` CRUD endpoints are orphaned — no frontend code calls them, increasing attack surface |
| INT-005 | HIGH | RUNTIME-ERROR | `ProcessingStatusResponse` frontend type uses `finished_at` instead of `completed_at`, missing `progress` field |
| INT-009 | MEDIUM | RUNTIME-ERROR | `login` callback in `useAuth.ts` doesn't check `force_password_change`, allowing users with temp passwords to bypass password change |

## Advisory Recommendations (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| INT-004 | LOW | SPEC-DEVIATION | `change_password` returns raw dict without `response_model`; frontend declares `Promise<void>` |
| INT-006 | MEDIUM | SPEC-DEVIATION | `DashboardSummary` frontend type requires `permission` but backend `DashboardRead` doesn't return it |
| INT-008 | MEDIUM | BEST-PRACTICE | Inconsistent error response formats across endpoints; frontend ignores structured error details |
| INT-010 | LOW | SPEC-DEVIATION | `CreateDashboardRequest` lacks `config` field; admin can't configure graph types during dashboard creation |

## Doc Updates Needed

- Document the orphaned `/api/v1/filters` endpoint status: either implement the frontend filter management UI or remove the backend endpoints and document the decision (INT-002).
- Document the `DashboardSummary` vs `DashboardRead` type separation: `DashboardSummary` is a frontend-only type for list views, and the `permission` field should be documented as frontend-computed (not backend-provided) or removed (INT-006).
- Document the error response format standard: all error responses should use `{status_code, detail, error_code}` format. Endpoints returning raw dicts (`change_password`, `register-request`) should be updated to use `SuccessResponse` or a typed error model (INT-008).

---

## Summary

- **10 findings validated**, 1 rejected (INT-003 — `updated_at` field exists and is populated), 1 merged (INT-007 → SEC-001).
- **4 mandatory fixes** (INT-001, INT-002, INT-005, INT-009), **4 advisory recommendations** (INT-004, INT-006, INT-008, INT-010).
- **1 merge** with Phase 04 (INT-007 → SEC-001 token revocation).
- **No cross-phase conflicts** that require resolution — complementary findings in Phase 01 (route architecture) and Phase 02 (frontend patterns) provide context but don't contradict.
- **Highest rollout risk:** INT-008 (error format standardization — cross-cutting backend + frontend change).
- **Lowest rollout risk:** INT-001 (dead code removal), INT-009 (single-function frontend change), INT-010 (additive type extension).
