# Bug Report: Dashboard Create Endpoint Missing Admin Authorization

**Date:** 2026-06-17
**Severity:** HIGH
**Status:** REPORTED
**Related Test Failure:** test_create_dashboard_forbidden in test_dashboards_api.py

## Problem

The `create_dashboard_endpoint` in `src/mkobi/api/routes/dashboards_crud.py` is missing the `AdminUser` dependency, allowing non-admin users to create dashboards when they should be forbidden.

## Evidence

### Test Failure
```
tests/test_dashboards_api.py::TestCreateDashboard::test_create_dashboard_forbidden FAILED
```

### Current Implementation
```python
# src/mkobi/api/routes/dashboards_crud.py:47-61
@router.post("/", response_model=DashboardRead, ...)
async def create_dashboard_endpoint(
    dashboard_data: DashboardCreate,
    current_user: CurrentUser,  # Should be AdminUser
    db: AsyncSession = Depends(get_db_dependency),
    ...
) -> DashboardRead:
```

The endpoint uses `CurrentUser` instead of `AdminUser`, allowing any authenticated user to create dashboards.

### Expected Implementation
Following the same pattern as user management endpoints in `admin.py` and `users.py`:
```python
async def create_dashboard_endpoint(
    dashboard_data: DashboardCreate,
    admin_user: AdminUser,  # Required for admin-only operation
    db: AsyncSession = Depends(get_db_dependency),
    ...
) -> DashboardRead:
```

## Analysis

This is the same authorization issue that was fixed for user management endpoints:
- `admin.py`: Fixed to use `AdminUser` for `/users/{user_id}/role`, `/users/{user_id}/active`, `/users/{user_id}`, and `/users` endpoints
- `users.py`: Fixed to use `AdminUser` for `/{user_id}` (PUT), `/{user_id}` (DELETE), and `/` (POST) endpoints
- `dashboards_crud.py`: Still uses `CurrentUser` for `/` (POST) endpoint - **BUG**

## Resolution

The `create_dashboard_endpoint` should use `AdminUser` as its dependency instead of `CurrentUser`. This requires:
1. Adding `AdminUser` import from `mkobi.api.deps`
2. Changing parameter from `current_user: CurrentUser` to `admin_user: AdminUser`

## Related

- Task: TASK_060_int019_add_admin_user_management_test.yaml
- Similar fixes made to: admin.py, users.py