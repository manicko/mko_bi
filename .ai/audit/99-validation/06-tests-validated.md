# Validation Report — Phase 06: Test Quality

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/06-tests/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted (unchanged) | Rejected | Reclassified | Merged |
|----------------|-------|----------------------|----------|--------------|--------|
| Mandatory | 3 | 3 | 0 | 0 | 0 |
| Advisory | 4 | 3 | 1 | 0 | 0 |
| **Total** | **7** | **6** | **1** | **0** | **0** |

---

## Rejected Findings

### TST-002: Stale `.pyc` Cache Files — REJECTED

**Original Severity:** LOW
**Original Type:** BEST-PRACTICE
**Original Classification:** advisory

**Rejection reason:** The finding is **partially stale and overstated**.

1. **`.gitignore` already covers `.pyc` files.** The project `.gitignore` line 2 includes `__pycache__/` and line 3 includes `*.py[codz]`. Therefore no `.pyc` file is tracked by git — confirmed by `git ls-files tests/__pycache__/` returning zero results. The `.pyc` files are local Python runtime artifacts that `.gitignore` correctly prevents from being committed.

2. **The "stale" `.pyc` files are normal.** Python caches compiled bytecode in `__pycache__` and does not automatically delete `.pyc` files when their source `.py` files are deleted. This is expected Python behavior. The files (`test_yoy_calculation`, `test_share_calculation`, `test_data_processing`, `test_models`) are old artifacts from test files that were removed — they do not affect test execution, coverage, or correctness.

3. **The recommendation to add `find . -type d -name __pycache__ -exec rm -rf {} +` is overkill** for a development environment. If cleanup is desired, running `Remove-Item -Recurse -Force tests/__pycache__` is a one-time manual step, not worth codifying in a Makefile target since Python recreates these caches on next test run anyway.

**Rejected**: `.gitignore` already handles this correctly. The cache files are harmless local artifacts. No action needed.

---

## Validated Findings (Accepted, No Issues)

The following findings pass validation unchanged. Per problems-only mode, they are listed for completeness but require no validation commentary:

| ID | Severity | Type | Classification | Verdict |
|----|----------|------|----------------|---------|
| TST-001 | CRITICAL | RUNTIME-ERROR | mandatory | Validated — DB port 5432 not published to host. `docker inspect docker-db-1` confirms `{"5432/tcp": null}`. `conftest.py:17-18` sets `DATABASE__HOST=localhost`, `DATABASE__PORT=5432`. Override file exists but is not used by default. All 233 test errors are `ConnectionRefusedError`. The `docker-compose.yml` header comment (line 6) documents the override usage, but `commands.md` does not mention this requirement. |
| TST-003 | LOW | BEST-PRACTICE | advisory | Validated — `tests/test_upload_api.py.bak` is tracked by git (29083 bytes, similar but different from the active 29114-byte `test_upload_api.py`). `*.bak` is not in `.gitignore`. Both files matched by pytest's `test_*.py` pattern. |
| TST-004 | HIGH | SPEC-DEVIATION | mandatory | Validated — Only 6 frontend test files exist (`enums.test.ts`, `formSchemas.test.ts`, `authToken.test.ts`, `authFlow.test.tsx`, `DashboardView.test.tsx`, `FileDropzone.test.tsx`). Zero test files found in admin, users, shared/api, shared/components, shared/hooks modules. Critical components like `ProtectedRoute`, `RoleBasedAccess`, `refreshHandler`, `axiosInstance`, chart components are all untested. |
| TST-005 | MEDIUM | BEST-PRACTICE | advisory | Validated — `baseline_data` fixture at `conftest.py:373-380` is a session-scoped no-op (`yield` with no setup). Grepped all test files: zero tests use this fixture. Docstring explicitly calls it a placeholder. |
| TST-006 | HIGH | SPEC-DEVIATION | mandatory | Validated — `conftest.py:18` defaults `DATABASE__PORT` to `5432` (dev instance). `docker-compose.test.yml` defines isolated `test-db` on port 5433 but conftest does not target it by default. `test_user` fixture at `conftest.py:443` calls `await async_db_session.commit()` which commits to whichever DB the conftest connects to — if using the dev instance at port 5432, this writes to the shared dev database. SAVEPOINT rollback provides transaction-level isolation but not database-level isolation. |
| TST-007 | MEDIUM | BEST-PRACTICE | advisory | Validated — `_auto_mock_redis` at `conftest.py:182` is `autouse=True`, patching Redis and disabling rate limiting in all tests. `_original_auth_init` uses a lazy-initialized global (`None` at line 170, set at line 178). The `strict_redis` fixture (line 257) restores real rate limiting but is only used by `TestRateLimiting`. Any test relying on active rate limiting without explicitly using `strict_redis` will silently pass with no actual rate limiting enforced. |

---

## Cross-Phase Conflicts

### 1. TST-001 vs Phase 05 (INF findings) — Docker Compose Port Exposure

**Nature:** Complementary, not conflicting.

Phase 05 found that `.env` development values override production mode (INF-02). TST-001 finds that the `db` service port 5432 is not published to the host. Both stem from the same root cause: the `docker-compose.yml` base file is designed for production, override file for development, but neither `commands.md` nor the docker-compose documentation makes the override requirement explicit for test runs from the host.

TST-001 recommends either (a) exposing port 5432 in the base compose or (b) always using the override. Phase 05 does not address DB port exposure. These are independent recommendations that should be resolved together: **document the override requirement in `commands.md`** as part of Docker setup for tests.

**Resolution:** Both findings are valid and should be addressed. TST-001's recommendation (b) is the safer option — always use the override for dev/test — rather than modifying the base compose file to add ports.

