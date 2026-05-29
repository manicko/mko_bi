---
name: 06-tests-validated
description: Validated audit findings for test quality (Phase 06)
source: .ai/audit/06-tests/findings.md
validator: validator
---

# Phase 06 Validated Findings — Test Quality

**Source:** `.ai/audit/06-tests/findings.md`
**Validator:** validator (conservative system integrity validation)
**Date:** 2026-05-29

**Outcome:** All 11 findings validated. 3 findings reclassified. 2 findings merged into 1. No findings rejected as stale or inapplicable.

---

## Reclassified Findings

### TST-001 (SPEC-DEVIATION → DOC-UPDATE)

**Rationale:** The finding recommends "dynamically generated test secrets or environment-specific test configurations" for a test environment. In practice, the codebase uses `os.environ.setdefault("JWT__SECRET_KEY", "test_secret_key_change_in_production")` in `conftest.py` lines 24 and 44 — this is the standard pattern for test fixtures. The `pytest_load_initial_conftests` hook and `pytest_sessionstart` hook validate the secret is set. The finding's claim of "potential credential leakage" is overstated for a test-only configuration that uses `setdefault` (allowing Docker Compose env vars to override). The real issue is documentation: the test README/docs should explicitly test that the test secret *should* be overridden by `_FILE` variants in production CI contexts. The code pattern is correct; what's missing is guidance documentation.

**New classification:** DOC-UPDATE — Add guidance to test documentation explaining how to override the default test secret in CI/CD and Docker environments.

**Severity:** LOW (downgraded from HIGH — no actual security risk in test configuration)

---

### TST-007 (SPEC-DEVIATION → BEST-PRACTICE)

**Rationale:** The finding claims "session scope" `setup_test_database` fixture "can cause issues in CI environments where database recreation might fail." In reality, the full-recreate approach via `DatabaseStarter` is a deliberate design choice — it ensures a clean database state for the entire test session, which is actually *more* reliable than per-test migrations. The `NullPool` and SAVEPOINT patterns at function scope are correctly implemented. The recommendation to use "transactional DDL or alembic migrations" is an alternative approach, not a defect. This is a trade-off discussion, not a spec deviation.

**New classification:** BEST-PRACTICE — Consider evaluating alembic-driven test DB setup as a future improvement for faster CI startup.

**Severity:** LOW (downgraded from MEDIUM — current implementation works correctly)

---

### TST-009 (SPEC-DEVIATION — adjusted scope, **advisory**)

**Rationale:** The finding requests "security-focused input validation tests for malicious patterns." However, the existing codebase validates MIME types, file extensions, and file size — which covers the primary attack vectors. The recommendation for SQL injection tests is partially addressed by the architecture (uses SQLAlchemy async ORM with parameterized queries). Path traversal and null-byte injection tests are not present but are low-risk given the application uses Polars for parsing and doesn't directly execute file content. Classified boundary is adjusted: this is a valid improvement area but not a spec deviation.

**New classification:** BEST-PRACTICE — Expand validation test coverage for defense-in-depth.

**Severity:** LOW (downgraded from MEDIUM)

---

## Merged Findings

### TST-003 + TST-008 → TST-003-MERGED (Malformed Data Handling Test Ambiguity)

**Original findings:** TST-003 (File Upload and Processing Flow Tests), TST-008 (Error Handling Path Tests)
**Merge rationale:** Both findings identify the same root cause — `test_upload_malformed_csv_wrong_delimiter` (line 357) and `test_upload_invalid_data_types` (line 504) both accept multiple status codes `[201, 400, 422]` without asserting expected behavior. TST-008 references these same tests from the error handling perspective. This is a single issue viewed through two lenses (upload flow correctness and error handling clarity).

**Consolidated finding:**

| Field | Value |
|-------|-------|
| **ID** | TST-003-MERGED |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/test_upload_api.py |
| **Classification** | mandatory |

**Description:** Two upload tests accept ambiguous status code ranges without clear behavioral expectations:
- `test_upload_malformed_csv_wrong_delimiter` (line 357): `assert response.status_code in [201, 400, 422]`
- `test_upload_invalid_data_types` (line 504): `assert response.status_code in [201, 400, 422]`

Additionally, `test_temp_file_deleted_on_processing_error` (line 667) manually creates task files for processing rather than going through the full upload endpoint flow, making it a hybrid unit/integration test rather than a true endpoint test.

