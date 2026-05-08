---
### TASK: Fix unrelated test failures

FILE: src/mkobi/models/user.py, src/mkobi/api/layouts.py, src/mkobi/db/repositories/registration_request_repo.py

GOAL: Fix test failures unrelated to storage manager unique constraint task

ISSUES FOUND:

1. **UserRead model missing password_hash attribute**
   - Error: `AttributeError: 'UserRead' object has no attribute 'password_hash'`
   - Files: `src/mkobi/models/user.py`, `tests/test_auth.py`, `tests/test_users_api.py`
   - Cause: Pydantic model doesn't include `password_hash` field that tests expect

2. **Layout API returns 405 Method Not Allowed**
   - Error: `assert 405 == 403` or `assert 405 == 201` etc.
   - File: `src/mkobi/api/layouts.py`
   - Cause: API endpoints may have incorrect HTTP methods or routing configuration

3. **Dashboard API returns 403 Forbidden for admin operations**
   - Error: `assert 403 == 200`, `assert 403 == 204`
   - File: `src/mkobi/api/dashboards.py`
   - Cause: Permission/authentication issues for admin operations

4. **RegistrationRequestRepository missing delete method**
   - Error: `AttributeError: 'RegistrationRequestRepository' object has no attribute 'delete'`
   - File: `src/mkobi/db/repositories/registration_request_repo.py`
   - Cause: Repository doesn't implement required `delete` method

IMPLEMENTATION:

1. Fix UserRead model to include or exclude `password_hash` appropriately
2. Fix Layout API routing/HTTP methods
3. Fix Dashboard API permissions for admin operations
4. Add `delete` method to RegistrationRequestRepository

TESTING:
- [ ] `uv run pytest tests/test_auth.py -v`
- [ ] `uv run pytest tests/test_users_api.py -v`
- [ ] `uv run pytest tests/test_layouts.py -v`
- [ ] `uv run pytest tests/test_dashboards_api.py -v`

PRIORITY: Medium

NOTE: These issues were discovered during task 21_storage_manager_unique_constraint but are unrelated to the UPSERT fix.
