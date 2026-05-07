---
## TASK: Fix MockPipeline in test configuration
---

### PROBLEM

Tests in `test_upload_api.py` are failing with error:
```
'MockPipeline' object has no attribute 'execute'
```

### ROOT CAUSE

The `MockPipeline` class in `tests/conftest.py` has an `execute` method defined, but the test is still failing. This could be due to:
1. The `execute` method not being properly async
2. The pipeline context manager not working correctly
3. The code in `src/mkobi/core/security.py` using pipeline differently than expected

### FILES TO CHECK

- `tests/conftest.py` (lines 84-105)
- `src/mkobi/core/security.py` (lines 33-51)

### SOLUTION

1. Check how `security.py` uses the pipeline
2. Ensure `MockPipeline.execute()` works correctly
3. May need to update the mock to properly simulate Redis pipeline behavior

### VERIFICATION

1. Run `uv run pytest tests/test_upload_api.py -v`
2. All tests should pass

### PRIORITY

Medium - blocks upload API tests

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests passing

---
