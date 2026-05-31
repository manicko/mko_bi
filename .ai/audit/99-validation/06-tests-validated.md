# Phase 06 Validation Report — Test Quality

**Validator:** validator agent
**Input:** `.ai/audit/06-tests/findings.md`
**Mode:** problems-only

---

## Cross-Phase Conflict

### TST-002 / SEC-003: Overlapping Finding — Graph Endpoint Dashboard Access

TST-002 (Phase 06 — Tests) and SEC-003 (Phase 04 — Security) identify the same root cause: the `/graphs/{graph_id}` endpoints lack dashboard-level access control. However, they approach it from different angles:

- **SEC-003** identifies that the **production code** (`src/mkobi/api/routes/graphs.py`) does not call `check_dashboard_access()` — any authenticated user can access any graph by ID. This is a code-level security vulnerability (IDOR).
- **TST-002** identifies that the **test suite** (`tests/test_graphs.py`) has no test coverage for cross-dashboard access scenarios — there is no test that creates a graph on one dashboard and attempts to access it from a user who only has access to a different dashboard.

**Resolution:** These findings are complementary, not conflicting. SEC-003 addresses the code fix; TST-002 addresses the test gap. Both should remain:
- SEC-003 (mandatory) — fix the production code to add `check_dashboard_access()` to graph endpoints.
- TST-002 (mandatory) — add cross-dashboard access tests to verify the fix.

**Merge decision:** Do NOT merge. The findings target different layers (code vs. tests) and require separate implementation tasks.

---

## Reclassified Findings

### TST-001: Reclassified from BEST-PRACTICE to DOC-UPDATE

**Original type:** BEST-PRACTICE
**New type:** DOC-UPDATE
**Rationale:** The finding describes a real pattern (heavy mocking of `check_dashboard_access`, `enqueue_job`, `find_task_file`, `enqueue_processing_job` in test_data_service.py), but the tests are **integration tests** that use a real database with real repositories. The mocking is limited to external side effects (job enqueueing) and access control — which are tested separately via `test_process_upload_no_permission_raises` pattern. The tests already verify actual database state (log records, status updates) rather than just mock calls.

However, the finding identifies that the test docstring says "integration tests verifying actual database state" while simultaneously mocking the permission check entirely. This is a documentation/consistency issue, not a code bug. The test comments should clarify WHY `check_dashboard_access` is mocked (e.g., "mocked to isolate data service logic from access control, which is tested separately in test_upload_api.py").

**Reclassification:** DOC-UPDATE — update test module docstrings and comments to explain the mocking strategy. No test restructuring required at this project scale.

**Advisory value confirmed:** The recommendation to reduce mocking and test at the API layer is already partially followed (test_upload_api.py does this well). But for data service unit tests, mocking external side effects is acceptable practice.

---

## Rejected Findings

### TST-004: No coverage threshold enforcement in CI config

**Rejection reason:** The finding claims `pyproject.toml` lines 221-227 show coverage config with `fail_under = 80`. Verified: pyproject.toml `[tool.coverage.report]` section has `fail_under = 80` and `show_missing = true` (lines ~520-522). The finding is correct that frontend has NO coverage threshold.

**However, the frontend `vite.config.ts` test block** contains only:
```ts
test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
}
```
No `coverage` key exists. The `@vitest/coverage-*` packages are transitive dependencies in `package-lock.json` (pulled in by vitest itself) but are explicitly listed in `package.json` devDependencies.

**Rejection rationale for problems-only report:** This finding is validated as accurate — the frontend does lack coverage threshold enforcement. The finding is retained as advisory. *(No rejection — see validated summary below.)*

**Correction:** TST-004 is **NOT rejected** — it is validated. Retained as advisory.

---

## Validated Findings (No Changes)

