# Phase 06 Validation Report — Test Quality

**Validator:** validator agent
**Input:** `.ai/audit/06-tests/findings.md`
**Validated:** yes
**Mode:** problems-only

---

## Rejected Findings

### TST-004: Mock-heavy unit tests verify mock calls instead of outcomes (test_graph_service.py)

**Rejection reason:** Partially stale / inaccurate evidence. The finding claims tests "only assert mock was called, not that returned data is correct." This is not fully accurate. `test_create_graph_success` (lines 60-62) asserts `isinstance(result, GraphRead)`, `result.name == "Sales"`, and `result.type == GraphType.BAR` in addition to the mock assertion at line 63. `test_update_graph_partial` (line 156) asserts `result.name == "Updated Name"` plus the mock call. While the tests are indeed mock-heavy and could be converted to integration tests, they DO verify outcome data alongside mock calls. The finding overstates the problem by claiming only mock calls are verified. The core recommendation (convert to integration tests) remains valid as advisory, but the severity is overstated.

**Action:** Downgrade from advisory BEST-PRACTICE to advisory with revised scope. The tests verify outcomes but rely on mocks instead of real database sessions.

---

## Reclassified Findings

### TST-002: Test assertion mismatch — MIME type error message differs from expected pattern

**Original type:** RUNTIME-ERROR → **Reclassified type:** BEST-PRACTICE

**Rationale:** The test failure is not a runtime error in production code — the production code correctly validates file extensions and raises the proper error. The issue is that the test expectation is wrong. The test comment (lines 555-557) claims "Small CSV content is detected as text/plain by libmagic," but on platforms without libmagic (e.g., Windows), the fallback MIME detector in `detect_mime_type_from_content` (lines 59-62) detects `b"col1,col2\nval1,val2\n"` as `text/csv` (contains commas and newlines), which passes the MIME check. The `.txt` extension then fails at the extension check (step 3, lines 127-141). This is a platform-dependent test bug, not a production runtime error. The test needs to be updated to match actual behavior on the target platform, or the test should use content that reliably produces `text/plain` across all MIME detection backends.

---

## Validated Findings (Problems Found)

### TST-001: Test expects None JWT secret to be accepted but .env config provides default value

**Status:** VALIDATED — mandatory fix
**Verification:** Test `test_none_jwt_secret_accepted` confirmed FAILED with `AssertionError: assert 'dev-secret-key-for-security-testing-do-not-use-in-prod-32chars' is None`. The `.env` file provides `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars` which takes precedence over `monkeypatch.delenv` because pydantic-settings loads .env before monkeypatch takes effect. The test's assumption that deleting the env var results in `None` is incorrect given the project's configuration loading order.

### TST-003: Tautological test — test_store_fail_open_on_error asserts only that no exception was raised

**Status:** VALIDATED — advisory
**Verification:** Test confirmed PASSES but only asserts `assert True` at line 177. The test cannot fail regardless of whether the store operation handles errors correctly. No verification of mock calls, logging, or state.

### TST-005: Mock-heavy unit tests verify mock calls instead of outcomes (test_auth_service.py)

**Status:** VALIDATED — advisory
**Verification:** Tests at lines 60, 446-447, 464, 482, 516 do assert mock invocations. However, some tests (e.g., line 58-59) also verify outcome data. The finding is partially valid: the tests rely on AsyncMock rather than real database sessions, testing implementation structure rather than behavior. The recommendation to convert to integration tests is reasonable but not urgent.

### TST-006: Frontend tests have act() warnings for async state updates

**Status:** VALIDATED — advisory
**Verification:** Frontend test run confirmed multiple `act(...)` warnings for `useAuth.test.tsx`. All 16 tests pass but emit warnings: "An update to TestComponent inside a test was not wrapped in act(...)." This indicates potential timing-sensitive test behavior.

### TST-007: Rate limiter tests exist but lack integration with auth endpoints

**Status:** VALIDATED — advisory
**Verification:** `TestRateLimiting` class (tests/test_auth.py:263-391) tests the `AsyncRateLimiter` class in isolation. `test_auth_api.py` contains no rate-limiting tests (confirmed via grep: zero matches for `rate_limit`). The `rate_limiter_fail_closed` config flag exists but is not tested at the endpoint level.

### TST-008: Coverage failure — total coverage 45% below required 80%

**Status:** VALIDATED — advisory (escalated scope)
**Verification:** Coverage run confirmed `TOTAL 7452 4129 45%` with `FAIL Required test coverage of 80.0% not reached. Total coverage: 44.59%`. This is significantly worse than the 68% reported in the original finding. Zero-coverage modules confirmed: `decorators.py (0%)`, `style.py (0%)`, `filter_service.py (0%)`, `aggregation_service.py (0%)`, `file_cleanup.py (16%)`, `layout_service.py (19%)`, `user_service.py (23%)`, `workers/data_worker.py (14%)`. The `base_repository.py` and `registry.py` modules referenced in the original finding do not exist in the current codebase — those findings were stale.

**Additional finding:** The `decorators.py` module (157 lines, 0% coverage) has zero imports from other production modules (confirmed via grep), suggesting it may be dead code that should be removed rather than tested.

---

## Cross-Phase Conflicts

### Coverage conflict: TST-008 reports 68% but actual coverage is 45%

The original finding reported 68% coverage. Current measurement shows 44.59%. This is a significant discrepancy. Possible causes: (1) the original measurement ran a different subset of tests, (2) code was added without corresponding tests, or (3) the original measurement used different coverage settings. The finding's core claim (coverage below 80%) is validated and actually understates the problem.

### Stale module references in TST-008

The original finding references `base_repository.py` and `registry.py` as zero-coverage modules. These files do not exist in the current codebase. This part of the finding is stale.

---

## Rollout Safety Analysis

No rollout sequencing issues identified. All findings are test-quality improvements that can be addressed independently. No circular dependencies or unsafe execution ordering detected.

---

## Validated Counts

| Category | Count |
|----------|-------|
| Validated mandatory fixes | 1 (TST-001) |
| Validated advisory recommendations | 5 (TST-003, TST-005, TST-006, TST-007, TST-008) |
| Rejected findings | 1 (TST-004 — partially inaccurate evidence) |
| Reclassified findings | 1 (TST-002 — RUNTIME-ERROR → BEST-PRACTICE) |
| Cross-phase conflicts | 2 (coverage discrepancy, stale module refs) |
