---
## TASK: Fix repository instance methods vs classmethods inconsistency
---

### PROBLEM

Several repository classes have inconsistent method definitions. Some methods are defined as `@classmethod` but are being called as instance methods (or vice versa). This causes `TypeError: missing 1 required positional argument: 'self'` errors.

Errors observed:
```
TypeError: AccessRepository.get_user_dashboards() missing 1 required positional argument: 'db'
TypeError: LayoutRepository.create() missing 1 required positional argument: 'self'
TypeError: DashboardRepository.create() missing 1 required positional argument: 'self'
```

### ROOT CAUSE

The repository pattern in this project uses instance methods (with `self`) based on the `IRepository` interface and how services like `DashboardService` and `UserService` use them. However, some repository implementations use `@classmethod` decorator incorrectly.

### FILES TO CHECK

- `src/mkobi/db/repositories/access_repo.py` - `get_user_dashboards()` method
- `src/mkobi/db/repositories/layout_repo.py` - `create()` method
- `src/mkobi/db/repositories/dashboard_repo.py` - `create()` method
- All other repository files for similar issues

### SOLUTION

1. Remove `@classmethod` decorators from repository methods
2. Change method signatures from `cls` to `self`
3. Update method calls to use instance methods (already done in services via DI)

### VERIFICATION

1. Run `uv run pytest tests/test_repositories.py -v`
2. Check that all repository tests pass
3. Run `uv run mypy src/mkobi/db/repositories/`

### PRIORITY

Medium - affects repository layer functionality

### STATUS

- [ ] Issue identified
- [ ] Fix applied to all affected repositories
- [ ] Tests pass
- [ ] mypy and ruff checks pass

---
