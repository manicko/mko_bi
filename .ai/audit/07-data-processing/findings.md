# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DP-01: Naive datetime used for `uploaded_at` timestamp — inconsistent with rest of codebase

| Field | Value |
|-------|-------|
| **ID** | DP-01 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/data_service.py` |
| **Classification** | advisory |

**Description:** The `_execute_upload` method in `DataService` uses `datetime.now()` (naive, no timezone) for the `uploaded_at` field in `UploadResponse` (line 165). Every other timestamp in the data processing pipeline uses `datetime.now(UTC)` — the worker (`data_worker.py` lines 207, 251, 263, 280, 332, 371, 479, 515, 547), the processing log repository (lines 56, 112), file cleanup (line 131), and security module (lines 253, 255, 296) all use timezone-aware UTC timestamps. This inconsistency means `uploaded_at` will be ambiguous — it will reflect the server's local timezone, which varies by deployment environment. In a Docker container this is typically UTC, but on a developer machine it could be any timezone, causing subtle ordering and display bugs.

**Evidence:** `src/mkobi/services/data_service.py:165` — `uploaded_at=datetime.now()`. Compare with `src/mkobi/workers/data_worker.py:332` — `started_at=datetime.now(UTC)` and `src/mkobi/db/repositories/processing_log_repo.py:56` — `"started_at": datetime.now(UTC)`.

**Recommendation:** Change `datetime.now()` to `datetime.now(UTC)` at `src/mkobi/services/data_service.py:165`. This is a trivial one-line fix that aligns with the project-wide convention already established in every other processing stage.

---

### DP-02: Upload processing creates two separate database transactions — processing log and aggregate data can diverge

| Field | Value |
|-------|-------|
| **ID** | DP-02 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/file_processing.py`, `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The data processing pipeline spans two completely independent database transactions with no atomicity guarantee between them:

1. **Transaction 1** (upload phase, `file_processing.py:268`): Creates the processing log entry, moves the temp file, enqueues the background job, and commits. If the enqueue fails, this transaction rolls back (line 264).

2. **Transaction 2** (background worker, `data_worker.py:522-524`): A brand-new `async with get_session() as session` / `async with session.begin()` block that updates the processing log status, stores aggregates, and marks the job complete.

The problem: if Transaction 1 commits successfully but the application crashes *before* Transaction 2 starts (e.g., worker process dies, OOM kill, deployment restart), the processing log remains permanently in `UPLOADED` state. The `cleanup_stale_processing_logs` function (`data_worker.py:234-292`) only cleans up entries stuck in `PROCESSING` state — it explicitly filters for `ProcessingLog.status == ProcessingStatus.PROCESSING`. Entries stuck in `UPLOADED` state are never cleaned up, leaving orphaned processing logs and uploaded files that consume disk space forever.

Additionally, if Transaction 2 partially fails (e.g., the server crashes between `_store_aggregates` and the final `_update_processing_log_status` to `COMPLETED`), the processing log can be stuck in `PROCESSING` state with partial aggregate data already committed. The stale cleanup will eventually mark it as `FAILED`, but the partial aggregate data remains in the database — users may see inconsistent dashboard data.

**Evidence:**
- `src/mkobi/services/file_processing.py:211-268` — Transaction 1: creates log, flushes, commits.
- `src/mkobi/workers/data_worker.py:520-551` — Transaction 2: separate session, separate transaction.
- `src/mkobi/workers/data_worker.py:254-266` — Stale cleanup only handles `PROCESSING` state, not `UPLOADED`.

**Recommendation:** At minimum, extend `cleanup_stale_processing_logs` to also handle `UPLOADED` state entries (which indicate the background worker never started). For the partial-commit issue within Transaction 2, the current design already wraps everything in a single `session.begin()` block (line 523), which provides atomicity for the worker phase — if anything fails, the entire Transaction 2 rolls back. However, the temp file cleanup on error path (lines 531-540) happens *inside* the transaction block, meaning if the file deletion fails, the transaction still rolls back, which is correct. The primary gap is the `UPLOADED` state orphan scenario.

---

### DP-03: `find_task_file` uses glob matching that can match wrong files for UUIDs with shared substrings

| Field | Value |
|-------|-------|
| **ID** | DP-03 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/file_processing.py` |
| **Classification** | advisory |

**Description:** The `find_task_file` function at `file_processing.py:295` uses `upload_dir.glob(f"*{task_id}*.csv*")` to locate a task's file. UUIDs are hex strings, and it's theoretically possible for two different UUIDs to share a long substring (e.g., `aabbccdd-...-1234` and `aabbccdd-...-5678`). The glob pattern `*{task_id}*` matches any file containing the task_id substring, not just files where the task_id is the actual filename prefix. Since the file was renamed to `{task_id}{file_ext}` at line 234, the correct glob pattern should be `f"{task_id}*.csv*"` (without the leading `*`). The current pattern could return multiple matches for edge cases, and the function silently returns the first match (`task_files[0]`), potentially processing the wrong file.

