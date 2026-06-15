---
name: audit-findings
description: Phase 06 Test Quality Audit Findings
agent: auditor
alwaysApply: false
---

# Phase 06 Audit Findings — Test Quality

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TST-001: Test assumes `.env` file fallback that does not exist in Docker

| Field | Value |
|-------|-------|
| **ID** | TST-001 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `tests/test_config.py` |
| **Classification** | mandatory |

**Description:** `test_none_jwt_secret_accepted` in `tests/test_config.py:379` deletes the `JWT__SECRET_KEY` environment variable via `monkeypatch.delenv` and expects the Settings constructor to fall back to a value from the `.env` file (`dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`). In the Docker test container, no `.env` file exists at `/app/.env`, so `settings.jwt.secret_key` is `None` instead of the expected fallback value. The test passes on the host (where `.env` exists) but fails in Docker, making the test environment-dependent.

**Evidence:**
- `tests/test_config.py:379-384` — test expects `.env` fallback value
- `src/mkobi/config.py:495` — `model_config` sets `"env_file": ".env"`
- Docker container confirmed: `ls -la /app/.env*` → `No such file or directory`
- Docker test run: `FAILED tests/test_config.py::TestJWTSecretValidation::test_none_jwt_secret_accepted - AssertionError: assert None == 'dev-secret-key-for-security-testing-do-not-use-in-prod-32chars'`
- Host test run: 874 passed (test passes when `.env` is present)

**Recommendation:** Either mount the `.env` file into the test container in `docker-compose.test.yml`, or rewrite the test to not depend on a `.env` file existing. The simplest fix is to set the expected fallback via `monkeypatch.setenv` in the test itself rather than relying on filesystem state. This makes the test self-contained and environment-independent.

---

### TST-002: Test assumes fallback MIME detector but Docker container uses python-magic

| Field | Value |
|-------|-------|
| **ID** | TST-002 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `tests/test_data_service.py` |
| **Classification** | mandatory |

**Description:** `test_validate_file_invalid_extension` in `tests/test_data_service.py:552` creates a `.txt` file with CSV-like content (`col1,col2\nval1,val2\n`) and expects the extension check to fail first with `"Invalid file format.*test.txt"`. The test comment explicitly states the assumption: "CSV content with commas/newlines is detected as text/csv (allowed), so extension check fails first." However, in the Docker container, `python-magic` is installed and correctly detects the content as `text/plain` (not `text/csv`), so the MIME validation step fails first with `"Detected MIME type text/plain not allowed"`. The test passes on Windows (where the fallback detector is used) but fails in Docker.

**Evidence:**
- `tests/test_data_service.py:552-577` — test expects "Invalid file format" error
- `src/mkobi/services/file_processing.py:22-64` — MIME detection has two paths: python-magic (Docker) and fallback (Windows)
- `src/mkobi/services/file_processing.py:91-141` — `validate_file` checks MIME first (step 2), then extension (step 3)
- Docker test run: `FAILED tests/test_data_service.py::TestFileValidation::test_validate_file_invalid_extension - AssertionError: Regex pattern did not match. Expected regex: 'Invalid file format.*test.txt'. Actual message: 'Detected MIME type text/plain not allowed'`
- Host test run: 874 passed (fallback detector treats content as `text/csv`)

**Recommendation:** Rewrite the test to not depend on which MIME detector is active. Either: (a) use content that both detectors agree is `text/csv` (e.g., more rows/columns), or (b) test the extension check and MIME check in separate tests with appropriate content for each. The test should be deterministic regardless of whether `python-magic` is installed.

---

### TST-003: Ruff cache permission errors in Docker container cause test failures

| Field | Value |
|-------|-------|
| **ID** | TST-003 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `tests/test_dev_seeders.py` |
| **Classification** | mandatory |

**Description:** `test_seed_script_ruff_mypy` and `test_dev_seeders_module_ruff_mypy` in `tests/test_dev_seeders.py:183,209` run `ruff check` via `subprocess.run` inside the Docker container. Ruff fails with a cache permission error: `Failed to initialize cache at /app/.ruff_cache: Permission denied (os error 13)`. The container's `/app` directory is not writable by the running user, causing ruff to fail before it can actually check the code. The tests assert `result.returncode == 0`, which fails because ruff couldn't run at all, not because the code has lint errors.