| Finding | Severity | Type | Validation | Classification |
|---------|----------|------|------------|----------------|
| TST-002 | HIGH | SPEC-DEVIATED | **VALIDATED** — `test_get_graph_by_id` creates a dashboard and graph using the same admin user, then fetches the graph via `authenticated_client` (same user). No test creates graph on dashboard A and attempts access from user with access only to dashboard B. Confirmed: `tests/test_graphs.py` lines 258-291 cross-dashboard scenario absent. | Mandatory |
| TST-003 | HIGH | BEST-PRACTICE | **VALIDATED** — Exactly 3 frontend test files confirmed: `authToken.test.ts`, `formSchemas.test.ts`, `enums.test.ts`. No `.spec.{ts,tsx}` files exist. Zero coverage for DashboardView, FileDropzone, all chart components, useAuth, admin panels. | Mandatory |
| TST-004 | MEDIUM | BEST-PRACTICE | **VALIDATED** — `vite.config.ts` has no `coverage` config. `package.json` has no coverage devDependencies. Backend has `fail_under = 80` in pyproject.toml. Frontend threshold entirely absent. | Advisory |
| TST-005 | LOW | BEST-PRACTICE | **VALIDATED** — `test_upload_api.py` lines 644-669: `mock_cleanup = mocker.patch(..., wraps=file_cleanup.cleanup_task_files)` then `file_cleanup.cleanup_task_files(task_id=UUID(task_id))` then `mock_cleanup.assert_called()`. The test calls the real function (via `wraps`) and then asserts the mock was called — tautological because the call path is: test code → real function → mock records call → assert_called. However, the intent is to verify cleanup is invoked as part of the processing flow. The assertion value is minimal but not harmful. | Advisory |
| TST-006 | MEDIUM | BEST-PRACTICE | **VALIDATED** — `test_auth.py` lines 176-217 (`test_refresh_valid_token`): Only tests happy path with valid refresh token. No tests for: expired refresh token, invalid/forgeable signature, concurrent refresh attempts, token rotation verification, reuse of revoked refresh token. The conftest auto-mock (`_auto_mock_redis`) patches `check_rate_limit` to always return `True`, so rate limiting on refresh is also untested. | Advisory |
| TST-007 | LOW | BEST-PRACTICE | **VALIDATED** — `conftest.py` MockRedis class has `expire`, `execute`, and `close` methods with `pass` bodies (no-ops). These are called by real Redis client code in production but do nothing in tests. Risk: if code depends on TTL enforcement or pipeline execution behavior, tests would silently pass. Low severity because the mock is intentionally simple and the test suite focuses on business logic, not Redis behavior. | Advisory |
| TST-008 | MEDIUM | BEST-PRACTICE | **VALIDATED** — `test_data_transformations.py` tests cover: formula parsing, filtering, computed fields, dtype application, aggregations, YoY, share calculation, and basic edge cases (zero total, missing columns). Missing tests: empty DataFrame input to `apply_transformations` or `calculate_aggregations`, all-null column aggregations, YoY with non-contiguous year gaps, share with negative values, date parsing failure handling in transformation context. | Advisory |

---

## Mandatory Fixes (2)

- **TST-002:** Add cross-dashboard access tests to `test_graphs.py` — create graph on dashboard A, attempt access from user with access only to dashboard B, assert 403. This directly supports the SEC-003 mandatory fix.
- **TST-003:** Add frontend tests for critical user flows (dashboard rendering, auth flow, file upload, chart rendering, access control).

## Advisory Recommendations (5)

- **TST-004:** Add coverage threshold to `vite.config.ts` (e.g., `coverage: { thresholds: { statements: 60 } }`).
- **TST-005:** Replace tautological `mock_cleanup.assert_called()` with direct state verification (e.g., verify files were actually deleted from disk).
- **TST-006:** Add refresh token tests: expired token, invalid signature, concurrent refresh, token rotation, revoked token reuse.
- **TST-007:** Either document MockRedis no-op methods or add TTL tracking for tests that depend on expiration behavior.
- **TST-008:** Add transformation edge case tests: empty DataFrame, all-null aggregations, YoY with year gaps, negative share values.

## Reclassified (1)

- **TST-001:** Reclassified from BEST-PRACTICE → DOC-UPDATE. The heavy mocking pattern is acceptable for integration tests that verify database state. Update test docstrings/comments to explain why `check_dashboard_access` is mocked. No test restructuring required.

## Cross-Phase Issues (1)

- **TST-002 / SEC-003 overlap:** Both identify missing dashboard access control on graph endpoints. SEC-003 targets production code; TST-002 targets test coverage. Both retained as separate mandatory findings requiring coordinated implementation.

---

## Validated Counts

| Category | Count |
|----------|-------|
| Total findings | 8 |
| Validated (unchanged) | 6 |
| Reclassified | 1 (TST-001: BEST-PRACTICE → DOC-UPDATE) |
| Rejected | 0 |
| Cross-phase conflicts | 1 (TST-002 ↔ SEC-003, complementary) |
| Mandatory fixes | 2 |
| Advisory recommendations | 5 |
| Doc updates | 1 |