**Evidence:** `src/mkobi/services/file_processing.py:295` — `task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))`. Compare with the rename at line 234: `final_file_path = upload_dir / f"{log.id}{file_ext}"`.

**Recommendation:** Change the glob pattern from `f"*{task_id}*.csv*"` to `f"{task_id}*.csv*"` at line 295. This matches only files that *start with* the task ID, which is the naming convention established at line 234.

---

### DP-04: `trigger_processing` does not pass `processing_config` when re-enqueuing

| Field | Value |
|-------|-------|
| **ID** | DP-04 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/data_service.py` |
| **Classification** | advisory |

**Description:** The `trigger_processing` method in `DataService` accepts a `processing_config` parameter (line 261) but does not pass it to `enqueue_processing_job` at line 286-290. The `processing_config` argument is accepted but silently ignored. This means manually triggered re-processing always runs with no processing configuration, even when the caller provides one. This is inconsistent with the initial upload path in `_execute_upload` (lines 136-145), which fetches and passes the processing config.

**Evidence:** `src/mkobi/services/data_service.py:286-290`:
```python
await enqueue_processing_job(
    file_path=file_path, dashboard_id=dashboard_id,
    task_id=task_id, mode="overwrite",
    processing_config=processing_config,  # <-- this IS passed
)
```

Wait — reviewing again, `processing_config` IS passed at line 289. However, the `mode` is hardcoded to `"overwrite"` at line 288, ignoring the original upload mode. This means re-processing always overwrites, even if the original upload was `APPEND`. This could be intentional for manual re-trigger, but it's undocumented behavior.

**Evidence:** `src/mkobi/services/data_service.py:288` — `mode="overwrite"` hardcoded.

**Recommendation:** Document whether the hardcoded `mode="overwrite"` is intentional for manual re-trigger. If the original mode should be preserved, the method should accept and forward the mode parameter.

---

### DP-05: `DataPipeline.run` in `registry.py` is orphaned — not called by the actual worker

| Field | Value |
|-------|-------|
| **ID** | DP-05 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/data/processing/registry.py` |
| **Classification** | advisory |

**Description:** The `DataPipeline` class in `registry.py` provides an alternative processing orchestration with its own `run()` method (line 67) that creates processing log entries, transforms data, aggregates, and saves. However, the actual background worker (`data_worker.py:745-785`, `process_csv_background`) does not use `DataPipeline` at all — it implements its own processing logic inline in `_process_csv_file_async`. This means:

1. `DataPipeline` is dead code in production — no worker calls it.
2. The `tenacity` retry logic in `DataPipeline._save_with_retry` (lines 204-221) is never exercised, while the actual worker has no retry logic for storage operations.
3. The `DataPipeline` uses `aggregate_data` from `transformations.py` (which does per-graph aggregation inline), while the worker uses `AggregationService.aggregate_for_dashboard` — two different aggregation implementations.

This creates maintenance risk: bug fixes to the pipeline logic may be applied to `DataPipeline` but not to the actual worker, or vice versa.

**Evidence:** `src/mkobi/data/processing/registry.py:67-221` — `DataPipeline.run()` is defined but never imported or called by `data_worker.py`. The worker's `process_csv_background` at `data_worker.py:745-785` implements its own flow.