**Evidence:**
- `tests/test_dev_seeders.py:183-206` — runs `ruff check` via subprocess
- `tests/test_dev_seeders.py:209-230` — runs `ruff check` via subprocess
- Docker test run error: `Ruff check failed: error: Failed to initialize cache at /app/.ruff_cache: Permission denied (os error 13)`
- Host test run: 874 passed (ruff cache is writable on host)

**Recommendation:** Either: (a) set `RUFF_CACHE_DIR` environment variable to a writable path (e.g., `/tmp/ruff_cache`) in the Docker test container, or (b) run ruff with `--no-cache` flag, or (c) fix the container's `/app/.ruff_cache` directory permissions in the Dockerfile. Option (b) is the simplest: `ruff check --no-cache <path>`.

---

### TST-004: Tests assert mock call counts instead of behavior outcomes

| Field | Value |
|-------|-------|
| **ID** | TST-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_data_worker.py`, `tests/test_auth_service.py`, `tests/test_graph_service.py` |
| **Classification** | advisory |

**Description:** Multiple tests verify that mock methods were called (e.g., `mock_session.execute.assert_called_once()`, `mock_user_repo.update.assert_called_once()`, `mock_db.commit.assert_called_once()`) rather than verifying the actual behavior or outcome. This makes tests brittle — they break when implementation details change even if the behavior is correct. Specific instances:

- `tests/test_data_worker.py:52,73,96,118,136,276` — `TestDataWorker` and `TestStoreAggregates` assert `mock_session.execute.assert_called_once()` without checking what SQL was executed
- `tests/test_auth_service.py:446-447,464,482` — `reset_password_admin` tests assert `mock_user_repo.update.assert_called_once()` and `mock_db.commit.assert_called_once()` instead of verifying the password was actually changed
- `tests/test_graph_service.py:63,157` — `create` and `update` tests assert `mock_graph_repo.create.assert_called_once()` and `mock_graph_repo.update.assert_called_once()`

**Evidence:**
- `tests/test_data_worker.py:52` — `mock_session.execute.assert_called_once()` with no verification of the SQL statement
- `tests/test_auth_service.py:446-447` — asserts mock calls instead of checking password change behavior
- `tests/test_graph_service.py:63` — asserts `mock_graph_repo.create.assert_called_once()` instead of verifying the returned graph data

**Recommendation:** Replace mock call assertions with behavioral assertions. For example, instead of `mock_session.execute.assert_called_once()`, verify the return value or side effect. Instead of `mock_user_repo.update.assert_called_once()`, verify the user's password was actually changed. Mock call assertions should only be used when the call itself is the behavior being tested (e.g., verifying that a cache was invalidated).

---

### TST-005: TestStoreAggregates mocks entire dependency chain, testing mock wiring not behavior

| Field | Value |
|-------|-------|
| **ID** | TST-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_data_worker.py` |
| **Classification** | advisory |

**Description:** The `TestStoreAggregates` class in `tests/test_data_worker.py:244-483` mocks all three major dependencies of `_store_aggregates`: `AggregationService`, `StorageManager`, and `DashboardFilterValuesRepository`. The tests then assert that these mocks were called (`mock_manager_instance.save_aggregates.assert_called_once()`, `mock_repo_instance.save_filter_values.assert_called_once()`). This tests that the function wires its dependencies correctly, but does not test any actual business logic — the real `AggregationService.aggregate_for_dashboard()`, `StorageManager.save_aggregates()`, and `DashboardFilterValuesRepository.save_filter_values()` are never exercised. If the real implementations have bugs, these tests will not catch them.

