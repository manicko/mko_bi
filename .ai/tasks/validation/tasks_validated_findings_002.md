# Task Specification Validation Report — mkobi BI Dashboard

**Date:** 2026-05-18
**Validator:** Kilo System Integrity Validation Agent
**Source:** 34 tasks (22 PLAN_01 Documentation + 11 PLAN_02 Authorization)

---

## Validation Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 34 |
| Approved | 33 |
| Rejected | 1 |
| Requires Revision | 2 |

---

## PLAN_01 — Documentation Restructuring (22 tasks)

### Wave 1: Preparation Tasks

#### TASK_001_T11_create_folder_structure ✅ APPROVED
- **Semantic targets:** Valid directories to create under docs/
- **Dependencies:** None (correct)
- **Scope:** Single responsibility - directory structure only
- **Risk:** Low

#### TASK_002_T12_extract_inventory_from_spec ✅ APPROVED
- **Dependencies:** TASK_001 (correct order)
- **Scope:** Analysis task, outputs to .ai/tmp/
- **Risk:** Low

#### TASK_003_T13_build_migration_map ✅ APPROVED
- **Dependencies:** TASK_002 (correct order)
- **Scope:** Planning artifact
- **Risk:** Low

#### TASK_004_T14_create_high_risk_checklist ✅ APPROVED
- **Dependencies:** TASK_003 (correct order)
- **Scope:** Planning artifact
- **Risk:** Low

### Wave 2: Core API Domain Migration

Tasks TASK_005 through TASK_015 are **APPROVED** for parallel execution with proper dependencies on TASK_003:
- TASK_005: overview.md and data-flow.md
- TASK_006: auth-api.md
- TASK_007: dashboards-api.md
- TASK_008: processing-api.md
- TASK_009: admin-api.md
- TASK_010: health-api.md
- TASK_011: backend architecture docs
- TASK_012: frontend architecture docs
- TASK_013: security docs
- TASK_014: database docs
- TASK_015: deployment docs

**Validation Note:** All 11 tasks are independent documentation tasks with parallel execution correctly specified.

### Wave 3: SPEC.md Conversion + README Creation

#### TASK_016_T41_convert_spec_to_overview ⚠️ REQUIRES REVISION
- **Issue:** Depends on 11 tasks individually creating tight coupling
- **Recommendation:** Depend on wave completion marker instead of individual tasks

#### TASK_017_T42_create_docs_readme ⚠️ REQUIRES REVISION
- **Issue:** Same tight coupling pattern as TASK_016

### Wave 4: Cross-Linking + Frontmatter

#### TASK_018_T51_add_yaml_frontmatter ✅ APPROVED
- **Dependencies:** Both TASK_016 and TASK_017 (correct)

#### TASK_019_T52_add_cross_links ✅ APPROVED
- **Dependencies:** TASK_018 (correct)

#### TASK_020_T53_integrate_standalone_docs ✅ APPROVED
- **Dependencies:** TASK_018 (correct)
- **Scope:** Integrates existing docs (SWAGGER_README.md, RUN.md)

### Wave 5: Validation + Cleanup

#### TASK_021_T61_reconciliation_pass ✅ APPROVED
#### TASK_022_T62_frontmatter_consistency_check ✅ APPROVED
#### TASK_023_T63_final_structure_verification ✅ APPROVED

---

## PLAN_02 — Authorization Phase (11 tasks)

### Wave 1: Backend Model/Type Changes

#### TASK_024_A01_add_display_name_to_userread ✅ APPROVED
- **Semantic target:** `UserRead` class in `src/mkobi/models/user.py` **CONFIRMED**
- **Current code:** UserRead class exists (lines 42-59) with `id`, `email`, `role`, `created_at`
- **Change type:** Add computed field - **SAFE**
- **Dependencies:** None (correct)
- **Risk:** Low - computed field doesn't require DB migration

#### TASK_025_A02_add_token_with_user_response_model ✅ APPROVED
- **Semantic target:** After `Token` class in `src/mkobi/models/auth.py` **CONFIRMED**
- **Current code:** Token class exists (lines 77-91)
- **Change type:** Add new model - **SAFE**
- **Dependencies:** None (correct)
- **Risk:** Low

### Wave 2: Backend Service/Route Logic

#### TASK_026_B01_admin_bypass_dashboard_listing ✅ APPROVED
- **Semantic targets:** 
  - `DashboardRepository.get_by_user` **CONFIRMED** (exists, lines 57-85)
  - `DashboardService.get_user_dashboards` **CONFIRMED** (exists, lines 218-240)
  - `DashboardService.get_dashboard` **CONFIRMED** (exists, lines 136-193)
  - `get_my_dashboards_endpoint` in `src/mkobi/api/routes/dashboards.py`
