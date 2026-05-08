---
### TASK: Fix linter issues (unused imports, undefined names)
FILE: alembic/versions/*.py, src/mkobi/api/deps.py, src/mkobi/api/routes/*.py, src/mkobi/core/permissions.py, src/mkobi/data/processing/transformations.py
GOAL: Fix all linter errors found by `uv run ruff check .`
ISSUES FOUND:
1. **F401**: Unused imports (`sqlalchemy`, `typing.cast`, `re`, etc.)
2. **F821**: Undefined name `UUID` in `deps.py`
3. **F841**: Local variable `filters_dict` assigned but never used
4. **E402**: Module level import not at top of file in `setup_test_db.py`
5. **F811**: Redefinition of unused imports in `dashboard_service.py` (backward compatibility wrappers)
IMPLEMENTATION:
* Run `uv run ruff check .` to see all errors
* Fix unused imports by removing them
* Fix undefined names by adding proper imports
* Fix redefinition issues by reorganizing imports
LOGIC:
1. Run linter: `uv run ruff check .`
2. Fix each error category:
   - Remove unused imports (F401)
   - Add missing imports (F821)
   - Remove unused variables (F841)
   - Reorganize module-level imports (E402)
3. Run `uv run ruff check .` to verify fixes
4. Run `uv run pytest tests/test_dashboards_api.py -v` to ensure no regressions
DONE:
* [ ] All F401 errors fixed
* [ ] All F821 errors fixed
* [ ] All F841 errors fixed
* [ ] All E402 errors fixed
* [ ] All F811 errors fixed
* [ ] `uv run ruff check .` passes with no errors
* [ ] All dashboard tests still pass
---