**Evidence:**
- `tests/test_data_worker.py:316-327` — patches `AggregationService`, `StorageManager`, and `DashboardFilterValuesRepository`
- `tests/test_data_worker.py:346-347` — only asserts `mock_session.execute.call_count == 2` and `mock_manager_instance.save_aggregates.assert_called_once()`
- `tests/test_data_worker.py:414-415` — only asserts `call_kwargs[1]["clear_old"] is False` on the mock
- `tests/test_data_worker.py:483` — only asserts `mock_repo_instance.save_filter_values.assert_called_once()`

**Recommendation:** Consider adding integration tests that exercise `_store_aggregates` with real (or test-database-backed) dependencies. At minimum, the unit tests should verify that the correct arguments are passed to the mocked dependencies (e.g., verify the aggregation input data, the storage mode, and the filter values). This would catch bugs in data transformation logic that is currently untested.

---

### TST-006: test_cleanup_task_files_called_during_processing calls real function then asserts mock

| Field | Value |
|-------|-------|
| **ID** | TST-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_upload_api.py` |
| **Classification** | advisory |

**Description:** `test_cleanup_task_files_called_during_processing` in `tests/test_upload_api.py:731-784` patches `cleanup_task_files` with `wraps=file_cleanup.cleanup_task_files`, then calls `cleanup_task_files(task_id=UUID(task_id))` directly in the test body, and finally asserts `mock_cleanup.assert_called()`. Since the test calls the function directly (which is the real function wrapped by the mock), the assertion `mock_cleanup.assert_called()` will always pass — it's testing that the function was called because the test itself called it. This is a tautological assertion pattern.

**Evidence:**
- `tests/test_upload_api.py:759-762` — patches with `wraps=file_cleanup.cleanup_task_files`
- `tests/test_upload_api.py:781` — calls `file_cleanup.cleanup_task_files(task_id=UUID(task_id))` directly
- `tests/test_upload_api.py:784` — asserts `mock_cleanup.assert_called()` which is always true since the test just called it

**Recommendation:** The test should verify the actual behavior (e.g., that the temp file was deleted from disk) rather than asserting the mock was called. Alternatively, if the intent is to verify that `cleanup_task_files` is called during processing, the test should trigger processing and assert the mock was called by the processing code, not by the test itself.

---

### TST-007: No coverage tool configured for CI; coverage only runnable from host

| Field | Value |
|-------|-------|
| **ID** | TST-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `pyproject.toml`, `docker/docker-compose.test.yml` |
| **Classification** | advisory |

**Description:** The project has `pytest-cov` as a dev dependency and `pyproject.toml` configures coverage thresholds (`fail_under = 65`), but running coverage inside the Docker test container fails due to SQLite database file permission errors (`coverage.exceptions.DataError: Couldn't use data file`). Coverage can only be run from the host. This means CI pipelines that run tests inside containers cannot enforce coverage thresholds. The `.coverage` SQLite database cannot be written to `/app` in the container.

**Evidence:**
- `pyproject.toml:207-213` — coverage config with `fail_under = 65`
- Docker test run with `--cov`: `coverage.exceptions.DataError: Couldn't use data file '/app/.coverage.90590686b30a.pid7.X6m5e2hx': unable to open database file`
- Host test run: coverage works, reports 70.58% total coverage

**Recommendation:** Either: (a) configure coverage to write to a writable directory in the container (e.g., `/tmp/.coverage`), or (b) add a `coverage.toml` or environment variable to set the coverage data file path, or (c) run coverage only from the host/CI and skip it in Docker test runs. The simplest fix is to set `COVERAGE_FILE=/tmp/.coverage` in the test container environment.

---

### TST-008: Critical path coverage gaps identified from coverage report

