# Phase 01 Audit Findings — Backend Architecture

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no
**problems-only:** true

---

## Findings

### BE-001: Failing Test — JWT Secret None Accepted Despite Env Fallback

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `tests/test_config.py`, `src/mkobi/config.py` |
| **Classification** | mandatory |

**Description:** Test `test_none_jwt_secret_accepted` expects that when `JWT__SECRET_KEY` is unset via `monkeypatch.delenv`, the settings fallback to the `.env` file value. However, the Docker test container does NOT have a `.env` file — `JWT__SECRET_KEY` is set via the compose file environment (`test_jwt_secret_key_for_integration_tests_32_chars`). When `monkeypatch.delenv` removes it, there is no `.env` fallback in the container, and the YAML config file has no JWT secret (it's commented out). The test then asserts `settings.jwt.secret_key == "dev-secret-key-for-security-testing..."` but gets `None` because no source provides the expected value.

**Evidence:**
- Test failure output: `assert None == 'dev-secret-key-for-security-testing-do-not-use-in-prod-32chars'`
- File: `tests/test_config.py:384`
- Docker test container env: `JWT__SECRET_KEY=test_jwt_secret_key_for_integration_tests_32_chars` (set in compose)
- Docker test container has no `.env` file: `os.listdir('.')` shows no `.env`
- The `.env` file at `C:\py_dev\mkobi\.env:18` sets `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars` but this file is NOT mounted into the test container
- YAML config `src/mkobi/settings/app.yaml` has JWT secret commented out

**Recommendation:** Either (a) Mount the `.env` file into the test container in `docker-compose.test.yml`, or (b) Update the test to not depend on `.env` file fallback (use `monkeypatch.setenv` with the expected value instead of `delenv`), or (c) Set `JWT__SECRET_KEY` in the test compose file to the expected test value.

---

### BE-002: Failing Test — File Validation Error Message Mismatch

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `tests/test_data_service.py`, `src/mkobi/services/file_processing.py` |
| **Classification** | mandatory |

**Description:** Test `test_validate_file_invalid_extension` expects the error message `"Invalid file format.*test.txt"` when validating a `.txt` file, but the actual error message is `"Detected MIME type text/plain not allowed"`. The test was written when validation checked extension first, but the current implementation performs MIME type detection BEFORE extension checking. This means a `.txt` file with CSV-like content fails at the MIME validation step (because `text/plain` is not in allowed MIME types), never reaching the extension check.

**Evidence:**
- Test failure output: `Expected regex: 'Invalid file format.*test.txt'` vs `Actual message: 'Detected MIME type text/plain not allowed'`
- File: `tests/test_data_service.py:569`
- File: `src/mkobi/services/file_processing.py:106-116` — `validate_mime_type()` runs before extension check in `validate_file()`
- The MIME type detection correctly identifies `text/plain` for `.txt` files, which is rejected before extension check

**Recommendation:** Update the test to match the actual validation order. Change the expected regex to match the MIME type error. Alternatively, if the spec requires extension-then-MIME ordering, reorder the validation. The current MIME-first approach is actually more secure (prevents spoofing), so the test should be updated, not the code.

---

### BE-003: Failing Tests — Dev Seeder Ruff/Mypy Permission Errors in Docker

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | LOW |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `tests/test_dev_seeders.py`, `src/mkobi/db/seeders/test_media_dash.py`, `src/mkobi/db/dev_seeders.py` |
| **Classification** | advisory |

**Description:** Tests `test_seed_script_ruff_mypy` and `test_dev_seeders_module_ruff_mypy` fail because the Docker container's non-root `app` user cannot write to the `.ruff_cache` directory. This is a Docker permission issue, not a code quality issue. The seed files themselves may be fine — the test tries to run `ruff check` inside the container and fails due to filesystem permissions. This causes false negatives in CI/quality checks.

**Evidence:**
- Test failure output: `error: Failed to initialize cache at /app/.ruff_cache: Permission denied (os error 13)`
- Test failure output: `ruff failed  Cause: Failed to create temporary file  Cause: No such file or directory (os error 2) at path "/app/.ruff_cache/0.15.17/.tmpCceot2"`
- Files: `tests/test_dev_seeders.py:198`, `tests/test_dev_seeders.py:223`

**Recommendation:** Either (a) disable these tests in Docker environments (they serve only as quality verification of seed scripts on the host), (b) Set `RUFF_CACHE_DIR` to a writable temp directory inside the test, or (c) ensure the Docker `.ruff_cache` volume is writable by the `app` user. The simplest fix is to set `os.environ["RUFF_CACHE_DIR"] = tempfile.mkdtemp()` in the test before running ruff.

---

### BE-004: Redundant Casts in Processing Log Service

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/processing_log_service.py` |
| **Classification** | advisory |

**Description:** mypy reports 5 `redundant-cast` errors in `processing_log_service.py`. The code uses `cast()` to tell the type checker to treat objects as specific types, but the objects are already of those types. This reduces code clarity and adds unnecessary noise.

**Evidence:**
- mypy output:
  - `src/mkobi/services/processing_log_service.py:78: error: Redundant cast to "list[ProcessingLogRead]"`
  - `src/mkobi/services/processing_log_service.py:85: error: Redundant cast to "list[ProcessingLogRead]"`
  - `src/mkobi/services/processing_log_service.py:224: error: Redundant cast to "list[ProcessingLogRead]"`
  - `src/mkobi/services/processing_log_service.py:249: error: Redundant cast to "int"`
  - `src/mkobi/services/processing_log_service.py:255: error: Redundant cast to "int"`
- File: `src/mkobi/services/processing_log_service.py:78, 85, 224, 249, 255`

**Recommendation:** Remove the `cast()` calls at lines 78, 85, 224, 249, 255 since the values are already of the correct type. If the repository interfaces return `Any`, update them to return proper types instead of using `cast()`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 2 |

## Mandatory Fixes

| ID | Description | Severity |
|----|-------------|----------|
| BE-001 | JWT secret test failure due to test environment/env interaction | HIGH |
| BE-002 | File validation error message mismatch (MIME-first vs extension-first) | MEDIUM |

## Advisory Recommendations

| ID | Description | Severity | Effort |
|----|-------------|----------|--------|
| BE-003 | Docker permission issue for ruff cache in dev seeder tests | LOW | Trivial |
| BE-004 | Remove redundant `cast()` calls in processing_log_service.py | LOW | Trivial |

## Doc Updates Needed

None identified in this phase.

---

## Audit Evidence

### Runtime Verification (R1) — Linters and Type Checkers
- **Ruff**: Passed — `All checks passed!` (exit code 0)
- **mypy**: 5 errors found in `src/mkobi/services/processing_log_service.py` (redundant casts, see BE-004)

### Runtime Verification (R2) — Import Verification
- `src/mkobi/main.py` successfully imports all required dependencies
- `app = create_app()` factory pattern confirmed working

### Runtime Verification (R3) — Dead Code Analysis
- No dead code found beyond documented compatibility APIs (deprecated classmethods in `StorageManager`)
- All routes registered in `__init__.py` are mounted in `app.py`

### Runtime Verification (R3-SPEC) — Dead Code vs Specification
- Deprecated methods (`save_aggregated_data`, `clear_graph_data_compat`, `clear_dashboard_data_compat`) are in `StorageManager` for backward compatibility — documented via `.. deprecated::` docstrings and `DeprecationWarning`

### Runtime Verification (R4) — Backend Tests
- **Total**: 870 passed, 4 failed, 17 warnings
- **Failures**:
  1. `test_none_jwt_secret_accepted` — JWT env fallback test (BE-001, HIGH)
  2. `test_validate_file_invalid_extension` — Error message mismatch (BE-002, MEDIUM)
  3. `test_seed_script_ruff_mypy` — Docker permission issue (BE-003, LOW)
  4. `test_dev_seeders_module_ruff_mypy` — Docker permission issue (BE-003, LOW)

### Runtime Verification (R5) — API Contract Verification
- All 17 route modules in `src/mkobi/api/routes/__init__.py` are mounted in `app.py` under `/api/v1`
- Routes: `auth`, `users`, `dashboards` (combined), `graphs`, `layouts`, `upload`, `data`, `client_errors`, `processing_configs`, `processing_logs`, `admin`
- `dashboards.py` combines 5 sub-routers: `crud`, `access`, `filters`, `graphs`, `filter_values`
- Health endpoints: `/health` (basic), `/health/detailed` (components)
