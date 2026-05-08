# Task: Complete Test Database Setup and Debug Failing Tests

## Status: IN PROGRESS

## Issue Summary

The test database `bidb_test` setup has been modified but tests are still failing:

### What Works:
- `test_create_dashboard_admin` PASSES (POST with `config` data)
- Tests that check ACCESS DENIED pass

### What Fails:
- `test_get_dashboard_detail` - 500 error
- `test_update_dashboard_admin` - 500 error  
- `test_delete_dashboard_admin` - 500 error
- `test_access_control_with_access` - 500 error

### Key Observations:
1. `check_db.py` shows `config` column DOESN'T EXIST in `dashboards` table
2. But `test_create_dashboard_admin` passes (suggesting column exists when test runs)
3. Server logs don't show the actual error (despite adding `exc_info=True`)
4. The `recreate_test_database()` function runs but column may not be created properly

## Changes Made:

1. **conftest.py**:
   - Enabled `DatabaseStarter().recreate_test_database()` in `pytest_sessionstart`
   - Set `RECREATE_TEST_DB = "true"`

2. **starter.py**:
   - Fixed `recreate_test_database()` to connect to `postgres` database for admin operations
   - Fixed `_apply_migrations()` to use `run_sync` correctly
   - Added manual `config` column check/addition after migrations

3. **alembic/versions/7130ecb0388c_true_initial_migration.py**:
   - Added `config JSONB` to `dashboards` table CREATE statement
   - Added `DROP TABLE IF EXISTS dashboards CASCADE` before CREATE

4. **alembic/versions/91f5436a3098_*.py** and **a2b3c4d5e6f7_*.py**:
   - Fixed unique constraint syntax for JSONB columns (using `(dims::text)`)

5. **db/models/dashboard.py**:
   - Changed `config` column from `Text` to `JSONB` type

## Remaining Work:

1. **Debug why `config` column isn't being created**:
   - The migration file has `config JSONB` but `check_db.py` shows it doesn't exist
   - Need to verify the migration is actually being applied to the correct database
   - Check if `alembic_version` table has correct version after recreation

2. **Capture the actual server error**:
   - The 500 errors don't show the actual error in test output
   - Try running tests with `-s` flag and capturing stdout
   - Check if logging config needs adjustment to show ERROR level with traceback

3. **Verify database recreation is working**:
   - Add debug prints to `recreate_test_database()` to verify:
     - Database is being dropped
     - Database is being recreated  
     - Migrations are being applied
     - `config` column exists after migrations

4. **Fix the actual test failures**:
   - Once the `config` column issue is resolved, the 500 errors should be fixed
   - May need to fix the `_dashboard_to_read()` function if it doesn't handle `None` config correctly

## Next Steps:

1. Run `check_db.py` and `alembic_version` check manually
2. Add comprehensive debug output to `recreate_test_database()`
3. Try running a single failing test with `-s -v` and capture ALL output
4. Check if the issue is with migration order or missing migrations
5. Consider manually creating the `dashboards` table with `config` column as a workaround

## Files to Check:

- `C:\py_dev\mkobi\alembic\versions\7130ecb0388c_true_initial_migration.py` - Initial migration with `config` column
- `C:\py_dev\mkobi\src\mkobi\db\starter.py` - Database recreation logic
- `C:\py_dev\mkobi\tests\conftest.py` - Test setup
- `C:\py_dev\mkobi\src\mkobi\services\dashboard_service.py` - `_dashboard_to_read()` function

## Test Command:

```bash
uv run pytest tests/test_dashboards_api.py::TestGetDashboardDetail::test_get_dashboard_detail -v -s 2>&1 | Select-String -Pattern "error|Error|500" -CaseSensitive:$false
```
