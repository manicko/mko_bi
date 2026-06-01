# Task Specification Validation Report — mkobi BI Dashboard

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/tasks/todo/` (41 task files + order.yaml)
**Source of truth:** `.ai/audit/validated/final-report.md` + 9 phase validation reports

---

## 1. Validated Counts

| Category | Count |
|----------|-------|
| Total task files | 41 |
| Approved (no changes needed) | 29 |
| Approved with warnings/advisory notes | 10 |
| Rejected | 2 |

---

## 2. Critical Structural Defects Found

### DEF-001: ID Mismatch in TASK_043 and TASK_046 (BLOCKING)

**Severity:** BLOCKING — prevents execution

Two task files have internal `id` fields that do NOT match their filenames or the order.yaml references:

| File | Internal `id` (wrong) | Should be (correct) |
|------|----------------------|---------------------|
| `TASK_043_verify_backend_architecture.yaml` | `TASK_032_verify_backend_architecture` | `TASK_043_verify_backend_architecture` |
| `TASK_046_verify_database_migrations.yaml` | `TASK_035_verify_database_migrations` | `TASK_046_verify_database_migrations` |

All `depends_on` references in other tasks and in the order.yaml use `TASK_043` and `TASK_046`. If an executor reads the internal `id` field, it will look for `TASK_032` and `TASK_035` which do not exist, causing dependency resolution failure.

**Required fix:** Update the `id` field in both files to match filenames and order.yaml.

**Status:** REJECTED until fixed. Task files renamed to `*_REJECTED.yaml`.

---

## 3. Approved Tasks (No Changes Required)

The following tasks pass all validation checks:

| Task | Validation Result |
|------|-------------------|
| TASK_009_fix_dual_router_mounting | ✅ Approved |
| TASK_010_implement_token_revocation | ✅ Approved |
| TASK_011_remove_weak_default_secrets | ✅ Approved |
| TASK_012_add_resource_level_access_control | ✅ Approved |
| TASK_013_remove_plaintext_temp_passwords | ✅ Approved |
| TASK_014_add_security_headers | ✅ Approved |
| TASK_015_add_streaming_size_check | ✅ Approved |
| TASK_016_fix_mime_type_validation | ✅ Approved |
| TASK_017_fix_silent_exception_swallowing | ✅ Approved |
| TASK_018_fix_yoy_inf_values | ✅ Approved |
| TASK_020_increase_frontend_test_coverage | ✅ Approved |
| TASK_021_fix_processing_status_response_mismatch | ✅ Approved |
| TASK_022_fix_gettoken_stale_state | ✅ Approved |
| TASK_023_add_confirm_password_server_validation | ✅ Approved |
| TASK_024_fix_migration_chain_branch | ✅ Approved |
| TASK_025_fix_orm_unique_index_drift | ✅ Approved |
| TASK_026_add_missing_fk_indexes | ✅ Approved |
| TASK_027_add_force_password_change_to_test_db | ✅ Approved |
| TASK_030_standardize_error_responses | ✅ Approved |
| TASK_031_fix_cors_origins_production | ✅ Approved |
| TASK_037_test_token_revocation | ✅ Approved |
| TASK_038_test_mime_type_validation | ✅ Approved |
| TASK_039_test_streaming_size_limit | ✅ Approved |
| TASK_040_test_resource_access_control | ✅ Approved |
| TASK_041_test_standardized_error_responses | ✅ Approged |
| TASK_042_test_force_password_change_flow | ✅ Approved |
| TASK_044_verify_security_fixes | ✅ Approved |
| TASK_045_verify_data_processing | ✅ Approved |
| TASK_047_verify_full_system | ✅ Approved |

---

## 4. Approved Tasks with Warnings

### TASK_001 — Fix Docker test port exposure (TST-001)

**Status:** ✅ Approved with advisory warnings

**Findings:**
1. **`docker-compose.test.yml` port already exposed.** The test compose already has `ports: ["5433:5432"]` on the `test-db` service (line 19-20). Adding another ports section is redundant and could cause drift.
2. **Service name mismatch.** The task targets `name: db` but the actual service is `test-db`.
3. **The actual fix is in `conftest.py`.** Line 18 sets `DATABASE__PORT` to `5432` but should be `5433` to match the test-db port mapping.

**Warnings:**
- Remove the `docker/docker-compose.test.yml` file entry from this task — the change is already present in the file. The test-db port 5433 is already exposed.
- Or, if this task intends to document the existing state, change the action from `add_code` to `verify_code`.
- The `conftest.py` change is the actual fix needed.

**Semantic stability:** ✅ Stable. The conftest.py line number and pattern are concrete.

---

### TASK_002 — Remove orphaned POST /{dashboard_id}/process endpoint (INT-001)

**Status:** ✅ Approved with advisory warnings

**Findings:**
1. **Endpoint confirmed orphaned.** Grep for `/process` in frontend/src returns no matches. The endpoint at `upload.py:216` (`process_file_endpoint`) has no frontend consumer.
2. **Endpoint confirmed broken.** The handler signature takes `task_id: UUID` as a query parameter (line 224), but the route path `/{dashboard_id}/process` doesn't capture it. This creates a broken endpoint that always fails at FastAPI's parameter binding level.
3. **Semantic anchor is fragile.** The anchor `insert_before: @router.post` is ambiguous — there are 21 `@router.post` decorators across route files, and 2 in upload.py alone. Must specify the specific route path.

**Warnings:**
- Update semantic anchor to reference the specific path: `value: "/{dashboard_id}/process"` for uniqueness.
- This removal affects 2 files minimum: `upload.py` (remove handler) and check if `app.py` mounts this router separately.

**Architectural safety:** ✅ Safe. Dead code removal, no functional impact.

---

### TASK_003 — Remove orphaned filters.py endpoints (INT-002)

**Status:** ✅ Approved with correction required

**Findings:**
1. **Filters.py endpoints confirmed orphaned.** Grep for `/api/v1/filters` usage in frontend returns no matches.
2. **Critical targeting error.** The task says to remove `include_router` from `app.py`, but the filters router is NOT included directly in `app.py`. It is included via `dashboards.py:22` as `router.include_router(filters_router)` inside the composite dashboards router.
3. Removing CRUD handlers from `filters.py` alone would make the router a hollow shell — still registered but returning 404s for all routes.

**Required correction:**
- Add `src/mkobi/api/routes/dashboards.py` as a target file, with action `remove_code` for the `include_router(filters_router)` line.
- Or, if the intention is to keep the router structure for future use, document this decision.

**Impact:** Medium. The correction targets the same architectural area (route mounting) and doesn't change the task's scope.

---

### TASK_004 — Fix .env overriding production mode (INF-02)

**Status:** ✅ Approved with advisory warnings

**Findings:**
1. **CORS_ORIGINS target exists** at `docker-compose.yml:98` — confirmed `${CORS_ORIGINS:-["http://localhost:3000"]}`.
2. **No `${ENV:-production}` pattern found** in docker-compose.yml — this pattern doesn't exist at the service level. The ENV override happens through `.env` file auto-loading mechanism, not through compose variable interpolation.
3. The task's change recommendation ("Add explicit env_file or override mechanism") is too vague — the actual recommendation from INF-02 validation is to fix `.env` (remove `ENV=development`), not to change compose file service definitions.

**Warnings:**
- The task title and description talk about `.env` overriding but the file changes target `docker/docker-compose.yml`. This misalignment between problem description and prescribed fix should be clarified.
- The actual `.env` fix is handled by TASK_005 (remove weak credentials from working tree). This task is partially redundant with TASK_005.
- Consider merging with TASK_005 or clarifying the scope.

---

### TASK_005 — Remove .env files with weak credentials (DC-001)

**Status:** ✅ Approved with advisory warnings

**Findings:**
1. `.env` file exists in working tree (referenced by INF-02 finding).
2. The task uses `action: replace_file` which is a valid operation for `.env.example` creation.
3. **Depends_on is empty** in the YAML (line 9: `depends_on:` with no value) — this is valid YAML (null/empty list).

**Warnings:**
- Ensure `.env.example` covers ALL required environment variables before removing `.env`.
- Coordinate with deployment team — TASK_004, TASK_005, and TASK_011 all touch secret management and should be sequenced together.

---

### TASK_006 — Rename PermissionError shadow (BE-004)

**Status:** ✅ Approved

**Findings:**
1. `class PermissionError(Exception)` confirmed at `core/permissions.py:48`.
2. Custom exception does NOT inherit from HTTPException — correct finding. The rename to `DashboardPermissionError` is sound.
3. Multiple files reference this: `data.py`, `data_service.py`, `upload.py`.
4. The task correctly identifies TASK_007 and TASK_008 as dependents.

**Scope:** Appropriate for a single task. The rename affects ~5 files.

---

### TASK_028 — Fix login force_password_change check (INT-009)

**Status:** ✅ Approved with priority correction

**Findings:**
1. Frontend `useAuth.ts` exists (referenced by FE-005 validated finding).
2. **Priority mismatch:** Task has `priority: medium` but the finding INT-009 is classified as mandatory with MEDIUM severity. Given that this is a security flow bug (bypassing forced password change), priority should be `high`.

**Warning:** Recommend changing priority from `medium` to `high`.

---

### TASK_029 — Add DashboardSummary.permission field (INT-006)

**Status:** ✅ Approved with advisory warning

**Findings:**
1. Frontend `DashboardSummary` type at `api.types.ts:17-23` requires `permission: DashboardPermission` — confirmed.
2. Backend has NO `DashboardSummary` model — the `/dashboards` routes likely return `DashboardRead` or a different model. The task targets `src/mkobi/api/routes/dashboards.py` for modifying `DashboardSummary` class, but `DashboardSummary` doesn't exist as a backend model.
3. The backend uses `DashboardRead` for responses. The fix requires either: (a) creating a `DashboardSummary` model with permission field in the backend, or (b) making `permission` optional in the frontend type.

**Warning:** Clarify the backend target. The class `DashboardSummary` may need to be created (e.g., in `models/dashboard.py`), not just modified in routes.

---

### TASK_043_verify_backend_architecture (ID: TASK_032) — REJECTED

**Status:** ❌ REJECTED — see DEF-001 above.

---

### TASK_046_verify_database_migrations (ID: TASK_035) — REJECTED

**Status:** ❌ REJECTED — see DEF-DEF-001 above.

---

## 5. Semantic Stability Analysis

### Stable Anchors (confirmed to exist in codebase)

| Anchor | Location | Status |
|--------|----------|--------|
| `class PermissionError` | `core/permissions.py:48` | ✅ Unique, stable |
| `select(Graph)` | `data.py:119` | ✅ Unique in file |
| `@router.post("/{dashboard_id}/process")` | `upload.py:216` | ✅ Unique in codebase |
| `router.include_router(filters_router)` | `dashboards.py:22` | ✅ Unique |
| `CORS_ORIGINS` | `docker-compose.yml:98` | ✅ Unique |
| `SecurityHeadersMiddleware` | Does NOT exist | ❌ TASK_014 targets nonexistent class |
| `content_type` param in `validate_mime_type` | `file_processing.py:22` | ✅ Exists, unique |
| `fill_nan` in aggregate_transforms | Exists (task targets after fill_nan) | ✅ Stable within function |
| `task_id: UUID` in process_file_endpoint | `upload.py:224` | ✅ Exists |
| `for.*chunk` in upload streaming | Not found in upload.py | ❌ TASK_015 anchor nonexistent |

### Unstable or Missing Anchors

| Task | Anchor | Problem |
|------|--------|---------|
| TASK_014 | `class SecurityHeadersMiddleware` | SecurityHeadersMiddleware does NOT exist in the codebase. There is no custom middleware class — security headers would need to be added as new middleware. |
| TASK_015 | `for.*chunk` value in upload loop | The upload.py streaming loop uses `async for chunk in file` pattern (FastAPI UploadFile), not a simple `for chunk in ...`. The anchor `insert_after: type: loop, value: chunk` is imprecise. |

### Missing Files Referenced by Frontend Tests

The following test files are referenced as `create_file` actions but do not exist. This is correct (they should be created), but the target directory may not exist:

| Test File | Directory exists? |
|-----------|-------------------|
| `frontend/src/shared/components/ProtectedRoute.test.tsx` | `shared/components/` exists ✅ |
| `frontend/src/shared/components/RoleBasedAccess.test.tsx` | `shared/components/` exists ✅ |
| `frontend/src/features/auth/model/useAuth.test.ts` | `features/auth/model/` exists ✅ |
| `frontend/src/features/dashboards/ui/charts/PlotlyChart.test.tsx` | `features/dashboards/ui/charts/` exists ✅ |
| `frontend/src/features/auth/model/useAuth.forcePassword.test.ts` | `features/auth/model/` exists ✅ |

All parent directories exist. ✅

---

## 6. Architectural Safety Analysis

### No Architecture-Breaking Changes Detected

All tasks are either:
- Configuration fixes (ports, env vars, Docker)
- Code cleanup (dead code removal, exception rename)
- Feature additions (access control, token revocation)
- Test coverage additions

### Layering Consistency

| Task | Layer Change | Assessment |
|------|-------------|------------|
| TASK_006 | Core (permissions) | ✅ Self-contained rename |
| TASK_008 | API route → Repository | ✅ Correct direction: using repo instead of raw query |
| TASK_010 | Security → Auth routes | ✅ Cross-cutting but handled with single-file additions |
| TASK_012 | API route → Access repo | ✅ Adding access check to route handler |
| TASK_029 | API route model | ⚠️ Needs clarification on backend model location |

### Integration Safety

- Backend-breaking changes (TASK_006 PermissionError rename) have proper dependents (TASK_007, TASK_008, TASK_012, TASK_029) sequenced after.
- Frontend-only changes (TASK_020, TASK_021, TASK_022, TASK_028) have no backend blast radius.
- Cross-cutting changes (TASK_010 token revocation) are properly scoped.

---

## 7. Rollout Safety Analysis

### Execution Wave Validity

The order.yaml defines 5 execution waves. Validation confirms the wave structure is correct:

**Wave 1 (21 parallel tasks):** All tasks with no dependencies. Valid — can execute in parallel.

**Wave 2a:** Dependencies on Wave 1 tasks only:
- TASK_019 → TASK_001 ✅

**Wave 2b:** Dependencies on TASK_006:
- TASK_007, TASK_008 → TASK_006 ✅

**Wave 2c:** Dependencies on TASK_005 and TASK_006 and TASK_024 and TASK_027:
- TASK_011 → TASK_005 ✅
- TASK_012, TASK_029 → TASK_006 ✅
- TASK_025, TASK_026, TASK_027 → TASK_024 ✅
- TASK_028 → TASK_027 ✅

**Wave 3 (Test tasks):** After respective implementation:
- TASK_037 → TASK_010 ✅
- TEST_038 → TASK_016 ✅
- TASK_039 → TASK_015 ✅
- TASK_040 → TASK_012 ✅
- TASK_041 → TASK_030 ✅
- TASK_042 → TASK_028 ✅

**Wave 4 (Verification):** After all impl + test in group ✅

**Wave 5 (Final):** TASK_047 after all verification ✅

---

## 8. Rejected Tasks

### TASK_043_verify_backend_architecture (DEF-001)

**Rejection reason:** Internal `id` field is `TASK_032_verify_backend_architecture` but filename and all dependency references use `TASK_043`. This mismatch will cause dependency resolution failure during execution.

**Fix required:** Change line 1 from `id: TASK_032_verify_backend_architecture` to `id: TASK_043_verify_backend_architecture`.

**File renamed:** `TASK_043_verify_backend_architecture.yaml` → `TASK_043_verify_backend_architecture_REJECTED.yaml`

### TASK_046_verify_database_migrations (DEF-001)

**Rejection reason:** Internal `id` field is `TASK_035_verify_database_migrations` but filename and all dependency references use `TASK_046`. Same class of defect as TASK_043.

**Fix required:** Change line 1 from `id: TASK_035_verify_database_migrations` to `id: TASK_046_verify_database_migrations`.

**File renamed:** `TASK_046_verify_database_migrations.yaml` → `TASK_046_verify_database_migrations_REJECTED.yaml`

---

## 9. Summary of Required Corrections

| # | Task | Issue | Severity | Action |
|---|------|-------|----------|--------|
| 1 | TASK_043 | `id` field mismatch (032 vs 043) | BLOCKING | Reject, rename, fix `id` field |
| 2 | TASK_046 | `id` field mismatch (035 vs 046) | BLOCKING | Reject, rename, fix `id` field |
| 3 | TASK_001 | docker-compose.test.yml change redundant (port already exposed) | Advisory | Remove or change to verify_code |
| 4 | TASK_002 | Semantic anchor ambiguous (`@router.post` not unique) | Advisory | Use specific route path |
| 5 | TASK_003 | Target file for filters removal wrong (dashboards.py, not app.py) | Moderate | Add dashboards.py target |
| 6 | TASK_004 | Fix target misalignment (compose vs .env) | Advisory | Clarify scope, avoid redundancy with TASK_005 |
| 7 | TASK_014 | SecurityHeadersMiddleware class does not exist | Advisory | Change from modify to create |
| 8 | TASK_015 | Loop anchor imprecise (`for.*chunk`) | Advisory | Use specific async for pattern |
| 9 | TASK_028 | Priority should be `high` not `medium` | Advisory | Update priority field |
| 10 | TASK_029 | DashboardSummary backend model may not exist | Advisory | Verify target, may need model creation |

---

## 10. Approved Execution Graph

After fixing DEF-001 (the two ID mismatches), the execution graph is:

```
Wave 1 (parallel, no deps):
  TASK_001, TASK_002, TASK_003, TASK_004, TASK_005, TASK_006, TASK_009,
  TASK_010, TASK_013, TASK_014, TASK_015, TASK_016, TASK_017, TASK_018,
  TASK_020, TASK_021, TASK_022, TASK_023, TASK_024, TASK_030, TASK_031

