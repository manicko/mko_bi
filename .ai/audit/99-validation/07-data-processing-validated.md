# Phase 07 Validation — Data Processing Pipeline

**Validator:** validator agent  
**Input:** `.ai/audit/07-data-processing/findings.md`  
**Output:** `.ai/audit/99-validation/07-data-processing-validated.md`  
**Mode:** problems-only  
**Date:** 2026-06-05  

---

## 1. Merged Findings

### MERGE-01: DP-001 + DP-002 (same root cause — test mode transaction boundary)

| Field | Value |
|-------|-------|
| **Merged IDs** | DP-001, DP-002 |
| **Merged As** | DP-001 |
| **Rationale** | Both findings address the identical root cause: `_store_aggregates` in test mode (lines 394-455 of `data_worker.py`) has no `async with session.begin()` transaction wrapper. DP-001 frames it as "missing transaction wrapper for storage operations," DP-002 frames it as "incomplete transaction boundary causing partial commit risk." These are the same issue described from slightly different angles. The evidence cited by both (lines 394-455) is identical. |

**Resolution:** DP-002 is merged into DP-001. DP-001 is reclassified (see Section 2).

---

## 2. Reclassified Findings

### RECLASS-01: DP-001 — SPEC-DEVIATION → BEST-PRACTICE

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Original Type** | SPEC-DEVIATION |
| **New Type** | BEST-PRACTICE |
| **Rationale** | The test mode in `_store_aggregates` (line 395-396) explicitly documents: *"Test mode - use provided session without creating nested transaction. Caller manages the transaction."* This is a deliberate design choice, not a specification deviation. The `_process_csv_file_async` function's test mode similarly expects the caller to manage transactions. The finding is valid as a **recommendation** (it would be cleaner to have consistent transaction handling), but it is not a spec deviation since there is no documented spec requiring test-mode transactions. The risk is limited to test environments where partial commits are acceptable for debugging. Production mode (lines 458-459) correctly uses `async with session.begin()`. |

### RECLASS-02: DP-005 — SPEC-DEVIATION → BEST-PRACTICE

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Original Type** | SPEC-DEVIATION |
| **New Type** | BEST-PRACTICE |
| **Rationale** | Same root cause as DP-001. The `cleanup_stale_processing_logs` test mode (line 114) follows the identical pattern: "Test mode - use provided session (already in transaction)." This is a consistent design choice across the module, not a spec deviation. No documented spec requires explicit transaction management in test mode. |

---

## 3. Rejected Findings

### REJECT-01: DP-003 — Race condition in task state transition

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Original Type** | SPEC-DEVIATION |
| **Rejection Reason** | **Overstated / speculative.** The finding describes a theoretical race between `_update_processing_log_status` and `cleanup_stale_processing_logs`, but: (1) Both functions operate on the same `ProcessingLog` row identified by `task_id`; the SELECT + UPDATE pattern with proper WHERE clause is a standard optimistic approach. (2) The `cleanup_stale_processing_logs` only targets rows with `status == PROCESSING` and `started_at < cutoff` — it cannot interfere with a row that has already transitioned to FAILED or COMPLETED. (3) The finding's claim about "session state could be left in an inconsistent state" is not substantiated — SQLAlchemy's session rollback on exception (line 89) handles this correctly. (4) The recommendation to "use a single `async with db.begin()` block for the entire `_process_csv_file_async`" would actually break the production mode which intentionally uses separate sessions for status updates (to avoid long-held transactions). |

### REJECT-02: DP-004 — Empty DataFrame handling

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Original Type** | RUNTIME-ERROR |
| **Rejection Reason** | **Partially mitigated + behavior is technically correct.** (1) The `validate_file` function in `file_processing.py` (line 121) already rejects zero-byte files. (2) A CSV with headers but no data rows would produce a DataFrame with 0 rows and N columns. The pipeline would proceed, aggregation would produce 0 records, and `save_aggregates` would return 0 processed records. This is **correct behavior** — no data means no aggregates. (3) The finding's core claim that `DataValidator.validate()` is "never called in the pipeline" is accurate but irrelevant — `CSVLoader.load_csv()` performs its own validation (file size, required columns). (4) The scenario described ("empty CSV file with headers would pass through and result in a completed status with zero data points") is not misleading — it accurately reflects that zero rows were processed. No data loss occurs. |

---

## 4. Validated Findings (Summary)

The following findings passed validation. Only problems are reported in detail above.

| ID | Title | Type | Severity | Classification | Status |
|----|-------|------|----------|---------------|--------|
| DP-001 | Missing transaction wrapper in test mode (merged with DP-002) | BEST-PRACTICE (reclassified) | CRITICAL → **MEDIUM** | advisory | Merged + Reclassified |
| DP-006 | Graceful handling of missing columns in graphs | BEST-PRACTICE | MEDIUM | advisory | Validated as-is |
| DP-007 | Potential unbounded memory usage with lazy CSV loading | BEST-PRACTICE | MEDIUM | advisory | Validated as-is |
| DP-008 | Unsafe eval() in computed field expressions | RUNTIME-ERROR | HIGH | **mandatory** | Validated, severity confirmed |

