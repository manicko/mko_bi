---
## TASK: Fix upload API returning 403 instead of 201
---

### PROBLEM

Upload API endpoints are returning 403 Forbidden instead of 201 Created for authenticated admin users.

Error observed:
```
FAILED tests/test_upload_api.py::TestUploadCSV::test_upload_csv_success - assert 403 == 201
FAILED tests/test_upload_api.py::TestUploadCSV::test_upload_csv_gz_success - assert 403 == 201
```

### ROOT CAUSE

The upload endpoints likely have incorrect permission dependencies or the test client is not properly authenticated with admin role.

### FILES TO CHECK

- `src/mkobi/api/routes/upload.py` - Upload endpoint definitions
- `tests/test_upload_api.py` - Upload API tests
- `src/mkobi/api/deps.py` - Authentication dependencies

### SOLUTION

1. Check upload endpoint dependencies (should require editor role or higher)
2. Verify test client is properly authenticated
3. Check if rate limiting is causing 403 (unlikely for tests with mock)

### VERIFICATION

1. Run `uv run pytest tests/test_upload_api.py -v`
2. Check that upload tests pass
3. Verify authentication works correctly

### PRIORITY

Medium - affects file upload functionality

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests pass

---
