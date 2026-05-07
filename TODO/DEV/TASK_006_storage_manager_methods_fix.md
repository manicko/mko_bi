---
## TASK: Fix StorageManager Missing Methods
---

### PROBLEM

Tests in `tests/test_storage_manager.py` are failing with:
```
AttributeError: 'StorageManager' object has no attribute 'clear_graph_data'
AttributeError: 'StorageManager' object has no attribute 'clear_dashboard_data'
```

### FILES TO CHECK

- `src/mkobi/data/storage/manager.py`
- `tests/test_storage_manager.py`

### ROOT CAUSE

The `StorageManager` class is missing the methods `clear_graph_data()` and `clear_dashboard_data()` that are being tested.

### SOLUTION

1. Check the test file to understand expected method signatures
2. Implement the missing methods in `StorageManager`:
   - `clear_graph_data(graph_id, db)` - should delete aggregated data for a specific graph
   - `clear_dashboard_data(dashboard_id, db)` - should delete all aggregated data for a dashboard
3. Follow existing patterns in the class for database operations

### VERIFICATION

1. Run `uv run pytest tests/test_storage_manager.py -v`
2. All tests should pass

### PRIORITY

Medium - blocks storage manager tests

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests passing

---
