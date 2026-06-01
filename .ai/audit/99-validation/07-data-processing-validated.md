# Validation Report — Phase 07: Data Processing Pipeline

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/07-data-processing/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted (unchanged) | Rejected | Reclassified | Merged |
|----------------|-------|----------------------|--------------|--------|
| Mandatory | 5 | 3 | 1 | 1 | 0 |
| Advisory | 4 | 3 | 0 | 0 | 1 |
| **Total** | **9** | **6** | **1** | **1** | **1** |

---

## Rejected Findings

### DP-002: Temp File Leaked on Validation Failure After Streaming — REJECTED

**Original Severity:** MEDIUM
**Original Type:** RUNTIME-ERROR
**Original Classification:** mandatory

**Rejection reason:** The audit executor **self-withdrew** this finding in the original document (line 66: "Revised finding: This is not actually a bug. The cleanup works correctly. Withdrawn."). Code review confirms the withdrawal is correct:

1. The `try/finally` block at `upload.py:152-193` properly wraps the streaming + service call. The `finally` at line 188-193 runs for ALL exit paths from the inner `try` block (normal return, `ValueError`, `HTTPException`, `PermissionError`, and generic `Exception`).
2. The inner `finally` checks `temp_file_path.exists()` before unlink, so it handles both the case where the file was moved by `process_upload` (file no longer exists at temp path) and the case where validation failed (file still at temp path).
3. The cleanup works correctly regardless of whether the outer `except` handlers re-raise — Python's `finally` always executes before the exception propagates.

**Rejected**: The finding was already self-withdrawn by the auditor. Code review confirms no temp file leak.

---

## Reclassified Findings

### DP-009: Reclassified `SPEC-DEVIATION` → `DOC-UPDATE`

| Field | Original | Updated |
|-------|----------|---------|
| **ID** | DP-009 | DP-009 |
| **Severity** | MEDIUM | MEDIUM |
| **Type** | SPEC-DEVIATION | DOC-UPDATE |
| **Classification** | mandatory | advisory |
| **Status** | ACCEPTED (reclassified) | — |

**Rationale:** After code review, the APPEND mode behavior is **by design**, not a spec deviation:

1. The SPEC.md (line 100 of `processing-api.md`) states: "Each upload triggers a **full recalculation** of aggregates for the dashboard. There is no incremental aggregation." This describes the OVERWRITE mode.
2. The `_bulk_upsert` at `manager.py:311-350` uses `ON CONFLICT (dashboard_id, graph_id, dims) DO UPDATE SET metrics = excluded.metrics` — this correctly implements "add or update" semantics for APPEND.
3. The code does exactly what a reasonable APPEND semantic implies: new-file aggregates are upserted, existing records for non-matching dims are preserved. This is standard CDC-style upsert behavior.
4. The issue identified by the auditor — that APPEND doesn't recalculate aggregates from the combined (old+new) dataset — is correct but **this is not a spec violation**. The SPEC.md doesn't promise additive/recalculating semantics for APPEND; it only says APPEND "adds to existing aggregated data" (`processing-api.md` line 111).
5. The **real** problem is that this behavior is insufficiently documented. Users can't know that APPEND calculates aggregates from only the new file without recalculation from combined data. This is a **documentation gap**, not a code defect.

**Recommendation adjusted:** Change type to `DOC-UPDATE`, reduce classification from `mandatory` to `advisory`. Update `processing-api.md` to clearly state: "APPEND mode calculates aggregates from the uploaded file only and upserts them. Existing aggregates for non-overlapping dimension combinations are preserved. Aggregates are NOT recalculated from the combined (old + new) dataset."

---

## Merged Findings

### DP-004 + DP-006: Merged for Implementation (Shared Root Cause: Worker Error Handling Integrity)

**Original IDs:** DP-004, DP-006
**Merged ID:** DP-004 (primary), DP-006 (subsumed)
**Rationale:** DP-006 (no explicit `FileNotFoundError` handling) is a subset of DP-004 (silent exception swallowing in `_update_processing_log_status`). The root problem is that the worker's error path is unreliable — status updates fail silently AND the worker doesn't distinguish between recoverable and unrecoverable errors. Fixing DP-004 (making status update failures visible) would automatically address the DP-006 symptom (unrecoverable state after file-not-found). The explicit `FileNotFoundError` handling recommended by DP-006 is still a good practice but becomes a minor improvement once DP-004's error-handling overhaul is done.

