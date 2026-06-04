---
name: audit-findings
description: Audit findings for temp file cleanup gaps in upload and test flows
agent: audit-executor
alwaysApply: false
---

# Audit Findings — Temp File Cleanup Gaps in `data/tmp_uploads`

**Executor:** audit-executor
**Template:** audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### TMP-001: TestCSVLoader leaves orphaned temp files in OS temp directory

| Field | Value |
|-------|-------|
| **ID** | TMP-001 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_data_csv_loader.py` |
| **Classification** | advisory |

**Description:**
`tests/test_data_csv_loader.py` creates `tempfile.NamedTemporaryFile(delete=False)` in 8 test functions but never calls `tmp_path.unlink()` or uses a `try/finally` block to clean up. These files are created in the OS temp directory (`tempfile.gettempdir()`), not in `data/tmp_uploads`, but they accumulate on every test run.

Affected tests:
- `test_load_csv_basic` (line 88)
- `test_load_csv_with_required_columns` (line 104)
- `test_load_csv_missing_required_columns` (line 117)
- `test_load_csv_with_separator` (line 136)
- `test_load_csv_lazy_threshold_respected` (line 151)
- `test_validate_file_size_within_limit` (line 254)
- `test_validate_file_size_exceeds_limit` (line 265)
- `test_get_file_size_mb` (line 278)

**Evidence:**
```python
# tests/test_data_csv_loader.py:88-99
def test_load_csv_basic(self):
    csv_content = b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    loader = CSVLoader()
    df = loader.load_csv(tmp_path)
    # ... assertions but NO tmp_path.unlink() ...
```

**Recommendation:**
Use `pytest`'s `tmp_path` fixture (already used by `test_mime_validation.py`) or wrap in `try/finally` with `tmp_path.unlink(missing_ok=True)`. The `tmp_path` fixture is the idiomatic pytest approach — it auto-cleans after each test.

**Effort:** trivial
**Priority:** recommended

---

### TMP-002: TestStreamingSizeLimit leaves temp dirs but they are OS-temp scoped

| Field | Value | 
|-------|-------|
| **ID** | TMP-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_streaming_size_limit.py` |
| **Classification** | advisory |

**Description:**
`tests/test_streaming_size_limit.py` creates isolated temp directories under `tempfile.gettempdir()` (e.g., `mkobi_streaming_test`, `mkobi_streaming_cleanup_test`, etc.) and some tests verify cleanup of files within them. However, the parent directories themselves are never removed after tests complete. While the files inside are cleaned (verified by assertions), the empty directories remain.

**Evidence:**
```python
# tests/test_streaming_size_limit.py:94
temp_dir = Path(tempfile.gettempdir()) / "mkobi_streaming_test"
# ... used but never deleted ...
```

**Recommendation:**
Use `pytest`'s `tmp_path` fixture or `tempfile.TemporaryDirectory()` context manager for automatic cleanup. Alternatively, add `shutil.rmtree(temp_dir, ignore_errors=True)` in a fixture teardown.

**Effort:** trivial
**Priority:** recommended

---

### TMP-003: Production upload flow — temp file survives when `process_upload_with_session` fails after file move

| Field | Value |
|-------|-------|
| **ID** | TMP-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `src/mkobi/services/file_processing.py` |
| **Classification** | mandatory |

**Description:**
The AGENTS.md states: "Temporary files after processing **must be deleted**." The production upload flow has a gap where files can survive in `data/tmp_uploads`:

**Flow analysis:**

