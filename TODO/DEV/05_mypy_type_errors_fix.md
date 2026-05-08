---
## DATA PROCESSING
---

### TASK: Fix MyPy Type Errors

FILE: src/mkobi/**/*.py

GOAL: Reduce MyPy errors from 234 to 0

IMPLEMENT:

* Fix return type errors (Returning Any from function declared to return "...")
* Fix unused "type: ignore" comments
* Fix UUID vs int type mismatches in API routes
* Fix Item "None" has no attribute "get" errors
* Fix Value of type "YoyModeEnum | None" is not indexable
* Fix Attr-defined errors (module does not explicitly export attributes)
* Fix FilterConfigDict has no attribute "model_dump"

LOGIC:

1. Run `uv run mypy .` to get current error list
2. Fix errors by category:
   - **Return type errors**: Add proper type annotations for repository return types
   - **Unused type: ignore**: Remove or fix incorrect type: ignore comments in:
     - dashboard_filter_repo.py
     - processing_config_repo.py
     - filter_repo.py
   - **UUID vs int**: Fix API routes expecting int but receiving UUID
   - **None attribute**: Add None checks before accessing attributes
   - **Enum access**: Fix YoyModeEnum.percent → YoyModeEnum.PERCENT
   - **Attr-defined**: Add explicit exports to __init__.py files
   - **model_dump**: Fix FilterConfigDict type definition

3. Run `uv run mypy .` after each category fix
4. Ensure no new errors introduced

DONE:

* [ ] MyPy errors reduced from 234 to 0
* [ ] Command `uv run mypy .` passes with no errors
* [ ] Tests still pass: `uv run pytest tests/`
* [ ] No new ruff warnings introduced

---

### TASK: Fix Unused Type Ignore Comments

FILE: src/mkobi/db/repositories/dashboard_filter_repo.py, src/mkobi/db/repositories/processing_config_repo.py, src/mkobi/db/repositories/filter_repo.py

GOAL: Remove or fix incorrect `# type: ignore` comments

IMPLEMENT:

* Search for all `# type: ignore` comments
* Verify if ignore is still needed
* Remove if no longer needed
* Fix underlying type issue if ignore was wrong solution

LOGIC:

1. `grep -r "type: ignore" src/mkobi/`
2. For each occurrence:
   - Check if MyPy still reports error without ignore
   - If error gone: remove comment
   - If error exists: fix type issue properly
3. Run `uv run mypy .` to verify

DONE:

* [ ] All unnecessary type: ignore comments removed
* [ ] All remaining type: ignore comments are justified
* [ ] MyPy passes

---
