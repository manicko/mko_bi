---
## DATA PROCESSING
---

### TASK: Fix Ruff Linting Issues

FILE: tests/test_users_api.py, src/mkobi/**/*.py

GOAL: Achieve clean ruff check (0 errors)

IMPLEMENT:

* Fix unused import in tests/test_users_api.py:6
  - `UserRole` imported but unused
* Run `uv run ruff check .` to find any other issues
* Fix all reported errors

LOGIC:

1. Check current ruff status: `uv run ruff check .`
2. Fix unused import in test_users_api.py:
   - Either use the import or remove it
3. Run `uv run ruff check . --fix` for auto-fixable issues
4. Manually fix remaining issues
5. Verify: `uv run ruff check .` returns no errors

DONE:

* [ ] Unused import in test_users_api.py fixed
* [ ] All ruff errors fixed
* [ ] Command `uv run ruff check .` passes with 0 errors
* [ ] Tests still pass

---