1. `upload_file_endpoint` (upload.py:148) streams upload to `upload_dir / f"upload_{uuid4()}_{filename}"` — the **pre-move temp file**.
2. `process_upload_with_session` (file_processing.py:236) moves the file via `file_path.replace(final_file_path)` to `upload_dir / f"{task_id}.csv"` — the **post-move file**.
3. The `finally` block (upload.py:203-208) cleans up the **pre-move temp file** if it still exists (i.e., if `replace()` didn't happen).
4. The background worker `_process_csv_file_async` (data_worker.py:308-310) deletes the **post-move file** after successful processing.
5. The background worker also deletes the **post-move file** on processing error (data_worker.py:332-340).

**Gap — pre-move temp file cleanup on streaming size rejection:**
When the streaming size check triggers during upload (upload.py:158-172), the code calls `temp_file_path.unlink(missing_ok=True)` manually. This is correct.

**Gap — post-move file NOT cleaned up by `cleanup_task_files`:**
The `cleanup_task_files` function in `file_cleanup.py` exists but is **never called** in the production upload/processing flow. It is only called manually in tests. The background worker deletes the file directly, so this is not a runtime leak under normal conditions.

**Gap — post-move file survives worker crash between `replace()` and `process_csv_background` completion:**
If the worker process crashes after the file is moved to the final location but before `_process_csv_file_async` completes, the file remains in `data/tmp_uploads` forever. The `cleanup_stale_temp_files` function exists but is **never scheduled** in the application startup.

**Evidence:**
- `file_cleanup.py:cleanup_stale_temp_files()` — exists but never called at startup
- `file_cleanup.py:cleanup_task_files()` — exists but never called in production flow
- No startup hook in `main.py` or `config.py` that schedules stale file cleanup
- 290+ files currently in `data/tmp_uploads` (confirmed on disk)

**Recommendation:**
1. Call `cleanup_stale_temp_files()` on application startup (e.g., in `Settings.__init__` or as a FastAPI startup event) to clean up orphaned files from previous runs.
2. Optionally schedule periodic cleanup using `start_stale_processing_cleanup_task` pattern already established for stale processing logs.

**Effort:** small
**Priority:** recommended

---

### TMP-004: `test_temp_file_deleted_after_successful_upload` may leave files when processing has no graphs

| Field | Value |
|-------|-------|
| **ID** | TMP-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `tests/test_upload_api.py` |
| **Classification** | advisory |

**Description:**
The test `test_temp_file_deleted_after_successful_upload` (line 626) calls `process_csv_background` directly with `db_session=async_db_session`. The processing function `_process_csv_file_async` calls `_store_aggregates`, which queries for graphs. If no graphs exist for the dashboard, `_store_aggregates` returns early (line 403-404: `if not graph_reads: ... return`), and the file is still cleaned up by the worker (line 308-310). So the file IS cleaned up correctly.

However, the test does not create any graphs for the dashboard, so the processing is essentially a no-op that just reads and discards the CSV. The test passes because the worker's cleanup runs regardless. But this means the test doesn't actually verify the full processing pipeline — it only verifies that the worker cleans up after itself.

**Evidence:**
```python
# test_upload_api.py:680-843
# No graph is created for test_dashboard_for_cleanup
# _store_aggregates returns early at line 403-404 of data_worker.py
# File cleanup at line 308-310 still runs
```

**Recommendation:**
Create a minimal graph in the test setup so the full processing pipeline is exercised. This makes the test more meaningful and catches regressions in the aggregation path.

**Effort:** small
**Priority:** recommended

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

- **TMP-003**: Production upload flow — `cleanup_stale_temp_files` is never scheduled, leaving orphaned files from crashes/restarts. This is a spec deviation from AGENTS.md rule "Temporary files after processing must be deleted."

## Advisory Recommendations

- **TMP-001**: `TestCSVLoader` tests leak temp files in OS temp directory (use `tmp_path` fixture).
- **TMP-002**: `TestStreamingSizeLimit` tests leave empty directories in OS temp directory.
- **TMP-004**: `test_temp_file_deleted_after_successful_upload` doesn't create graphs, so it tests only the no-op path.

## Doc Updates Needed

- Document the stale file cleanup startup behavior once implemented (in `docs/11-guides/docker.md` or `docs/99-reference/run-guide.md`).
- Update `docs/00-overview/doc-maintenance-rules.md` if new cleanup patterns are established.

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `TMP-001`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` or `advisory` |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements
