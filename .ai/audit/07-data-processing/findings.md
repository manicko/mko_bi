# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete

---

## Findings

### DP-001: Transaction Boundary Issue — Orphaned File After Failed Commit

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/services/file_processing.py`, `src/mkobi/api/routes/upload.py` |
| **Classification** | mandatory |

**Description:**
In `process_upload_with_session` (file_processing.py:114-206), the file move operation (`file_path.replace(final_file_path)` at line 171) occurs before `await db.commit()` at line 185. If the file move succeeds but the database commit fails (e.g., due to constraint violation, deadlock, or connection error), the file is left at the final location with no corresponding database record. This creates orphaned files and an inconsistent system state. Similarly, the processing log creation at line 161-167 is flushed but not yet committed, leaving a window where partial state exists.

**Evidence:**
```python
# file_processing.py:146-185
log = await log_repo.create_log(...)  # Creates log entry
await db.flush()                      # Flushes but not committed
file_path.replace(final_file_path)     # File moved to final location
await db.commit()                     # If this fails, file is orphaned
```

**Recommendation:**
Wrap both the log creation and file operations in a single transaction. If the commit fails, ensure the temp file is moved back or deleted. Use try/except to handle rollback scenarios and clean up orphaned files. Consider creating the log entry within the same transaction context as the file move, or move the file only after the commit succeeds.

---

### DP-002: Processing Configuration Ignored in Pipeline

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/file_processing.py`, `src/mkobi/services/data_service.py` |
| **Classification** | mandatory |

**Description:**
The `processing_config` stored in the `processing_configs` database table is never retrieved or applied during the data processing pipeline. The `ProcessingConfig` model (processing_configs.py) defines `settings` including `loader`, `date_column`, and `timezone` fields, but `process_upload_with_session` and `enqueue_processing_job` do not fetch this configuration. Consequently, `process_csv_background` receives `processing_config_dict=None` (line 191 in data_service.py), and all processing happens without the configured transformation rules.

**Evidence:**
- `data_service.py:240-273` - `trigger_processing` method never fetches `ProcessingConfig` from database
- `file_processing.py:188-197` - `enqueue_processing_job` passes `processing_config_dict=None`
- `data_worker.py:148-226` - `processing_config_dict` parameter receives `None` and is used conditionally, affecting zero users

**Recommendation:**
Fetch `ProcessingConfig` from the database in `trigger_processing` or `process_csv_background` using the dashboard_id, and pass it through to `_process_csv_file_async`. The configuration should define transformations, aggregations, and processing rules that are applied to the data.

---

### DP-003: Missing Transaction Wrapper in Test Mode for _store_aggregates

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:**
In `_store_aggregates` (data_worker.py:278-410), when `db_session` is provided (test mode code path at lines 297-351), there is no explicit transaction wrapper. The code performs delete operations and bulk inserts within the provided session, but without `session.begin()`, partial writes can be committed on error. Production mode (lines 352-410) correctly uses `async with session.begin()`, but the test mode path lacks this protection.

**Evidence:**
```python
# data_worker.py:297-351 (test mode - no transaction wrapper)
if db_session is not None:
    result = await session.execute(...)  # No begin() wrapper
    graphs = result.scalars().all()
    # ... deletes and inserts without transaction protection
```

vs.

```python
# data_worker.py:355-357 (production mode - correct)
async with session.begin():  # Proper transaction wrapper
    result = await session.execute(...)
```

**Recommendation:**
Add explicit transaction control (`async with db_session.begin()` or ensure the calling code wraps in a transaction) for the test mode code path, or restructure the code to use a shared implementation path that handles both cases consistently.

---

### DP-004: In-Memory Task Queue Not Persistent Across Restarts

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/core/task_queue.py` |
| **Classification** | mandatory |

**Description:**
The `TaskQueue` class (task_queue.py:18-118) uses in-memory storage (`self._queue`, `self._statuses`, `self._results`, `self._errors` dictionaries) to track task status. While the code mentions "For production, replace with Redis/RabbitMQ" in the docstring, the actual implementation means:
1. All in-flight tasks are lost on application restart
2. Task status is not shared between multiple worker processes
3. The `STARTED` -> `PROCESSING` -> `SUCCESS/FAILED` state transitions exist only in memory

**Evidence:**
```python
# task_queue.py:27-30
self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
self._statuses: dict[str, ProcessingStatus] = {}
self._results: dict[str, Any] = {}
self._errors: dict[str, str | None] = {}
```

The stale processing cleanup (data_worker.py:87-145) attempts to recover from this by checking the database, but the primary queue mechanism is non-persistent.

**Recommendation:**
Replace the in-memory `TaskQueue` with a persistent implementation using Redis or RQ (Redis Queue), or ensure that task status is always persisted to the `processing_logs` table before any in-memory state changes. The current implementation should at minimum persist state changes before operating on them.

---

### DP-005: No Validation for Invalid Decimal Precision in Aggregations

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/data/processing/aggregate_transforms.py` |
| **Classification** | advisory |

**Description:**
The `_calculate_share` function (aggregate_transforms.py:218-251) performs floating-point division for share calculations without considering precision drift. When dividing values that don't result in exact floating-point representations (e.g., 1/3 = 0.333...), the accumulated errors could lead to inconsistent results. Additionally, the function silently handles division by zero by returning 0.0 (lines 246-248) but doesn't log this edge case for debugging.

**Evidence:**
```python
# aggregate_transforms.py:240-242
result = df.with_columns(
    pl.when(pl.col("total") == 0).then(0.0).otherwise(pl.col(value_column) / pl.col("total") * 100).alias(alias)
)
```

**Recommendation:**
Consider using `pl.Decimal` precision for financial calculations or Round to a fixed precision before storage. Add warning logs when total is zero to help identify data quality issues.

---

### DP-006: ProcessingStatus.COMPLETED Enum Value Never Used

| Field | Value |
|-------|-------|
| **ID** | DP-006 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/enums.py` |
| **Classification** | advisory |

**Description:**
The `ProcessingStatus` enum (enums.py:58-66) defines a `COMPLETED` status alongside `SUCCESS`, but `COMPLETED` is never used anywhere in the codebase. All successful processing completes with `ProcessingStatus.SUCCESS`, creating confusion about the intended state machine.

**Evidence:**
```python
# enums.py:58-66
class ProcessingStatus(StrEnum):
    STARTED = "started"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    COMPLETED = "completed"  # Never used
```

**Recommendation:**
Either remove the unused `COMPLETED` status or document its intended use. If it represents a different state (e.g., all graphs processed), implement the logic to transition to it.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 1 |

---

## Mandatory Fixes

1. **DP-001** - Transaction boundary issue in `process_upload_with_session` causing potential orphaned files
2. **DP-002** - Processing configuration ignored in the data processing pipeline
3. **DP-003** - Missing transaction wrapper in test mode for `_store_aggregates`
4. **DP-004** - In-memory task queue not persistent across restarts

---

## Advisory Recommendations

1. **DP-005** - Consider decimal precision handling for share calculations
2. **DP-006** - Clean up unused `ProcessingStatus.COMPLETED` enum value