Wave 2 (after wave 1):
  TASK_007 → TASK_006
  TASK_008 → TASK_006
  TASK_011 → TASK_005
  TASK_012 → TASK_006
  TASK_019 → TASK_001
  TASK_025 → TASK_024
  TASK_026 → TASK_024
  TASK_027 → TASK_024
  TASK_029 → TASK_006

Wave 3 (after wave 2):
  TASK_028 → TASK_027

Wave 4 — Tests (after respective implementation):
  TASK_037 → TASK_010
  TASK_038 → TASK_016
  TASK_039 → TASK_015
  TASK_040 → TASK_012
  TASK_041 → TASK_030
  TASK_042 → TASK_028

Wave 5 — Verification:
  TASK_043 → TASK_006, 007, 008, 009
  TASK_044 → TASK_010, 011, 012, 013, 014, 037, 040
  TASK_045 → TASK_015, 016, 017, 018, 038, 039
  TASK_046 → TASK_024, 025, 026, 027

Wave 6 — Final:
  TASK_047 → TASK_043, 044, 045, 046, 019, 020, 021, 022, 028, 041, 042
```

---

## 11. Mandatory vs Advisory Classification

### Mandatory Fixes (must succeed before production)

| Task | Finding | Reason |
|------|---------|--------|
| TASK_001 | TST-001 | 233/603 tests failing — blocks validation of all other fixes |
| TASK_002 | INT-001 | Broken endpoint increases attack surface |
| TASK_003 | INT-002 | Orphaned endpoints increase attack surface |
| TASK_006 + 007 | BE-003, BE-004 | PermissionError causes 500 instead of 403 |
| TASK_010 | SEC-001 | No token revocation |
| TASK_012 | SEC-003 | Missing resource-level access control |
| TASK_015 | DP-001 | Unbounded file upload |
| TASK_016 | DP-003 | Spoofable MIME type validation |
| TASK_017 | DP-004 | Silent exception swallowing |
| TASK_018 | DP-008 | YoY inf breaks JSON serialization |

### Advisory Recommendations (should fix, not blocking)

| Task | Finding | Reason |
|------|---------|--------|
| TASK_004 | INF-02 | Env override protection |
| TASK_005 | DC-001 | Weak .env in working tree |
| TASK_008 | BE-002 | Repository pattern bypass |
| TASK_009 | BE-001 | Dual router mounting |
| TASK_011 | SEC-002 | Weak default secrets |
| TASK_013 | SEC-004 | Plaintext temp passwords |
| TASK_014 | SEC-005 | Missing security headers |
| TASK_019 | TST-006 | Test DB isolation |
| TASK_020 | TST-004 | Frontend coverage |
| TASK_021 | INT-005 | Field name mismatch |
| TASK_022 | FE-005 | Stale token state |
| TASK_023 | FE-009 | Confirm password validation |
| TASK_024-027 | DB-01 to DB-07 | Migration + index fixes |
| TASK_028-031 | INT/FE/DC minor | Integration + config |
| TASK_037-042 | Test tasks | Coverage verification |

---

*End of report*
