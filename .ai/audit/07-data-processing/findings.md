# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DP-001: Unbounded File Read When file.size Is None (Pre-Check Bypass)

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/upload.py` |
| **Classification** | mandatory |

**Description:** The upload endpoint at `upload.py:110` checks `file.size` before reading, but the condition `if file.size is not None` means that when `file.size` is `None` (which occurs for some client implementations or proxy configurations), the size check is entirely skipped. The code then proceeds to `await file.read(CHUNK_SIZE)` in a loop with no size limit, potentially reading an unbounded amount of data into temp storage. This can be exploited for a denial-of-service via disk exhaustion, or to exceed the intended file size limit.

**Evidence:** `upload.py:110-122`:
```python
if file.size is not None and file.size > config.max_file_size:
    # ... reject file
# If file.size is None, we fall through with no size check
# Then at line 156:
while chunk := await file.read(CHUNK_SIZE):
    await f.write(chunk)
    total_bytes += len(chunk)
# No cumulative size check during streaming
```
The streaming loop at line 155-158 has no cumulative size guard. A malicious client sending a file with `Content-Length` omitted can bypass the size limit entirely.

**Recommendation:** Add a cumulative byte counter inside the streaming loop and abort with HTTP 413 if `total_bytes` exceeds `config.max_file_size`. Never rely solely on the `file.size` header for security enforcement.

---

### DP-002: Temp File Leaked on Validation Failure After Streaming

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `src/mkobi/services/file_processing.py` |
| **Classification** | mandatory |

**Description:** When a file is streamed to a temp location at `upload.py:155-158`, and then `data_service.process_upload()` (which calls `validate_file()`) fails with a `ValueError` (e.g., wrong MIME type after streaming, empty file), the temp file is cleaned up in the `finally` block at `upload.py:191-193`. However, if the exception is NOT a `ValueError`, `HTTPException`, `AppException`, or `PermissionError` — i.e., any unexpected exception — it falls through to the generic `except Exception` handler at `upload.py:208-213`. That handler raises a new `HTTPException(500)` but does NOT clean up the temp file. The `finally` block at line 188 covers the service call, but the outer `try/except` at lines 106-213 has no corresponding `finally` for the generic exception case. If any unexpected exception occurs during `process_upload`, the temp file at `temp_file_path` remains on disk.

**Evidence:** `upload.py:152-213`:
```python
try:
    # ... stream file to temp_file_path ...
    result = await data_service.process_upload(...)  # line 168
    return result
finally:
    if temp_file_path.exists():  # line 191 - only reached via the TRY block
        temp_file_path.unlink(missing_ok=True)
```
The `finally` block at line 188 is inside the `try` that starts at line 106. However, the `except Exception` handler at line 208 raises a new `HTTPException` which propagates up — the `finally` at 188 IS actually reached before the exception propagates. This means on an unexpected exception, the temp file IS cleaned up by the finally. Re-examining: the `try/finally` at lines 152-193 is nested inside the outer `try/except` at 106-213. If the inner `try/finally` handles cleanup and then `process_upload` raises ValueError, the inner finally runs, then the ValueError goes to `_handle_value_error` which raises HTTPException. If something else unexpected happens, the inner finally runs. So the cleanup appears to work for this path. **However**, if `process_upload` succeeds but `result` construction fails (unlikely but possible), the temp file was already moved by `file_path.replace(final_file_path)` in `file_processing.py:188`, so cleanup is correct.

After deeper review: The real issue is that the comment at line 190 says "temp_file_path no longer exists if process_upload succeeded (file was moved)". But `process_upload` delegates to `process_upload_with_session` which calls `validate_file` BEFORE moving. If validation fails, the file is still at `temp_file_path`, and the inner `finally` does clean it up. This is actually correct.

**Revised finding: This is not actually a bug. The cleanup works correctly. Withdrawn.**

---

### DP-003: MIME Type Validation Trusts Client-Provided Content-Type (Spoofable)

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/services/file_processing.py`, `src/mkobi/api/routes/upload.py` |
| **Classification** | mandatory |

