---
## TESTING & QUALITY
---

### TASK: Improve test coverage for API endpoints

FILES: `tests/`

**PROBLEM**: 
Current test files mainly cover dashboard API. Need to improve coverage for:
1. Auth endpoints (login, register-request, me)
2. Upload endpoints (upload, process, status, result)
3. Data endpoints (aggregated data)
4. Users endpoints (admin and regular user operations)
5. Filters endpoints
6. Graphs endpoints
7. Layouts endpoints
8. Processing configs endpoints
9. Processing logs endpoints
10. Admin endpoints (registration requests approval/rejection)

**CURRENT TEST FILES**:
- `test_auth.py` - exists, needs review
- `test_dashboards_api.py` - good coverage
- `test_filters.py` - exists, needs review
- `test_graphs.py` - exists, needs review
- `test_layouts.py` - exists, needs review
- `test_processing_logs.py` - exists, needs review
- `test_users_api.py` - exists, needs review
- `test_upload_api.py` - exists, needs review
- `test_pydantic_models.py` - exists
- `test_repositories.py` - exists
- `test_security.py` - exists
- `test_config.py` - exists

**IMPLEMENT**:
1. Review existing test files for completeness
2. Add missing tests for:
   - Rate limiting behavior
   - Permission checks (403 responses)
   - Input validation (422 responses)
   - Error handling (500 responses)
   - File upload edge cases (large files, wrong MIME types)
   - Data processing workflow (upload → process → status → result)
3. Add integration tests for complete ETL flow
4. Add frontend tests (if not present)
5. Aim for >80% code coverage

**COMMANDS**:
```bash
# Run tests with coverage
uv run pytest tests/ --cov=src/mkobi --cov-report=html

# Check specific endpoint coverage
uv run pytest tests/test_upload_api.py -v
```

**REFERENCES**:
- `tests/` directory
- SPEC.md for expected endpoint behavior

**DONE**:
- [ ] All API endpoints have test coverage
- [ ] Edge cases tested
- [ ] Integration tests added
- [ ] Code coverage >80%
- [ ] Frontend tests added (if applicable)