### 2. TST-006 vs Phase 03 (DB findings) — Test Database Isolation

**Nature:** Complementary, not conflicting.

Phase 03 (database) addresses migration correctness and schema design. TST-006 addresses the test infrastructure connecting to the wrong database instance. No overlap in root causes, but a coordinated fix should ensure that when tests use port 5433 (`test-db`), the conftest configuration is updated to match (change default `DATABASE__PORT` from `5432` to `5433`).

### 3. TST-001 vs TST-006 — Shared Root Cause (Test Database Configuration)

**Nature:** Related findings, should be merged in implementation plan.

TST-001 and TST-006 are two symptoms of the same problem: **the backend test suite is not configured for host-native execution with the test docker-compose stack**. TST-001 is the immediate symptom (port not exposed, 233 errors). TST-006 is the deeper issue (even when port is exposed, tests target the wrong database instance).

These are **not merged** as findings because they have distinct severity and scope (one is a blocking runtime error, the other is a data isolation risk). However, the **implementation fix should be unified**: run `docker compose -f docker/docker-compose.test.yml up -d` and configure conftest to use `DATABASE__PORT=5433` when running tests natively. This single action resolves both TST-001 and TST-006.

---

## Rollout Safety Assessment

### TST-001 (DB Port Exposure) — Rollout Risk: LOW

- **Risk:** Minimal. Exposing port 5432 on the `db` service or using the override does not affect container-internal networking. Containers already communicate via Docker network.
- **Dependency:** None for the docker-compose change. Test execution from host requires the override to be active.
- **Recommendation (b)** is preferred over (a): add the override requirement to `commands.md` and the Docker documentation. Do NOT add ports to the base `docker-compose.yml` — the base file is production-targeted, and exposing DB ports in production is a security concern.

### TST-003 (Backup File Removal) — Rollout Risk: NONE

- **Risk:** Zero. Removing a `.bak` file does not affect any runtime or test behavior. The active `test_upload_api.py` remains intact.
- **Dependency:** None.
- **Note:** Ensure `git rm tests/test_upload_api.py.bak` is used so the file is removed from version control history tracking as well.

### TST-004 (Frontend Test Coverage) — Rollout Risk: NONE

- **Risk:** Adding tests has no production impact. Tests are development-only artifacts.
- **Dependency:** None.

### TST-005 (No-op baseline_data fixture) — Rollout Risk: NONE

- **Risk:** Removing or implementing a fixture that no test uses has zero runtime impact.
- **Dependency:** None.

### TST-006 (Test Database Isolation) — Rollout Risk: LOW

- **Risk:** Changing `DATABASE__PORT` from `5432` to `5433` in conftest defaults would break test runs that rely on the dev DB being exposed on port 5432. However, the test stack (`docker-compose.test.yml`) should be the standard for all native test runs. The conftest defaults should be changed **only** when the test stack is confirmed to be the standard testing approach.
- **Dependency:** Requires `docker compose -f docker/docker-compose.test.yml up -d` to be running.
- **Recommendation:** Update `commands.md` to document the test stack startup step before running tests. This aligns with the existing comment in `docker-compose.yml` line 7 ("Test: docker compose -f docker/docker-compose.test.yml up -d").

### TST-007 (Auto-Mock Redis) — Rollout Risk: NONE (advisory only)

- **Risk:** No code change recommended. The advisory is to improve documentation within `conftest.py` to warn future developers about the auto-mock behavior. Zero runtime impact.
- **Dependency:** None.
- **Critique of the recommendation:** The finding suggests initializing `_original_auth_init` eagerly at module level to avoid import-order coupling. This is a micro-optimization with negligible impact. The lazy initialization via `_get_original_auth_init()` is a well-established pytest pattern. The more valuable action is adding a comment at the top of conftest.py documenting the autouse mock behavior.

---

## Mandatory Fixes (Accepted)

| ID | Severity | Type | Issue |
|----|----------|------|-------|
| TST-001 | CRITICAL | RUNTIME-ERROR | 233/603 backend tests fail because DB port 5432 is not exposed to host. Override file exists but is not used by default. |
| TST-004 | HIGH | SPEC-DEVIATION | Frontend has only 82 tests across 6 files. Critical components (ProtectedRoute, RoleBasedAccess, refreshHandler, charts) have zero coverage. |
| TST-006 | HIGH | SPEC-DEVIATION | Test suite targets dev DB instance (port 5432) instead of isolated test DB (port 5433). Risk of data corruption and non-deterministic behavior. |

## Advisory Recommendations (Accepted)

| ID | Severity | Type | Issue | Rollout Risk |
|----|----------|------|-------|--------------|
| TST-003 | LOW | BEST-PRACTICE | `test_upload_api.py.bak` tracked by git; `*.bak` not in `.gitignore` | NONE |
| TST-005 | MEDIUM | BEST-PRACTICE | `baseline_data` fixture is a no-op placeholder, used by zero tests | NONE |
| TST-007 | MEDIUM | BEST-PRACTICE | Auto-mock Redis fixture disables rate limiting in all tests; fragile global variable pattern | NONE |

---

## Summary

- **7 findings validated**, 1 rejected (TST-002), 0 reclassified, 0 merged.
- **3 mandatory fixes** (TST-001, TST-004, TST-006), **3 advisory recommendations** (TST-003, TST-005, TST-007).
- **TST-001 and TST-006 share a root cause** (test infrastructure not configured for host-native execution) and should be resolved together by documenting and using the test docker-compose stack (`docker-compose.test.yml`).
- **Cross-phase:** TST-001 complements Phase 05 findings about Docker Compose configuration. No conflicts.
- **Highest priority:** TST-001 (CRITICAL) — blocks 38% of the backend test suite from running on the host.
