TASK: Fix remaining test files

FILE: tests/test_new_models.py, tests/test_data_processing.py, tests/test_pydantic_models.py, tests/test_storage_manager.py, tests/services/test_data_service.py

GOAL: Fix syntax errors and update enum usages in test files

IMPLEMENT:

1. Fix syntax errors in `test_new_models.py` (broken by fix script)
2. Update `AggregationFunctionEnum` member names from lowercase to uppercase:
   - `sum_val` → `SUM`
   - `mean` → `MEAN`
   - `count_val` → `COUNT`
   - `min_val` → `MIN`
   - `max_val` → `MAX`
   - `median` → `MEDIAN`
   - `std` → `STD`
   - `var` → `VAR`
   - `first` → `FIRST`
   - `last` → `LAST`

3. Remove remaining `config={}` from Dashboard creations in test files

4. Update enum string values to enum members:
   - `type="select"` → `type=FilterType.SELECT`
   - `type="multiselect"` → `type=FilterType.MULTISELECT`
   - `type="range"` → `type=FilterType.RANGE`
   - `type="date"` → `type=FilterType.DATE`
   - `permission="view"` → `permission=DashboardPermission.VIEW`
   - `permission="edit"` → `permission=DashboardPermission.EDIT`
   - `permission="admin"` → `permission=DashboardPermission.ADMIN`
   - `status="started"` → `status=ProcessingStatus.STARTED`
   - etc.

LOGIC:

1. Manually fix syntax errors in `test_new_models.py`
2. Use search/replace to update all enum member names
3. Remove all `config={}` occurrences from Dashboard creations
4. Run `uv run pytest tests/ -v` to verify
5. Fix any remaining failures

DONE:

* [ ] All test files have correct enum member names
* [ ] No `config={}` in Dashboard creations
* [ ] All tests pass (or at least the core model tests)
* [ ] `uv run ruff check tests/` passes
* [ ] `uv run mypy tests/` passes (if applicable)