**Recommendation:** Define clear expected behavior for each malformed data scenario: if the endpoint should reject, assert the specific error code; if it should accept and process, assert success. Each test should have exactly one expected outcome. Consider splitting the cleanup test into a separate unit test focused on cleanup logic directly.

---

## Rollout Safety Analysis

**Dependency graph for test improvements:**

```
TST-001 (DOC-UPDATE)          — independent, docs only
TST-002 (cleanup fixtures)     — independent, test infra only
TST-003-MERGED (ambiguous tests) — depends on: endpoint behavior clarity
TST-004 (assertions)           — independent
TST-005 (mock refactor)        — independent, test-only
TST-006 (decorator cleanup)    — independent, remove-only
TST-007 (BEST-PRACTICE)        — no action needed (reclassified)
TST-009 (BEST-PRACTICE)        — independent, additive
TST-010 (frontend coverage)    — independent, additive
TST-011 (type hints)           — independent, additive
```

**Safety assessment:** All test-only changes are isolated from production code. The highest-risk change is TST-005 (refactoring mock-based tests) because it changes test semantics — ensure integration test pattern from `test_services_integration.py` is followed as the replacement cross-phase conflicts.

**No circular dependencies detected. No unsafe rollout ordering issues.**

---

## Cross-Phase Evidence Verification

No cross-phase conflicts detected for Phase 06 findings. All findings are internally consistent with the codebase state.

---

## Validated Findings Summary

### Mandatory Fixes (7)

| ID | Title | Severity | Type | Notes |
|----|-------|----------|------|-------|
| TST-002 | Authorization boundary test cleanup gaps | MEDIUM | SPEC-DEVIATION | Some tests create DB entries without cleanup in finally blocks — validated as real issue via code inspection of test_permissions.py, test_deps.py |
| TST-003-MERGED | Malformed data handling test ambiguity (merged from TST-003 + TST-008) | MEDIUM | SPEC-DEVIATION | Ambiguous status code assertions in 2 tests; cleanup test manually creates files |
| TST-004 | Data transformation test assertions | MEDIUM | SPEC-DEVIATION | Unknown function test (line 442) asserts shape but not behavior; unknown operator test (line 388) asserts no filtering but doesn't verify logging |
| TST-005 | Mock verification anti-pattern | HIGH | SPEC-DEVIATION | `log_repo.create_log.assert_called_once()` tests mock calls instead of outcomes — confirmed at test_data_service.py line 68-69 |
| TST-006 | Redundant async decorators | LOW | BEST-PRACTICE | `@pytest.mark.asyncio` class decorators present despite `asyncio_mode = "auto"` — confirmed unnecessary |
| TST-010 | Frontend test coverage gap | MEDIUM | SPEC-DEVIATION | Only 3 frontend test files exist vs. 10+ feature modules with zero test coverage — confirmed via glob |
| TST-011 | Missing test type hints | LOW | BEST-PRACTICE | `pyproject.toml` line 194: `path = "tests"` has `ignore_errors = true` — confirmed |

### Advisory Recommendations (3)

| ID | Title | Severity | Type | Notes |
|----|-------|----------|------|-------|
| TST-001 → DOC-UPDATE | Test secret documentation | LOW | DOC-UPDATE | Code pattern is correct; docs should explain CI/CD secret override |
| TST-007 → BEST-PRACTICE | Evaluate alembic-driven test DB setup | LOW | BEST-PRACTICE | Current implementation works; alternative worth evaluating |
| TST-009 → BEST-PRACTICE | Security input validation tests | LOW | BEST-PRACTICE | Defense-in-depth improvement; current validation covers primary vectors |

### Counts

| Category | Original | After Validation |
|----------|----------|-----------------|
| Total findings | 11 | 10 (TST-003 + TST-008 merged → TST-003-MERGED) |
| Mandatory fixes | 9 | 7 (TST-001 → advisory, TST-007 → advisory, TST-009 → advisory) |
| Advisory recommendations | 2 | 3 (TST-001, TST-007, TST-009 reclassified to advisory) |
| Reclassified findings | 0 | 3 |
| Merged findings | 0 | 1 pair (TST-003 + TST-008) |
| Rejected findings | 0 | 0 |

### Doc Updates Required

- **Test configuration documentation:** Document how to override `JWT__SECRET_KEY` in CI/CD pipelines using `_FILE` environment variables or Docker Compose overrides.
