# Execution Order — PLAN_01: Admin User Password Reset

## Wave 1 — Foundation (Parallel, no dependencies)

| Order | Task ID | Task Name | Files Modified |
|-------|---------|-----------|----------------|
| 001 | TASK_001 | user_model_force_flag | src/mkobi/db/models/user.py |
| 002 | TASK_002 | alembic_migration | alembic/versions/xxxx_add_force_password_change_to_users.py (NEW) |
| 003 | TASK_003 | pydantic_userread_flag | src/mkobi/models/user.py |
| 004 | TASK_004 | iauthservice_interface | src/mkobi/interfaces/service_interfaces.py |

## Wave 2 — Backend Service Logic (depends on Wave 1)

| Order | Task ID | Task Name | Depends On | Files Modified |
|-------|---------|-----------|------------|----------------|
| 005 | TASK_005 | authservice_reset_password | 001, 003, 004 | src/mkobi/services/auth_service.py |
| 006 | TASK_006 | authservice_clear_flag | 001 | src/mkobi/services/auth_service.py |

Note: TASK_005 and TASK_006 can run in parallel (same file, non-overlapping changes).

## Wave 3 — Backend API Endpoints (depends on Wave 2)

| Order | Task ID | Task Name | Depends On | Files Modified |
|-------|---------|-----------|------------|----------------|
| 007 | TASK_007 | admin_reset_endpoint | 005 | src/mkobi/api/routes/admin.py |
| 008 | TASK_008 | approve_sets_force_flag | 006 | src/mkobi/api/routes/admin.py |

Note: TASK_007 and TASK_008 can run in parallel (same file, different locations).

## Wave 4 — Frontend (depends on Wave 1 + Wave 3)

| Order | Task ID | Task Name | Depends On | Files Modified |
|-------|---------|-----------|------------|----------------|
| 009 | TASK_009 | adminapi_reset_function | 003 | frontend/src/features/admin/api/adminApi.ts |
| 010 | TASK_010 | apitypes_force_flag | 003 | frontend/src/shared/types/api.types.ts |
| 011 | TASK_011 | reset_result_dialog | — | frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx (NEW) |
| 012 | TASK_012 | usermanagement_reset_button | 009, 011 | frontend/src/features/admin/ui/UserManagement.tsx |
| 013 | TASK_013 | change_password_force_mode | — | frontend/src/features/users/ui/ChangePasswordPage.tsx |
| 014 | TASK_014 | useauth_force_redirect | 010 | frontend/src/features/auth/model/useAuth.ts |
| 015 | TASK_015 | loginform_force_redirect | 014 | frontend/src/features/auth/ui/LoginForm.tsx |

Note: TASK_009, TASK_010, TASK_011, TASK_013 can run immediately after Wave 1 completes.
TASK_012 needs TASK_009 + TASK_011. TASK_015 needs TASK_014.

## Wave 5 — Verification (depends on all Wave 3 + Wave 4)

| Order | Task ID | Task Name | Depends On | File |
|-------|---------|-----------|------------|------|
| 016 | TASK_016 | verify_phase01 | 007, 008, 012, 013, 014, 015 | Verification task |

## Summary Statistics

- **Total tasks:** 16
- **Implementation tasks:** 15
- **Verification tasks:** 1
- **Parallel waves:** 5
- **Files modified (backend):** 5
- **Files modified (frontend):** 7 (1 new component)
- **New files:** 2 (1 migration, 1 React component)
- **Estimated critical path:** Wave 1 → Wave 2 → Wave 3 → Wave 4 → Wave 5 (5 sequential steps)
