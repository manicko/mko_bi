---
## DATA PROCESSING
---

### TASK: Fix Ruff Linting Issues

FILE: tests/test_users_api.py, test_cors_simple.py, src/mkobi/**/*.py

GOAL: Achieve clean ruff check (0 errors)

IMPLEMENT:

* Fix unused import in tests/test_users_api.py:6
  - `UserRole` imported but unused
* Fix E402 (module level import not at top of file) in test_cors_simple.py
  - File has imports after code execution (lines 11, 22, 23, 25, 35, 46, 56)
  - Either move imports to top or add `# noqa: E402` with justification
* Run `uv run ruff check .` to find any other issues
* Fix all reported errors

LOGIC:

1. Check current ruff status: `uv run ruff check .`
2. Fix unused import in test_users_api.py:
   - Either use the import or remove it
3. Fix E402 errors in test_cors_simple.py:
   - Option A: Move imports to top of file
   - Option B: Add `# noqa: E402` if dynamic import is intentional
   - Option C: Move file to `tests/` directory if it's a test file
4. Run `uv run ruff check . --fix` for auto-fixable issues
5. Manually fix remaining issues
6. Verify: `uv run ruff check .` returns no errors

DONE:

* [ ] Unused import in test_users_api.py fixed
* [ ] E402 errors in test_cors_simple.py fixed
* [ ] All ruff errors fixed
* [ ] Command `uv run ruff check .` passes with 0 errors
* [ ] Tests still pass

---