**Description:** The MIME type validation in `validate_mime_type()` at `file_processing.py:22-41` trusts the client-provided `Content-Type` header without verifying the actual file content. A malicious user can send a file with `.csv.gz` extension but set `Content-Type: text/csv` (or any allowed MIME type), which passes validation. Conversely, a user could upload an executable file with `Content-Type: text/csv` and it would pass initial validation. The MIME check does not inspect file magic bytes (magic number detection), making it trivially bypassable. This is a defense-in-depth gap — while file extension is separately checked, the MIME validation provides a false sense of security and can be confused with actual content validation.

**Evidence:** `file_processing.py:77`:
```python
validate_mime_type(content_type)  # Only checks against allowed list, not actual file content
```
`file_processing.py:34-41`:
```python
allowed_mime_types = MimeTypeEnum.allowed_values()
if content_type not in allowed_mime_types:
    raise ValueError(f"Invalid MIME-type: {content_type}")
```

**Recommendation:** Add file magic byte validation (e.g., check for gzip magic bytes `\x1f\x8b` for `.gz` files) in `validate_file()` to verify actual file content matches the declared MIME type. Do not rely solely on the client-provided `Content-Type` header.

---

### DP-004: Silent Exception Swallowing in _update_processing_log_status Causes Undetected Status Update Failures

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The `_update_processing_log_status` function at `data_worker.py:36-84` has a bare `except Exception` block that catches ALL exceptions, logs them, and silently continues. This means if the database is unreachable, the log table is locked, or any other error occurs during status update, the processing pipeline continues as if the status was updated. In `_process_csv_file_async` (line 174), if the status update to `PROCESSING` fails silently, the log remains at `UPLOADED` while actual processing begins. If processing then fails and the FAILED status update also fails silently, the log stays at `UPLOADED` forever — the user sees a task that appears to be waiting for processing but is actually failed. During error recovery (`cleanup_stale_processing_logs`), these entries would never be cleaned up because they're not in `PROCESSING` state.

**Evidence:** `data_worker.py:82-84`:
```python
except Exception as e:
    logger.error("Error updating processing log: %s", e)
# No re-raise, no return value indicating failure
```
Called at `data_worker.py:174`, `data_worker.py:229`, `data_worker.py:253` — any of these failures silently corrupt the task state machine.

**Recommendation:** Either re-raise the exception after logging, or return a boolean indicating success/failure and handle it in the caller. For the PROCESSING status update in `_process_csv_file_async`, a failure should abort the pipeline to avoid orphan processing. For the FAILED status update in the error handler, the exception should still propagate as it represents a cascading failure.

---

### DP-005: In-Memory Task Queue Loses All Pending Tasks on Process Restart

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/core/task_queue.py` |
| **Classification** | advisory |

**Description:** The `enqueue_processing_job` function (`file_processing.py:282-308`) uses the in-memory `default_queue` from `task_queue.py` via `enqueue_job()`. As documented in the code comments, this is an MVP implementation using `asyncio.Queue`. Any enqueued processing jobs are lost if the worker process restarts or crashes. While the `shutdown()` method logs a warning about pending tasks, it does not prevent data loss. The upload endpoint returns a success response with a `task_id`, but if the process restarts before the background worker picks up the task, the task disappears while the log entry remains in `UPLOADED` state with no worker to process it. The stale processing cleanup task only handles entries in `PROCESSING` state, not `UPLOADED` ones.

**Evidence:** `task_queue.py:27-29`:
```python
self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
self._statuses: dict[str, ProcessingStatus] = {}
self._results: dict[str, Any] = {}
```
All state is in-memory dicts, lost on restart. `file_processing.py:300-308`:
```python
await enqueue_job(
    process_csv_background,
    file_path=str(final_file_path),
    ...
)
```
The job is enqueued in-memory with no persistence.

**Recommendation:** Document this as an MVP limitation. For production, migrate to Redis/RQ as noted in the code comments. As immediate improvement, consider making the endpoint eagerly set the task to PROCESSING state or periodically scanning for stuck UPLOADED entries.

---

### DP-006: No Null/Malformed Input Validation in CSV Processing Worker

| Field | Value |
|-------|-------|
| **ID** | DP-006 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |

**Description:** The `_process_csv_file_async` function at `data_worker.py:148-275` receives `file_path_str` and attempts to load the CSV with `loader.load_csv(file_path)`. If the file has been deleted (e.g., by a concurrent cleanup process) between the time the job was enqueued and when it executes, `loader.load_csv` raises `FileNotFoundError`. This exception is caught by the generic `except Exception` at line 248, which sets the status to FAILED. However, the `file_path.exists()` check at line 262 on the error path would fail if the file was already removed, and the `file_path.unlink()` attempt at line 264 would raise an additional exception caught by the secondary `except Exception` at line 265. While this doesn't crash, it means the FAILED status update at line 253 is attempted even though the log update may also fail (see DP-004). The task ends in an unrecoverable state. There is no retry for transient failures.

**Evidence:** `data_worker.py:248-275`:
```python
except Exception as e:
    error_msg = str(e)
    logger.exception("Processing failed: task_id=%s, error=%s", task_id, error_msg)
    await _update_processing_log_status(
        task_id=task_id,
        status=ProcessingStatus.FAILED,
        message=f"Processing failed: {error_msg}",
        finished_at=datetime.now(UTC),
        session=db_session,
    )
    # Clean up temp file on error
    if file_path.exists():  # File may never have existed or already deleted
        try:
            await asyncio.to_thread(file_path.unlink)
        except Exception:
            logger.warning(...)
