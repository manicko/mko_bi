---
## TASK: Fix filter_service import error in filters.py route
---

### PROBLEM

ImportError when loading conftest.py:

```
ImportError: cannot import name 'get_filter' from 'mkobi.services.filter_service' (c:\py_dev\mkobi\src\mkobi\services\filter_service.py)
```

The `src/mkobi/api/routes/filters.py` is trying to import standalone functions (`create_filter`, `get_filter_by_id`, `get_all_filters`, `update_filter`, `delete_filter`) from `mkobi.services.filter_service`, but the `filter_service.py` module contains a `FilterService` class with these as methods, not standalone functions.

### ROOT CAUSE

The filters.py route file expects standalone functions, but the service module was refactored to use a class-based approach (likely as part of the DI/interfaces refactoring).

### FILES TO CHECK

- `src/mkobi/api/routes/filters.py` (lines 25-31)
- `src/mkobi/services/filter_service.py`

### SOLUTION

Either:
1. Update `filters.py` to use the `FilterService` class correctly with dependency injection
2. Or add standalone wrapper functions in `filter_service.py` that use the service class

Based on the project's DI pattern (interfaces, repositories), option 1 is preferred.

### VERIFICATION

1. Run `uv run pytest tests/` 
2. Check that ImportError is resolved

### PRIORITY

High - blocks all tests from running

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests pass

---
