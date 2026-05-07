---
## TASK: Fix Repository Instantiation in Tests
---

### PROBLEM

Multiple tests are failing with error:
```
TypeError: DashboardRepository.create() missing 1 required positional argument: 'self'
TypeError: GraphRepository.create() missing 1 required positional argument: 'self'
TypeError: AccessRepository.grant_access() missing 1 required positional argument: 'self'
```

The repository classes are being used as if they were static classes, but they need to be instantiated first since the methods are instance methods.

### FILES TO CHECK

- `tests/test_repositories.py`
- `tests/test_dashboards_api.py`
- `tests/test_upload_api.py` (already fixed)
- `src/mkobi/db/repositories/*.py`

### ROOT CAUSE

The repository pattern requires instantiation before calling instance methods. Tests are calling `ClassName.method()` instead of `instance.method()`.

### SOLUTION

1. Check all repository usage in tests
2. Ensure repositories are instantiated before use: `repo = Repository()` then `repo.method()`
3. Or convert to static methods if that's the intended design (less likely given the interface pattern)

### VERIFICATION

1. Run `uv run pytest tests/test_repositories.py -v`
2. Run `uv run pytest tests/test_dashboards_api.py -v`
3. All tests should pass

### PRIORITY

Medium - blocks multiple test suites

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests passing

---