| Field | Value |
|-------|-------|
| **ID** | TST-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/`, `src/mkobi/services/`, `src/mkobi/workers/`, `src/mkobi/core/` |
| **Classification** | advisory |

**Description:** Coverage analysis (host run, 70.58% total) reveals significant gaps in critical paths:

| Module | Coverage | Missing Lines | Risk |
|--------|----------|---------------|------|
| `api/routes/dashboards_access.py` | 32% | 65-124, 155-168, 200-224 | Access control logic untested |
| `api/routes/dashboards_filters.py` | 26% | 49-102, 123-175, 195-208 | Filter CRUD untested |
| `api/routes/processing_configs.py` | 30% | 60-95, 133-178, 210-244 | Processing config API untested |
| `api/routes/users.py` | 34% | 59-74, 105-112, 150-178, 216-240, 277-291, 329-331, 342-346 | User management API untested |
| `api/routes/upload.py` | 63% | 84, 89, 94, 132-136, 159-169, 221-223, 243-279, 299-335 | Upload error handling partially untested |
| `services/user_service.py` | 51% | 37-46, 67, 126-132, 144-150, 173-204, 226-246, 269, 284-285, 310, 327, 343-347 | User service partially untested |
| `services/filter_service.py` | 56% | 71-72, 83, 94-98, 117-118, 120-122, 138-146, 160-165, 186-187, 195, 198, 201, 208, 210, 213-214, 221, 225-228, 251, 255-258, 292-293, 296-297, 300-301, 316-317, 320-321, 324-325 | Filter service partially untested |
| `workers/data_worker.py` | 52% | 54-77, 98, 104, 130, 135, 144, 155, 160, 205, 220-222, 226-231, 269-284, 342-348, 365-375, 379-386, 390-407, 411-413, 417-419, 425-446, 494-551, 674-737, 810, 834-844 | Background worker partially untested |
| `core/base_repository.py` | 0% | 7-204 (all) | Base repository completely untested |
| `data/processing/registry.py` | 0% | 7-217 (all) | Processing registry completely untested |
| `db/repositories/aggregated_data_repo.py` | 35% | 56-96, 109-127, 172-178, 193-211, 226-244, 264-287 | Aggregated data repo partially untested |
| `db/repositories/dashboard_filter_repo.py` | 0% | 7-195 (all) | Dashboard filter repo completely untested |
| `db/repositories/dashboard_filter_values_repo.py` | 33% | 43-67, 83-118, 133-139, 153-172 | Filter values repo partially untested |

**Evidence:**
- Coverage report from host run: `TOTAL 7633 statements, 2246 missing, 70.58% coverage`
- `src/mkobi/core/base_repository.py`: 0% — 91 statements, all missing
- `src/mkobi/data/processing/registry.py`: 0% — 70 statements, all missing
- `src/mkobi/db/repositories/dashboard_filter_repo.py`: 0% — 52 statements, all missing
- `src/mkobi/api/routes/dashboards_filters.py`: 26% — 68 statements, 50 missing
- `src/mkobi/api/routes/dashboards_access.py`: 32% — 56 statements, 38 missing

**Recommendation:** Prioritize adding tests for:
1. `api/routes/dashboards_access.py` (32%) — access control is security-critical
2. `api/routes/dashboards_filters.py` (26%) — filter management is a core feature
3. `api/routes/processing_configs.py` (30%) — processing configuration is critical for data pipeline
4. `workers/data_worker.py` (52%) — background worker handles the core data processing
5. `core/base_repository.py` (0%) — base repository is used by all repositories

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 1 |

## Mandatory Fixes

- **TST-001**: Test `test_none_jwt_secret_accepted` fails in Docker due to missing `.env` file — test is environment-dependent
- **TST-002**: Test `test_validate_file_invalid_extension` fails in Docker due to python-magic vs fallback MIME detector — test is environment-dependent
- **TST-003**: Tests `test_seed_script_ruff_mypy` and `test_dev_seeders_module_ruff_mypy` fail in Docker due to ruff cache permission errors

## Advisory Recommendations

- **TST-004**: Tests assert mock call counts instead of behavior outcomes (brittle, tests implementation not behavior)
- **TST-005**: `TestStoreAggregates` mocks entire dependency chain, testing mock wiring not business logic
- **TST-006**: `test_cleanup_task_files_called_during_processing` calls real function then asserts mock — tautological
- **TST-007**: Coverage tool cannot run in Docker container due to file permission issues
- **TST-008**: Critical path coverage gaps in access control, filter management, processing configs, background worker, and base repository

## Doc Updates Needed

None identified in this phase.
