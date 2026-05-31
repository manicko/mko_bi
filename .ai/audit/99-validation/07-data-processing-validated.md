# Phase 07 Validation Report — Data Processing Pipeline

**Validator:** validator agent
**Input:** `.ai/audit/07-data-processing/findings.md`
**Mode:** problems-only

---

## Rejected Findings

### DP-002: Processing Configuration Ignoted in Pipeline — PARTIALLY REJECTED

**Original type:** SPEC-DEVIATION
**Rejection type:** Overstated — the finding misidentifies the root cause.

**Analysis:**

The finding claims that `processing_config` from the `processing_configs` table is "never retrieved or applied" and that `process_csv_background` always receives `processing_config_dict=None`. This is **partially incorrect**:

1. **`trigger_processing` does accept `processing_config` parameter** (`data_service.py:246`). The route `POST /upload/{dashboard_id}/process` also accepts `config: ProcessingConfig | None` (`upload.py:226`). However, `trigger_processing` at line 270-273 **does not forward** the `processing_config` to `enqueue_processing_job` — this part of the finding is correct.

2. **The primary data flow does not go through `trigger_processing` at all.** The normal upload flow is:
   - `process_upload_with_session` → `enqueue_processing_job` → `enqueue_job` → `process_csv_background`
   - At no point in this chain is `processing_config` fetched from the database. The `enqueue_processing_job` function (`file_processing.py:269-292`) does not accept a `processing_config` parameter. This part of the finding is correct.

3. **However**, there exists a separate `DataPipeline` class (`registry.py`) that correctly fetches `ProcessingConfig` via `config_service.get_processing_config_by_dashboard()` at line 116. This pipeline is not used by the current upload→process flow, which bypasses it entirely.

4. **Line reference errors:** The finding references `data_service.py:240-273` for `trigger_processing` and `file_processing.py:188-197` for `enqueue_processing_job`. The line numbers are slightly off (the function starts at 240, but the enqueue call is at 270-273; `enqueue_processing_job` is at 269-292, not 188-197). The reference to `data_worker.py:148-226` for `processing_config_dict` receiving `None` is roughly correct.

**Rejection verdict:** The finding correctly identifies that `processing_config` is not passed through the main upload→process pipeline, but incorrectly states it is "never" retrieved. The existence of `DataPipeline` (which does fetch config) and the `trigger_processing` parameter (which accepts config but doesn't forward it) make this a **partial hit**. The core problem is valid — config is not wired through the primary path.

**Decision: KEEP** but reclassify severity. The issue is real but the framing is inaccurate. Downgrade from CRITICAL to HIGH because:
- Processing does work without config (default transformations apply)
- The `COMPLETED` status path in `DataPipeline` proves config-aware processing is implemented somewhere
- This is a missing integration, not a data corruption bug

---

## Merged Findings

### DP-001 / DP-003: Transaction Boundary Issues — MERGE CANDIDATE

**DP-001:** Transaction boundary issue in `process_upload_with_session` (file_processing.py:167-171) — file moved before `db.commit()`.

**DP-003:** Missing transaction wrapper in test mode for `_store_aggregates` (data_worker.py:297-351) — no `session.begin()` in test code path.

**Merge rationale:** Both findings address the same root cause class — **incomplete transaction boundary protection**. DP-001 is about file-system + DB inconsistency (file moved before commit). DP-003 is about DB-only inconsistency (test mode lacks transaction wrapper).

**Merge decision: DO NOT MERGE.** Rationale:
- They target different files and different operations (file move vs. DB writes)
- They require independent fixes with different risk profiles
- DP-001 has broader system-level impact (orphaned files); DP-003 is limited to test mode
- A fix for one does not resolve the other

---

## Reclassified Findings

### DP-002: Reclassified from SPEC-DEVIATION (CRITICAL) to SPEC-DEVIATION (HIGH)

**Original:** CRITICAL / SPEC-DEVIATION / mandatory
**Revised:** HIGH / SPEC-DEVIATION / mandatory

**Rationale:** The finding is technically correct that `processing_config` is not wired through the primary upload pipeline, but the CRITICAL severity is unjustified because:
- Data processing does function without explicit config (default/aggregation logic applies)
- The `DataPipeline` class in `registry.py` proves the config-aware path exists in the codebase
- Missing config causes suboptimal processing, not data loss or corruption
- The `COMPLETED` enum usage in `registry.py:106,111` shows another code path handles terminal states

---

## Cross-Phase Conflicts

### DP-006 vs. registry.py: ProcessingStatus.COMPLETED Usage — CONFLICT

**DP-006** claims `ProcessingStatus.COMPLETED` is "never used anywhere in the codebase."

**Evidence contradicts this:** `registry.py:106` and `registry.py:111` DO use `ProcessingStatus.COMPLETED`:
```python
# registry.py:104-111
await self.log_service.update_processing_log(
    log_id=log_entry.id,
    status=ProcessingStatus.COMPLETED.value,
    message="No data to process",
    ...
)
log_entry.status = ProcessingStatus.COMPLETED
```

**Resolution:** DP-006 is **partially incorrect**. The enum value IS used, but only in `data/processing/registry.py` (the `DataPipeline` class), not in the main `data_worker.py` processing path. The finding's core observation — that `COMPLETED` and `SUCCESS` are redundant/confusing — remains valid, but the claim of "never used" is false.

**Impact on DP-006:** The finding should be updated to note that `COMPLETED` is used in `DataPipeline` but not in `data_worker.py`. This is actually a **bigger** problem than an unused enum: there are **two different terminal success states** (`SUCCESS` in `data_worker.py`, `COMPLETED` in `registry.py`) with no clear semantic distinction, and they are applied by **two parallel processing pipelines** that never communicate.

**Decision:** KEEP DP-006 but upgrade significance. This is not just an unused enum — it is evidence of **two divergent processing pipelines** with inconsistent state handling.

---

## Rollout Safety Issues

### DP-001 Fix Requires Careful Sequencing

Any fix for DP-001 (reordering file move after DB commit) must handle:
1. The `finally` block in `upload.py:188-193` that cleans up `temp_file_path` — if the file has already been moved to `final_file_path`, this cleanup won't trigger (correct behavior). But if commit fails, the file is now at `final_file_path`, not `temp_file_path`, so the automatic cleanup misses it.
2. A rollback strategy is needed: either move the file back to temp on commit failure, or track the final path for cleanup.

### DP-002 Fix Requires Pipeline Consistency Decision

Fixing DP-002 (wiring `processing_config` through the upload pipeline) requires deciding which processing path is canonical:
- `data_worker.py:process_csv_background` → `_process_csv_file_async` (current primary path)
- `registry.py:DataPipeline.run` (alternative path with config integration)

Adding config fetching to the `data_worker.py` path without reconciling it with `DataPipeline` risks creating a third parallel code path. This is an architectural decision, not just a parameter-passing fix.

---

## Validated Count Summary

| Category | Count |
|----------|-------|
| Total findings | 6 |
| Validated as-is | 3 (DP-001, DP-003, DP-004) |
| Reclassified | 1 (DP-002: CRITICAL→HIGH) |
| Partially incorrect | 2 (DP-002 framing, DP-006 "never used" claim) |
| Rejected | 0 |
| Merged | 0 |
| **Mandatory (validated)** | 4 (DP-001, DP-002, DP-003, DP-004) |
| **Advisory (validated)** | 2 (DP-005, DP-006) |
