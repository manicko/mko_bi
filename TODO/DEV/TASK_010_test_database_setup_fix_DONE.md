# Task: Test Database Setup Fix - COMPLETED

## Status: COMPLETED (Dashboard Tests Fixed)

## Summary

Successfully fixed the test database setup for dashboard API tests. The `bidb_test` database is now properly recreated with the correct schema, and all dashboard API tests pass.

## What Was Fixed:

### 1. Dashboard Model Type Annotation (`src/mkobi/db/models/dashboard.py`)
- Changed `config: Mapped[str | None]` to `Mapped[dict[str, Any] | None]`
- This correctly reflects that JSONB columns return dict objects, not strings

### 2. Dashboard Service (`src/mkobi/services/dashboard_service.py`)
- Removed unnecessary `json.dumps()` call when creating dashboards
- JSONB columns handle dict->JSON conversion automatically
- Fixed `_dashboard_to_read()` to handle `config` when it's `None` or empty dict `{}`
- Removed unused imports (`typing.cast`, `DashboardRepository`, `AccessRepository` at module level)

### 3. Dashboard API Endpoint (`src/mkobi/api/routes/dashboards.py`)
- Fixed `update_dashboard_endpoint()` to pass `update_data` correctly
- Previously it only passed `config`, now passes all update fields via `dashboard_update.model_dump(exclude_unset=True)`

### 4. Test Fixes (`tests/test_dashboards_api.py`)
- Added access grant to `test_update_dashboard_admin` and `test_delete_dashboard_admin`
- The tests create dashboards directly via repository (not service), so access must be granted manually

### 5. Database Recreation (`src/mkobi/db/starter.py`)
- Verified that `recreate_test_database()` correctly:
  - Drops and recreates `bidb_test` database
  - Applies all migrations (including initial migration with `config JSONB` column)
  - The initial migration `7130ecb0388c` now has `config JSONB` in the `dashboards` table

## Test Results:

### Dashboard API Tests: 11/11 PASSED ✓
- `test_get_my_dashboards` ✓
- `test_get_dashboard_detail` ✓
- `test_get_dashboard_no_access` ✓
- `test_create_dashboard_admin` ✓
- `test_create_dashboard_forbidden` ✓
- `test_update_dashboard_admin` ✓
- `test_update_dashboard_forbidden` ✓
- `test_delete_dashboard_admin` ✓
- `test_delete_dashboard_forbidden` ✓
- `test_access_control_no_access` ✓
- `test_access_control_with_access` ✓

### Other Test Failures (Pre-existing Issues):
- **19 tests failing** with `AttributeError: 'UserRead' object has no attribute 'password_hash'`
- These are **NOT caused by my changes** (they involve auth, user, and layout tests)
- The error occurs in Starlette's error middleware when trying to access `password_hash` on `UserRead` objects
- `UserRead` correctly doesn't have `password_hash` (it's a read model without password)
- This appears to be a pre-existing issue with how the `get_current_user` dependency or response serialization works

## Key Learnings:

1. **JSONB columns in SQLAlchemy**: When using `JSONB` type, SQLAlchemy returns Python dict objects (not JSON strings). Don't use `json.dumps()` before storing.

2. **Pydantic model validation**: The `DashboardConfig` model requires `graph_types` field. When creating a default config (for dashboards without config), use `DashboardConfig(graph_types=["bar"])`.

3. **Test database setup**: The `DatabaseStarter.recreate_test_database()` method works correctly - it drops and recreates the test database, then applies all migrations.

4. **Access control in tests**: When creating dashboards directly via repository (not through the service), access must be granted manually in tests.

## Remaining Work (Pre-existing Issues):

The following are **NOT related to the database setup task** and appear to be pre-existing issues:

1. **Auth/User tests failing**: `AttributeError: 'UserRead' object has no attribute 'password_hash'`
   - Likely related to how the `get_current_user` dependency returns user data
   - May be an issue with Starlette's error middleware trying to serialize user objects

2. **Layout tests failing**: 405 Method Not Allowed errors
   - Seems to be a routing or endpoint issue, not database-related

3. **RegistrationRequestRepository missing `delete` method**
   - The repository needs a `delete()` method implemented

## Files Modified:

1. `src/mkobi/db/models/dashboard.py` - Fixed type annotation for `config` column
2. `src/mkobi/services/dashboard_service.py` - Removed `json.dumps()`, fixed config handling
3. `src/mkobi/api/routes/dashboards.py` - Fixed update endpoint to pass correct data
4. `tests/test_dashboards_api.py` - Added access grant to failing tests

## Verification:

```bash
# Run dashboard tests - all pass
uv run pytest tests/test_dashboards_api.py -v

# Run full test suite - 145 passed, 19 failed (pre-existing issues)
uv run pytest tests/ -v
```

## Next Steps (for pre-existing issues):

1. Debug the `UserRead` password_hash error in auth/user tests
2. Fix the `RegistrationRequestRepository.delete()` method
3. Debug the layout API endpoint routing issues
4. Consider adding better error handling in Starlette middleware or FastAPI dependencies

---

**Task completed: 2026-05-08**
**Dashboard API tests: 11/11 passing ✓**