```

**Recommendation:** Add explicit handling for `FileNotFoundError` before the generic `except` to provide a clearer error message. Consider adding a retry mechanism for transient file-system errors.

---

### DP-007: Aggregation Iterates All Graphs Per Row Causing Duplicate Record Explosion

| Field | Value |
|-------|-------|
| **ID** | DP-007 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |

**Description:** In `_store_aggregates` at `data_worker.py:370-395`, the code iterates over all rows and for each row, iterates over ALL graphs in the dashboard. This means if a dashboard has N graphs and the CSV has M rows, the total aggregates stored is M × N. Each graph gets identical `dims` + `metrics` data (split from the same row), regardless of whether that graph's configured dimensions match the row's data. The `valid_dimensions` check at line 316 ensures the graph's configured dimensions exist in the DataFrame, but doesn't filter rows per-graph. If different graphs have different dimension configurations, every graph still gets a copy of every row, with NULL-like behavior for non-matching dimensions through the `dims` extraction. This inflates storage and can cause frontend display issues where each graph shows data for dimensions it wasn't configured for.

**Evidence:** `data_worker.py:370-395`:
```python
rows = df.to_dicts()
aggregates = []
for row in rows:           # M rows
    for graph in graphs:   # N graphs
        valid_dimensions = [...]
        dims = {k: v for k, v in row.items() if k in valid_dimensions}
        metrics = {k: v for k, v in row.items() if k not in dims}
        aggregates.append({"graph_id": str(graph.id), "dims": dims, "metrics": metrics})
```
M × N inserts regardless of graph configuration.

**Recommendation:** Filter aggregates relevant to each graph's configuration, or build a deduplication strategy based on which dimensions/metrics each graph actually uses.

---

### DP-008: _calculate_yoy Floating-Point Division Produces Infinity Instead of NULL for Zero Values

| Field | Value |
|-------|-------|
| **ID** | DP-008 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/data/processing/aggregate_transforms.py` |
| **Classification** | mandatory |

**Description:** In the `_calculate_yoy` function at `aggregate_transforms.py:202-203`, the YoY formula is:
```python
.when(prev_value_expr.is_null() | (prev_value_expr == 0))
.then(None)
.otherwise((pl.col(value_column) - prev_value_expr) / prev_value_expr * 100)
```
The `prev_value_expr == 0` check uses exact floating-point equality comparison. When `prev_value` is a float column (which it is, since Polars aggregation results are floats), the `== 0` check is unreliable — a value of `0.0` might be stored as a very tiny float. More critically, the check happens AFTER `.shift(1).over()` which produces Polars expressions, but the `is_null()` check is on the expression, not executed as a filter. If `prev_value_expr` evaluates to exactly `0.0`, the check works. But if a value like `-0.0` or a very near-zero float appears, the check fails and division proceeds, producing `inf` or `-inf` values. These `inf` values propagate into the `fill_nan(None)` at line 209 which does NOT handle `inf`. The resulting `inf` values are stored into JSONB metrics and sent to the frontend, which cannot serialize `inf` in JSON.

