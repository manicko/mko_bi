---
### TASK: Fix UserRead password_hash AttributeError
FILE: src/mkobi/models/user.py, src/mkobi/core/permissions.py, src/mkobi/api/dependencies.py
GOAL: Fix `AttributeError: 'UserRead' object has no attribute 'password_hash'` in auth and user tests
IMPLEMENT:
* Investigate why `password_hash` is being accessed on `UserRead` objects
* Check `get_current_user()` in `permissions.py` - how it returns user data
* Check if Starlette error middleware is trying to serialize user objects incorrectly
* Determine if `UserRead` should have `password_hash` or if code should not access it
LOGIC:
1. Run failing test with `-s` flag to see full traceback
2. Identify where `password_hash` is being accessed on `UserRead`
3. Fix the root cause:
   - Option A: Add `password_hash` to `UserRead` (if needed for some operations)
   - Option B: Remove code that tries to access `password_hash` on `UserRead`
   - Option C: Fix Starlette middleware or response serialization
4. Verify auth tests pass
DONE:
* [ ] Root cause identified
* [ ] Fix implemented
* [ ] `uv run pytest tests/test_auth.py -v` passes
* [ ] `uv run pytest tests/test_users_api.py -v` passes
---