**Merge resolution:** Keep DP-006 as advisory but note that DP-004 implementation should also address the file-not-found scenario. The combined fix should:
1. Make `_update_processing_log_status` return a boolean (DP-004).
2. Handle `FileNotFoundError` explicitly before the generic `except` (DP-006).
3. Abort processing when the PROCESSING status update fails (DP-004 caller fix).

---

## Cross-Phase Conflicts

### 1. DP-003 (MIME Validation) vs Phase 04 (SEC findings on Upload Validation)

**Nature:** Phase 04 (Security) findings SEC-005/SEC-008 don't directly address MIME validation, so no conflict exists. However, DP-003 (MIME type trusts `Content-Type` header) is **complementary** to any file validation findings in Phase 04. If Phase 04 findings recommend adding server-side MIME detection, they would overlap with DP-003's recommendation. No actual Phase 04 finding recommends this, so no conflict.

**Resolution:** No action needed. DP-003 stands alone as a security concern specific to the data processing phase.

### 2. DP-005 (In-Memory Task Queue) vs Phase 06 (TST-001: Test Infrastructure)

**Nature:** These findings are independent. DP-005 describes an architectural limitation (task loss on restart), while TST-001 describes an infrastructure problem (DB port not exposed to host). No conflict.

### 3. DP-008 (YoY Infinity) — Same Infliction in `_calculate_share`

**Nature:** The same `inf` generation pattern exists in `_calculate_share` at `aggregate_transforms.py:240-241` — when `total` evaluates to a near-zero float, division produces `inf`. However, the `_calculate_share` function handles `total == 0` explicitly (line 247-248 and line 239-240), and Polars returns `NaN` (not `inf`) for `0/0` in float division (IEEE 754). For very small non-zero totals, the division produces a very large float but not `inf`. So `_calculate_share` is less vulnerable than `_calculate_yoy`, but the same defensive pattern (`.is_infinite()` check) would be prudent.

**Resolution:** No separate finding needed, but the DP-008 fix should also review `_calculate_share` as part of the same defensive-coding pass.

---

## Rollout Safety Assessment

### DP-001 (Cumulative Size Check) — Rollout Risk: LOW

- **Risk:** Minimal. Adding a cumulative counter inside the existing streaming loop is a self-contained change. The check is additive — it doesn't modify existing logic, only adds a new guard.
- **Dependency:** None. Self-contained to `upload.py:155-158`.
- **Implementation note:** Must also check `total_bytes > config.max_file_size` **during** the loop (not just after), to abort early and avoid writing more data than necessary. Should clean up the partial temp file on abort.

### DP-003 (Magic Byte Validation) — Rollout Risk: LOW

- **Risk:** Adding magic byte checks to `validate_file()` in `file_processing.py` is a self-contained change to the validation function.
- **Dependency:** Must handle both regular files and gzip files (read first 2 bytes from raw file or from decompressed stream). The gzip magic bytes are `\x1f\x8b`. CSV files have no magic bytes — the check would be "file is valid UTF-8 and parseable as CSV."
- **Caution:** Don't reject files solely for lacking CSV magic bytes (since CSVs have no standard magic number). The check is most valuable for gzip files (`\x1f\x8b`).

### DP-004 (Status Update Error Handling) — Rollout Risk: MEDIUM

- **Risk:** Changing `_update_processing_log_status` to return a boolean (or re-raise) affects **all** callers: `data_worker.py:174`, `data_worker.py:229`, `data_worker.py:253`, and `cleanup_stale_processing_logs`. Each caller must be updated to handle the new behavior.
- **Dependency:** The `_process_csv_file_async` function's error handler at line 248-275 must be restructured to handle status-update failure. If the FAILED status update itself fails, the function should still return a failure dict (not crash), but should log at CRITICAL level.
- **Note for merged DP-006:** When adding explicit `FileNotFoundError` handling, keep it as a specific `except ValueError | FileNotFoundError` before the generic `except Exception` — or better, group all expected exceptions together.