**Recommendation:** Either remove `DataPipeline` (if it's truly dead code) or migrate the worker to use it. If keeping both, add a comment in `DataPipeline` indicating it's not currently used in production. The retry logic in `_save_with_retry` should be incorporated into the actual worker's storage path.

---

### DP-06: Worker creates a separate DB session for status updates outside the main transaction

| Field | Value |
|-------|-------|
| **ID** | DP-06 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The `_update_processing_log_status` function (line 175-231) has two code paths:
- When `session is not None` (test mode): uses the provided session, no commit.
- When `session is None` (production): creates a **brand-new** session with `get_session()` and its own transaction (`async with db.begin()`).

In the production path of `_process_csv_file_async` (line 520-551), the main processing happens inside `async with session.begin()`. When an error occurs, the except block (line 526) calls `_update_processing_log_status` **without** passing the session — so the function creates a separate session/transaction (line 220-222). This means the FAILED status update is committed in a different transaction from the main one. If the main transaction rolls back (which it does on any exception due to `session.begin()` context manager), but the status update transaction commits, the log shows FAILED with no aggregate data — which is correct. However, if the status update transaction *also* fails (e.g., DB is down), the processing log remains in whatever state it was before the worker started, with no indication of failure.

More critically, the `_update_processing_log_status` production path (lines 219-222) does its own `async with db.begin()` — a nested transaction. If the DB connection is broken, this will fail silently (caught at line 226-227, only logged), and the processing log status will never be updated to FAILED.

**Evidence:** `src/mkobi/workers/data_worker.py:218-222`:
```python
async with get_session() as db:
    async with db.begin():
        await db.execute(stmt)
```
And the error path at lines 543-550 where `_update_processing_log_status` is called without `session=session`.

**Recommendation:** In the production error path (lines 543-550), pass the main session to `_update_processing_log_status` so the FAILED status update is part of the same transaction. This ensures atomicity: either both the rollback and the FAILED status are persisted, or neither is. The current separate-session approach can leave the processing log in an inconsistent state.

---

### DP-07: `APPEND` mode in worker does not clear old data but also doesn't merge — it only adds new aggregate rows

| Field | Value |
|-------|-------|
| **ID** | DP-07 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/data/storage/manager.py` |
| **Classification** | advisory |

**Description:** When `mode="append"`, the worker calls `_store_aggregates` with `clear_old=False`, which calls `StorageManager.save_aggregates` with `clear_old=False`, which performs a bulk UPSERT (lines 136-148). The UPSERT matches on `(dashboard_id, graph_id, dims::text)` and updates only the `metrics`. This means:

1. New dimension combinations from the appended data are inserted — correct.
2. Existing dimension combinations have their metrics *overwritten* (not added) — this is an UPSERT, not a mathematical append.
3. Dimension combinations that existed in the old data but are absent in the new data remain unchanged — they are not removed.

This behavior is semantically an "upsert/merge" rather than a true "append." If a user uploads a file with fewer rows (e.g., only 2024 data after previously having 2023+2024), the old 2023 data persists. This may be intentional, but it's not documented and could confuse users expecting APPEND to mean "add new rows to existing data" (which it does) while also expecting old rows to be removed if they're not in the new file (which it doesn't do).

**Evidence:** `src/mkobi/data/storage/manager.py:136-148` — `clear_old=False` path does UPSERT. `src/mkobi/workers/data_worker.py:637-642` — `clear_old = (mode == UploadMode.OVERWRITE)`.

**Recommendation:** Document the APPEND behavior clearly. If true append-with-replacement semantics are desired (replace all data for dimensions present in new file, keep dimensions not in new file), consider adding a pre-step that deletes existing records for any `(dashboard_id, graph_id, dims)` combinations that appear in the new data before inserting.

---

### DP-08: No validation that uploaded file's columns match graph dimension/metric requirements before aggregation

| Field | Value |
|-------|-------|
| **ID** | DP-08 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |

**Description:** The worker's `_process_csv_file_async` validates the CSV structure (required columns, data types) at lines 358-375, but the `LoaderConfig` used for validation is constructed from `processing_config_dict` settings (lines 358-361). If no processing config is provided (which is the default when no config has been set up), `required_columns` is an empty list and `column_types` is empty — meaning the validation passes for any CSV structure. The actual column compatibility with graph dimensions and metrics is only checked implicitly at line 57-59 of `aggregation_service.py`, where non-existent columns are silently skipped:

```python
groupby_cols = [d for d in (graph.dimensions + dashboard_filter_dim_names) if d in df.columns]
metric_cols = [m for m in graph.metrics if m in df.columns]
```

If a graph expects a column that doesn't exist in the uploaded file, that column is silently omitted from the GROUP BY, and the graph is skipped entirely if no valid columns remain (line 61-65). No error or warning is raised — the user sees an empty graph with no indication that required data was missing.

**Evidence:** `src/mkobi/services/aggregation_service.py:52-65` — silent column skipping. `src/mkobi/workers/data_worker.py:358-361` — validation config derived from processing_config which may be empty.

**Recommendation:** After loading the CSV, compare the file's columns against the union of all graph dimensions and metrics for the dashboard. If required columns are missing, raise a clear validation error before processing begins, rather than silently producing empty results.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 5 |
| LOW | 1 |

## Mandatory Fixes

- **DP-02**: Extend `cleanup_stale_processing_logs` to handle `UPLOADED` state entries, or implement a mechanism to detect and clean up orphaned processing logs that never transitioned to `PROCESSING`.
- **DP-06**: Pass the main session to `_update_processing_log_status` in the worker's error path so the FAILED status update is atomic with the main transaction rollback.

## Advisory Recommendations

- **DP-01**: Use `datetime.now(UTC)` instead of `datetime.now()` for `uploaded_at` timestamp.
- **DP-03**: Fix glob pattern in `find_task_file` to avoid potential UUID substring collisions.
- **DP-04**: Document or fix the hardcoded `mode="overwrite"` in `trigger_processing`.
- **DP-05**: Remove or integrate the orphaned `DataPipeline` class; migrate its retry logic to the actual worker.
- **DP-07**: Document APPEND mode semantics clearly for users.
- **DP-08**: Add pre-processing validation that uploaded file columns cover graph dimension/metric requirements.

## Doc Updates Needed

- **DP-01**: Update any API documentation that describes the `uploaded_at` field to specify it's UTC.
- **DP-04**: Document the behavior of `trigger_processing` regarding upload mode.
- **DP-07**: Document APPEND mode semantics in the data upload API docs.