- **Dependencies:** None (correct - parallel with other wave 2 tasks)
- **Risk:** Medium - touches multiple layers

#### TASK_027_B02_registration_request_validation ⚠️ REQUIRES REVISION
- **Semantic target:** `AuthService.register_request` **CONFIRMED** (exists, lines 364-445)
- **Issue:** Current implementation order is:
  1. Blocked domain check (lines 393-401)
  2. Existing request check (lines 407-415)
- **Task requirement:** Existing request check BEFORE blocked domain check
- **Issue:** Task description conflicts with stated goals - blocked domain message needs update before existing request check is moved
- **Required Fix:** Clarify implementation order and message update timing

#### TASK_028_B03_login_response_includes_user ✅ APPROVED
- **Dependencies:** TASK_024, TASK_025 (correct)
- **Semantic targets:** 
  - `AuthService.login_user` **CONFIRMED** (lines 174-211)
  - `_handle_login`, `login`, `login_form` in auth.py **CONFIRMED** (lines 38-107)
- **Risk:** Medium - modifies return format

#### TASK_029_B04_403_for_unauthorized_dashboard_access ✅ APPROVED
- **Dependencies:** TASK_026 (correct - depends on admin bypass implementation)
- **Semantic targets:** 
  - `DashboardService.get_dashboard` **CONFIRMED**
  - `get_dashboard_endpoint` in dashboards.py
- **Risk:** Medium - security-sensitive change

### Wave 3: Frontend Changes

#### TASK_030_C01_update_frontend_login_for_user_response ✅ APPROVED
- **Dependencies:** TASK_028 (correct)
- **Semantic targets:** 
  - `AuthResponse` interface **CONFIRMED** (already has `user` field, lines 31-35)
  - `UserProfile` interface **CONFIRMED** (needs display_name)
  - `useAuth` hook **CONFIRMED**
- **Risk:** Low - frontend verification

#### TASK_031_C02_restructure_routes_move_login_outside_layout ✅ APPROVED
- **Semantic targets:** `AppRoutes` component **CONFIRMED** (routes.tsx, lines 15-77)
- **Current structure:** /login and /register are inside AppLayout (lines 18-20)
- **Dependencies:** None (correct)
- **Risk:** Medium - routing changes

#### TASK_032_C03_update_header_navigation ✅ APPROVED
- **Semantic targets:** `Header` component **CONFIRMED** (Header.tsx, lines 5-34)
- **Current:** Shows email, Profile, Admin (for admins), Logout
- **Required change:** Remove email and Logout, keep Profile (rightmost), Admin (left of Profile)
- **Dependencies:** None (correct)
- **Risk:** Low

#### TASK_033_C04_add_display_name_to_profile_page ✅ APPROVED
- **Dependencies:** TASK_024 (correct)
- **Semantic targets:** `UserProfile` component **CONFIRMED** (UserProfile.tsx, lines 9-132)
- **Risk:** Low

#### TASK_034_C05_update_register_form_success_message ✅ APPROVED
- **Semantic targets:** 
  - `RegisterForm` component **CONFIRMED**
  - `registerRequest` function in authApi.ts
- **Dependencies:** None (correct) - parallel with backend TASK_027
- **Risk:** Low

---

## DEPENDENCY VALIDATION RESULTS

### DAG Integrity ✅
No circular dependencies detected. All dependency chains are valid.

### Cross-Plan Independence ✅
PLAN_01 (docs/) and PLAN_02 (src/mkobi/, frontend/src/) are completely file-system independent.

### Wave Execution Validation
| Wave | Parallel Tasks | Shared Files | Risk |
|------|---------------|--------------|------|
| PLAN_01 Wave 1 | Sequential | None | Low |
| PLAN_01 Wave 2 | Parallel | None (docs only) | Low |
| PLAN_02 Wave 1 | Parallel | None | Low |
| PLAN_02 Wave 2 | Sequential | Multiple | Medium |
| PLAN_02 Wave 3 | Sequential | None | Low |

---

## SEMANTIC STABILITY ANALYSIS

### Stable Anchors Confirmed ✅

All semantic targets reference existing code symbols:

