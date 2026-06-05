---
name: 01-backend-findings
description: Backend architecture audit findings
agent: audit-executor
alwaysApply: false
---

# Phase 01 Audit Findings — Backend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### BE-001: Missing Response Model on Filter Values Endpoint

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/filter_values.py |
| **Classification** | advisory |

**Description:** The `/api/v1/dashboards/{dashboard_id}/filter-values` endpoint returns `dict[str, Any]` instead of using a Pydantic response model. The frontend has a properly typed `FilterValuesResponse` interface in `frontend/src/shared/types/api.types.ts`, but the backend does not use a corresponding Pydantic model. This breaks type safety on the API boundary and prevents OpenAPI schema generation for this endpoint.

**Evidence:** `src/mkobi/api/routes/filter_values.py:42`
```python
async def get_filter_values_endpoint(...) -> dict[str, Any]:
```
The route returns `dict[str, Any]` and manually constructs `{"filter_name": filter_name, "values": values}`. Compare with frontend type:
```typescript
export interface FilterValuesResponse {
  filter_name: string
  values: string[]
}
```

**Recommendation:** Create a `FilterValuesResponse` Pydantic model in `src/mkobi/models/data.py` and use it as the `response_model` for this endpoint. This ensures type consistency between frontend and backend, enables OpenAPI schema generation, and maintains data validation.

---

### BE-002: Test Failure - JWT Secret Validation Test Expectation Misaligned with Environment

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | tests/test_config.py, .env |
| **Classification** | mandatory |

**Description:** The test `test_none_jwt_secret_accepted` expects `settings.jwt.secret_key` to be `None` when the `JWT__SECRET_KEY` environment variable is deleted. However, the `.env` file at the project root contains `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`, and this value is loaded via pydantic-settings' dotenv mechanism. The test deletes the environment variable but does not clear the cache or prevent `.env` loading, causing the test to receive the `.env` value instead of `None`.

**Evidence:** 
- `tests/test_config.py:377-381` - Test deletes env var but doesn't account for `.env` loading
- `.env:15` - Contains `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`
- `src/mkobi/config.py:382` - `model_config` includes `"env_file": ".env"`

**Recommendation:** The test should either:
1. Delete the environment variable AND clear the config cache before creating Settings, OR
2. Mock the `.env` file to ensure it doesn't interfere, OR
3. Update the test expectation to match the actual behavior (`.env` provides a value)

---

### BE-003: Test Failure - File Extension Validation Order

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_data_service.py, src/mkobi/services/file_processing.py |
| **Classification** | advisory |

**Description:** The test `test_validate_file_invalid_extension` expects MIME-type validation to occur before extension checking (to verify `text/plain` detection for `.txt` files). However, on systems without `python-magic` (like Windows without libmagic), the fallback detection in `detect_mime_type_from_content` returns `text/csv` for CSV-like content (contains commas and newlines) rather than `text/plain`. This causes the extension check to fail first, not the MIME check, breaking the test's assumption.

**Evidence:**
- `tests/test_data_service.py:552-576` - Test expects MIME error before extension error
- `src/mkobi/services/file_processing.py:40-64` - Fallback MIME detection logic that returns `text/csv` for CSV-like content
- Error message shows: `Invalid file format: 'test.txt'. Allowed formats: csv.gz, csv`

**Recommendation:** Update the test to account for platform differences in MIME detection, or mock the detection to ensure consistent behavior across platforms. Consider whether the fallback detection is correct - small CSV content should arguably be `text/csv` given its structure.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 1 |

## Mandatory Fixes

- BE-002: Test failure - JWT secret validation test expectation misaligned with .env loading behavior

## Advisory Recommendations

- BE-001: Missing response model on filter values endpoint (breaks type safety)
- BE-003: Test failure - file extension validation order (platform-specific test issue)

---

## Architectural Observations (No Issues Found)

The following areas were verified and found to be compliant with spec:

1. **Clean Architecture Layers** - Properly separated: API routes call services, services call repositories, no layer bleeding detected
2. **StrEnum for Constants** - All enums in `src/mkobi/models/enums.py` properly use `StrEnum`
3. **Error Handling** - RFC 7807 format implemented via `AppException` and `ErrorResponse` in `src/mkobi/utils/exceptions.py`
4. **Security** - JWT + bcrypt implemented, rate limiting via Redis, MIME-type detection from content
5. **Type Hints** - All public functions have type hints, no `print()` statements found
6. **No Raw SQL** - No f-string SQL queries found in codebase
7. **English Only** - All comments, logs, and error messages are in English
8. **Dependency Injection** - Proper DI pattern with `Depends()` in API routes and interfaces in `src/mkobi/interfaces/`
9. **Temporary File Cleanup** - Cleanup logic exists in `src/mkobi/workers/data_worker.py` and upload routes