### DP-005 (Task Queue Persistence) — Rollout Risk: DOCUMENTATION ONLY (advisory)

- **Risk:** No code change recommended by the finding (document as MVP limitation). The code already has the migration path documented in `docs/03-processing/task-queue.md`.
- **Recommendation:** Instead of code changes, add a note to the startup log and the API docs warning about task loss on restart.

### DP-007 (Aggregate M×N Explosion) — Rollout Risk: LOW

- **Risk:** Changing the aggregation logic in `_store_aggregates` would require a full re-upload to regenerate data for existing dashboards. No schema change.
- **Dependency:** The current code creates M×N aggregates (all rows × all graphs). Any filtering change would need to be clearly documented as a behavioral change.
- **Implementation note:** The simplest fix is to also group by dimension values so that each unique `(graph_id, dims)` combination gets exactly one row — equivalent to what the frontend expects.

### DP-008 (YoY Infinity) — Rollout Risk: LOW

- **Risk:** Adding `is_infinite()` handling to `_calculate_yoy` is a one-line expression change in `aggregate_transforms.py:202-209`.
- **Dependency:** None. Self-contained within `_calculate_yoy`.
- **Implementation note:** Replace `fill_nan(None)` with a chained expression: `.fill_nan(None).replace([float('inf'), float('-inf')], None)` or add a separate `.when(pl.col(alias).is_infinite()).then(None)` clause.

---

## Mandatory Fixes (Accepted)

| ID | Severity | Type | Issue | Rollout Risk |
|----|----------|------|-------|--------------|
| DP-001 | HIGH | RUNTIME-ERROR | No cumulative size check during file streaming when `file.size` is `None` — unbounded disk write possible | LOW |
| DP-003 | HIGH | RUNTIME-ERROR | MIME type validation trusts client-provided `Content-Type` header without magic byte verification | LOW |
| DP-004 | HIGH | RUNTIME-ERROR | `_update_processing_log_status` silently swallows all exceptions, causing undetected status update failures and corrupting task state machine | MEDIUM |
| DP-008 | HIGH | RUNTIME-ERROR | `_calculate_yoy` can produce `inf`/`-inf` values that bypass `fill_nan(None)` and cause JSON serialization failures when stored in JSONB | LOW |

## Advisory Recommendations (Accepted)

| ID | Severity | Type | Issue | Rollout Risk |
|----|----------|------|-------|--------------|
| DP-005 | MEDIUM | BEST-PRACTICE | In-memory task queue loses all pending tasks on process restart; documented limitation needs explicit warning | NONE (docs only) |
| DP-006 | MEDIUM | RUNTIME-ERROR | No explicit `FileNotFoundError` handling in CSV worker (merged with DP-004 fix — handle as part of DP-004 rewrite) | LOW |
| DP-007 | MEDIUM | BEST-PRACTICE | M×N aggregate storage (all rows × all graphs) inflates storage and may confuse frontend | LOW |
| DP-009 | MEDIUM | DOC-UPDATE | APPEND mode semantics (no aggregate recalculation from combined data) are undocumented | NONE (docs only) |

---

## Summary

- **9 findings**: 6 accepted (unchanged or with noted context), 1 rejected (DP-002), 1 reclassified (DP-009: SPEC-DEVIATION → DOC-UPDATE), 1 merged (DP-006 into DP-004).
- **4 mandatory fixes** (DP-001, DP-003, DP-004, DP-008).
- **4 advisory recommendations** (DP-005, DP-006, DP-007, DP-009).
- **No cross-phase conflicts** with Phases 01-06. Findings are independent.
- **Highest rollout risk:** DP-004 (affects all worker status update paths).
- **DP-009 downgraded** from mandatory SPEC-DEVIATION to advisory DOC-UPDATE — the code behavior is correct for the documented semantics; only the documentation is incomplete.
- **DP-002 self-withdrawn** by original auditor — cleanup logic is correct.