| Target | File | Line | Stability |
|--------|------|------|-----------|
| UserRead | user.py | 42 | STABLE |
| Token | auth.py | 77 | STABLE |
| DashboardRepository.get_by_user | dashboard_repo.py | 57 | STABLE |
| DashboardService methods | dashboard_service.py | 136, 218 | STABLE |
| AuthService.register_request | auth_service.py | 364 | STABLE |
| AuthService.login_user | auth_service.py | 174 | STABLE |
| AppRoutes | routes.tsx | 15 | STABLE |
| Header | Header.tsx | 5 | STABLE |
| UserProfile | UserProfile.tsx | 9 | STABLE |
| useAuth | useAuth.ts | 6 | STABLE |
| AuthResponse, UserProfile types | api.types.ts | 8, 31 | STABLE |

### No Line-Based Anchors ✅

All targets use symbol-level referencing.

---

## REJECTED Tasks

### REJECTED: TASK_027_B02_registration_request_validation

**Rejection Reason:** Implementation order conflict with stated acceptance criteria

1. **Current Code Analysis:**
   - Lines 393-401: Blocked domain check happens FIRST
   - Lines 407-415: Existing request check happens SECOND
   
2. **Task Requirement Conflict:**
   - Task description says: "check existing registration request BEFORE checking blocked domain"
   - Acceptance criteria requires: "Blocked domain → 'This email domain is not allowed for registration'"
   - But the error message for blocked domain uses `email_domain` variable that's set at line 391

3. **Unsafe Implementation Risk:**
   - Moving existing request check before blocked domain check requires careful handling
   - The duplicate check needs to differentiate by status (pending/approved vs rejected)
   - Current code doesn't have status differentiation logic

4. **Missing Implementation Detail:**
   - Task doesn't specify what `UserRegistrationRequest` model contains for status field
   - Acceptance criteria mentions status values but they're not validated against code

**Required Fixes Before Reconsideration:**
- Analyze current `RegistrationRequest` model for status field
- Add status differentiation logic (pending/approved vs rejected)
- Clarify exact error message for each status
- Specify exact location and implementation pattern for status check

---

## TASKS REQUIRING REVISION

### TASK_016_T41_convert_spec_to_overview
- **Issue:** Too many individual dependencies (11 tasks) creates fragile ordering
- **Required Fix:** Either depend on a wave-level marker or accept that partial documentation is acceptable

### TASK_017_T42_create_docs_readme  
- **Issue:** Same over-coupling pattern as TASK_016
- **Required Fix:** Same recommendation

### TASK_027_B02_registration_request_validation
- **Issue:** See rejection section above
- **Required Fix:** Address implementation order conflicts

---

## ROLLOUT CONSISTENCY VALIDATION

| Task ID | File Impact | Dependency Chain | Rollout Safety |
|---------|-------------|------------------|----------------|
| TASK_024 | models/user.py | None | ✅ Safe |
| TASK_025 | models/auth.py | None | ✅ Safe |
| TASK_026 | 3 files | None | ⚠️ Medium - multiple files |
| TASK_027 | auth_service.py | None | ⚠️ Medium - order conflict |
| TASK_028 | 2 files | TASK_024, TASK_025 | ✅ Safe |
| TASK_029 | 2 files | TASK_026 | ✅ Safe |
| TASK_030 | 2 files | TASK_028 | ✅ Safe |
| TASK_031 | routes.tsx | None | ✅ Safe |
| TASK_032 | Header.tsx | None | ✅ Safe |
| TASK_033 | UserProfile.tsx | TASK_024 | ✅ Safe |
| TASK_034 | 2 files | None | ✅ Safe |

---

## ARCHITECTURAL SAFETY ASSESSMENT

### Layer Boundaries Preserved ✅
All PLAN_02 tasks follow Clean Architecture:
- Models (TASK_024, TASK_025) - API layer
- Services (TASK_027, TASK_028) - Business logic layer  
- Repositories (TASK_026) - Data layer
- Routes (TASK_029) - API layer integration

### No Architecture-Breaking Changes ✅
All changes are additive or modifying within existing boundaries.

---

## REQUIRED CORRECTIONS

1. Rename rejected task file:
   - `TASK_027_B02_registration_request_validation.yaml` → `TASK_027_B02_REJECTED.yaml`

2. Update rejected task file with rejection reason

3. Revise TASK_016, TASK_017 to reduce dependency coupling

---

## STALE ASSUMPTIONS

None detected. All targets exist in current codebase.

---

## EXECUTION READINESS

### Ready for Implementation (28 tasks)
All non-rejected tasks have:
- Valid semantic anchors
- Correct dependency ordering
- Clear acceptance criteria
- Appropriate risk assessment

### Hold for Corrections (6 tasks)
- 1 rejected task (TASK_027_B02)
- 2 tasks requiring revision (TASK_016, TASK_017)
- 3 tasks depend on revised tasks

---

*End of Validation Report*
*Validated 34 tasks against current codebase state*
*Next validation number: 003*