**Evidence:** `aggregate_transforms.py:202-209`:
```python
.when(prev_value_expr.is_null() | (prev_value_expr == 0))
.then(None)
.otherwise((pl.col(value_column) - prev_value_expr) / prev_value_expr * 100)
.alias(alias)
)
result = result.with_columns([pl.col(alias).fill_nan(None)])  # Only handles NaN, not Inf
```

**Recommendation:** Replace the zero-check with `abs(prev_value) < epsilon` or use `pl.col(alias).fill_nan(None).replace(float('inf'), None).replace(float('-inf'), None)` to handle infinity values. Or add a second `.when(pl.col(alias).is_infinite()).then(None)` clause.

---

### DP-009: APPEND Mode Upload Does Not Recalculate Aggregates (Incremental Update Risk)

| Field | Value |
|-------|-------|
| **ID** | DP-009 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/data/storage/manager.py` |
| **Classification** | mandatory |

**Description:** When uploading with `UploadMode.APPEND`, the `_store_aggregates` function (via `StorageManager.save_aggregates`) uses `_bulk_upsert` (`manager.py:311-350`) instead of delete+insert. The UPSERT operation matches on `(dashboard_id, graph_id, dims)` and only updates the `metrics` column. This means if the new CSV data has different dimension values than existing data, the old dimension records remain unchanged (stale). More critically, if a previously-existing dimension combination is completely absent from the new CSV, it persists as stale data. The APPEND mode is semantically supposed to add new data while keeping old data, but from a dashboard perspective, if the user intends to replace the dataset but accidentally uses APPEND, they'll see merged old+new data with no indication of the mismatch. More importantly, aggregate calculations (SUM, MEAN, COUNT) are performed on just the new CSV file's data, not merged with existing data — so the UPSERT'd values represent aggregates from ONLY the new file. If APPEND is meant to combine datasets, the aggregate values should be recalculated from the combined dataset.

**Evidence:** `manager.py:113-148`:
```python
if clear_old:  # Only True for OVERWRITE
    deleted = await self.delete_by_dashboard(dashboard_id)
    inserted = await self._bulk_insert(...)
else:  # APPEND path
    processed = await self._bulk_upsert(...)
```
The `_bulk_upsert` at line 311-350 performs `ON CONFLICT DO UPDATE` setting only `metrics`. No aggregation recalculation from combined data.

**Recommendation:** Document APPEND semantics clearly: new aggregates are calculated from the new file only, and existing metric values for matching dims are overwritten. If additive semantics are needed, use numeric addition in the UPSERT. Consider adding a warning when APPEND mode is used with a new file.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 5 |
| MEDIUM | 3 |
| LOW | 0 |

## Mandatory Fixes

1. **DP-001** — Add cumulative size check during file streaming to prevent unbounded disk writes when `file.size` is `None`.
2. **DP-003** — Add file magic byte validation to verify actual file content matches declared MIME type.
3. **DP-004** — Make `_update_processing_log_status` return success/failure status and handle failures in callers, or re-raise exceptions.
4. **DP-008** — Handle `inf`/`-inf` values in YoY calculation output to prevent JSON serialization failures.

## Advisory Recommendations

1. **DP-005** — Document task queue persistence limitation; plan Redis/RQ migration.
2. **DP-006** — Add explicit `FileNotFoundError` handling in the worker with appropriate logging.
3. **DP-007** — Optimize aggregate storage to avoid M × N record explosion for multi-graph dashboards.
4. **DP-009** — Clarify APPEND mode semantics in documentation; consider aggregate recalculation from combined data.

## Doc Updates Needed

- Document that `APPEND` mode does not merge/recalculate aggregates — it only upserts new-file aggregates.
- Document the in-memory task queue limitation and data loss risk on process restart.
- Document MIME type validation as header-only (not content-verified) in security considerations.