---

## 5. Validated Finding Details (Advisory)

### DP-006: Graceful handling of missing columns in graphs

**Status:** Validated as advisory BEST-PRACTICE.

The finding is correct: `aggregation_service.py` lines 61-65 silently skip graphs with no matching columns. The recommendation to add skipped-graph information to the processing log is reasonable but low priority. Currently a warning is logged; enhancing user-visible feedback would be a quality-of-life improvement.

### DP-007: Potential unbounded memory usage with lazy CSV loading

**Status:** Validated as advisory BEST-PRACTICE.

The finding is technically correct: `pl.scan_csv().collect()` (loader.py line 210) materializes the entire dataset. However, Polars' lazy API still provides query optimization benefits (predicate pushdown, projection pushdown) during the scan phase. The 10MB threshold is configurable via `app.yaml`. True streaming would require architectural changes to the aggregation pipeline. This is a valid optimization observation but not urgent for the current project scale.

---

## 6. Validated Finding Details (Mandatory)

### DP-008: Unsafe eval() in computed field expressions

**Status:** Validated as HIGH severity mandatory fix.

**Evidence confirmed:**
- `filter_transforms.py:96-100`: `eval(expr_str.strip(), {"__builtins__": {}}, polars_ns)` where `polars_ns = {"pl": pl, "polars": pl, "col": pl.col}`
- The `eval()` path is triggered when `expr_str.strip().startswith("pl.")`
- Processing configs with `computed_fields` can be modified by any user with `editor` role via `PUT /api/v1/processing-configs/{dashboard_id}` (processing_configs.py line 63: `require_editor_role`)
- The `{"__builtins__": {}}` restriction is insufficient when the full `pl` module is provided in the namespace — Polars internals can be exploited for arbitrary code execution

**Attack vector:** An editor-role user can craft a `computed_fields` expression starting with `pl.` that executes arbitrary Python code via Polars' `map_elements` or similar methods.

**Recommendation confirmed:** Replace `eval()` with the existing safe `_parse_formula()` parser (already implemented in `formula_parser.py`) for all non-`pl.` expressions, and either: (a) remove the `eval()` path entirely, or (b) implement a strict allowlist of permitted Polars expressions.

**Note:** The existing `_parse_formula()` function (formula_parser.py) already provides a safe alternative that supports column names, numeric literals, and basic arithmetic operators (+, -, *, /). This should be the default path for all computed field expressions.

---

## 7. Cross-Phase Conflicts

No cross-phase conflicts detected. The data processing findings are self-contained within the data processing pipeline module and do not contradict findings from other audit phases.

---

## 8. Rollout Safety Analysis

### Dependency Graph

```
DP-008 (eval removal) — independent, can be done first
DP-001/DP-002 (transaction consistency) — independent, test-mode only
DP-006 (skipped graph feedback) — independent, additive change
DP-007 (streaming optimization) — independent, architectural
```

### Rollout Ordering

1. **DP-008** (mandatory, HIGH) — Should be fixed first. Isolated change in `filter_transforms.py`. Low risk, high security impact.
2. **DP-001** (advisory, MEDIUM) — Can be addressed in a follow-up. Requires careful testing of test-mode transaction boundaries. Risk: low (test mode only).
3. **DP-006** (advisory, MEDIUM) — Purely additive. Can be done anytime.
4. **DP-007** (advisory, MEDIUM) — Architectural change. Should be deferred until memory issues are observed in production.

### Semantic Target Stability

| Finding | Anchor | Stability |
|---------|--------|-----------|
| DP-008 | `_add_computed_fields` function in `filter_transforms.py:75-110` | **Stable** — function signature and eval usage are unlikely to change |
| DP-001 | `_store_aggregates` test mode branch in `data_worker.py:394-455` | **Stable** — well-defined code block with clear boundaries |
| DP-006 | `aggregate_for_dashboard` in `aggregation_service.py:50-65` | **Stable** — core aggregation logic, unlikely to be refactored soon |
| DP-007 | `_read_csv_lazy` in `loader.py:186-213` | **Moderate** — loading strategy may evolve with Polars updates |

---

## 9. Validated Counts Summary

| Category | Count |
|----------|-------|
| **Total findings in phase** | 8 |
| **Merged** | 1 (DP-002 → DP-001) |
| **Reclassified** | 2 (DP-001: SPEC-DEVIATION → BEST-PRACTICE; DP-005: SPEC-DEVIATION → BEST-PRACTICE) |
| **Rejected** | 2 (DP-003, DP-004) |
| **Validated (mandatory)** | 1 (DP-008) |
| **Validated (advisory)** | 3 (DP-001 merged, DP-006, DP-007) |
| **Net actionable findings** | 4 |
