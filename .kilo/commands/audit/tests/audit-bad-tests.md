---
name: audit-bad-tests
description: audit-bad-tests
agent: auditor
alwaysApply: false
---

# Objective

Identify tests that do not match the current architecture and style of the production code, especially if they force changes to production code to satisfy tests rather than the other way around.

## Bad Test Indicators (subject to deletion or complete rewrite):

### Architecture / Contract Mismatch
- Use `sync` instead of `async`/`await` (mkobi uses async SQLAlchemy throughout)
- Call deprecated methods, functions, or settings
- Violate the current layer separation (API → Service → Repository)
- Use `pandas` instead of `polars` (pandas is forbidden in mkobi)
- Test against old response shapes (e.g., login returning only `{access_token}` instead of `TokenWithUser` with `user` + `display_name`)
- Reference removed or renamed StrEnum classes (e.g., old enum names)
- Test for `print()` output instead of logger calls

### No Business Logic Verification
- Only verify object creation or HTTP status codes (e.g., `assert response.status_code == 200` with no body checks)
- Verify method calls instead of business rules
- Mock completely replaces business logic
- Assertions check mock values, not real results
- Don't verify side effects (DB state, processing_logs entries, temp file cleanup)

### Weak Coverage & Low Value
- Ignore negative scenarios and boundary conditions
- Use minimal/artificial data instead of realistic data
- Don't verify DB state, logs, or side effects after execution
- Superficial tests ("field exists", "function doesn't crash")
- `assert True` or no `assert` at all
- `assert result is None` without verifying WHY it's None

### Quality & Maintenance Problems
- Redundant and duplicate tests
- Depend on test execution order
- Strongly coupled to internal implementation (fragile)
- Excessive mocking where test DB or real dependencies would suffice
- Don't use pytest fixtures from `conftest.py` (duplicate fixture definitions)
- Don't use `pytest.mark.asyncio` for async tests

### mkobi-Specific Anti-Patterns
- Tests that don't verify JSONB normalization (dims key sorting)
- Tests that don't verify `display_name` is computed from email prefix
- Tests that don't verify `TokenWithUser` response shape (token + user profile)
- Tests that don't verify admin bypass for dashboard access
- Tests that don't verify 403/404 dual-signal behavior
- Tests that don't verify rate limiting (fail-open/fail-closed)
- Tests that don't verify temp file cleanup after processing
- Tests that don't verify processing_logs status lifecycle transitions
- Tests that don't verify registration approval flow (temp password generation)
- Tests that don't verify StrEnum values match PostgreSQL ENUM types
- Tests that use `unittest.TestCase` instead of pytest style

## Special Attention

- Tests without `assert` or with `assert True` / `assert not None`
- Mocks of repositories/services inside unit tests when test DB would suffice
- Tests that break after architecture refactoring without behavior change
- Tests written for old code version and not updated
- Tests that import from wrong module paths (e.g., old package structure)

**Rule:** If a test requires significant changes to production code just to make the test pass — delete that test.

## Report Format

Create file: `.ai/audit/tests/audit_report_<number>.md` (next available number)

| FilePath | TestName (function name) | Problem | Recommendation |
|----------|------------------------|---------|----------------|
| tests/test_auth.py | test_login_old_response | Checks only `{access_token}`, not `TokenWithUser` with `display_name` | Rewrite to verify full response shape |
| tests/test_processing.py | test_process_uses_pandas | Imports pandas instead of polars | Delete — violates mkobi tech stack |
| tests/test_upload.py | test_no_assert | Has no assert statement | Delete or add meaningful assertions |
