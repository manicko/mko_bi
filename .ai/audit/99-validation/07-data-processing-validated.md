---
name: 07-data-processing-validated
description: Validation report for Phase 07 Data Processing findings
validator: validator
date: 2026-06-10
mode: problems-only
---

# Phase 07 Data Processing Validation Report

## Rejected Findings

### DP-001: Processing Status Enum Has Duplicate/Split Terminal States
**Status:** REJECTED

**Reason:** The finding claims that `ProcessingStatus` enum defines both `SUCCESS` and `COMPLETED` as terminal states, but `ProcessingStatus` enum in `src/mkobi/models/enums.py` (lines 58-65) only contains: `STARTED`, `UPLOADED`, `PROCESSING`, `COMPLETED`, `FAILED`.

The `SUCCESS` enum value exists in `ButtonVariant` (line 125), NOT in `ProcessingStatus`. The code correctly uses `COMPLETED` as the canonical terminal success state throughout (`data_worker.py` line 339, `processing_log_service.py` line 186).

The `update_to_success` method (lines 193-198) is correctly marked as deprecated and internally delegates to `update_to_completed` - this is a proper deprecation pattern, not a bug.

**Evidence:**
- `src/mkobi/models/enums.py:58-65` — ProcessingStatus enum has no SUCCESS member
- `src/mkobi/models/enums.py:120-125` — SUCCESS exists in ButtonVariant enum only
- `src/mkobi/workers/data_worker.py:339` — Uses ProcessingStatus.COMPLETED
- `src/mkobi/services/processing_log_service.py:193-198` — Deprecated method delegates to correct implementation

---

## Validated Findings (Mandatory)

### DP-002: Filter Values Not Fully Cleared on Overwrite Mode When Dashboard Filters Change
**Status:** VALIDATED as SPEC-DEVIATION (mandatory)

**Verification:** CONFIRMED. The `_store_aggregates` function in `data_worker.py` (lines 508-523) iterates over currently configured dashboard filters (`filter_names = [f.name for f in filter_reads]`) and saves values for each. When a dashboard filter is removed between uploads, its orphaned values remain in the `dashboard_filter_values` table because `clear_dashboard_values` method (which clears ALL values for a dashboard) exists in the repository but is never called during `mode=OVERWRITE`.

This violates the documented behavior: "Each upload triggers a full recalculation — both `aggregated_data` and `dashboard_filter_values` are rebuilt from scratch" (docs/03-processing/processing-api.md line 103).

---

## Validated Findings (Advisory)

### DP-003: Non-Deterministic Aggregation Due to Floating-Point Math in YoY Calculation
**Status:** VALIDATED as BEST-PRACTICE (advisory)

**Verification:** CONFIRMED. The `_calculate_yoy` function in `aggregate_transforms.py` (line 205) performs `(pl.col(value_column) - prev_value_expr) / prev_value_expr * 100` without any precision rounding. While the sorting is deterministic (line 181), floating-point arithmetic can produce values like `49.999999999999` instead of `50.0`.

### DP-004: Configuration Fields "metric_agg" and "aggregation_function" Not Exposed in Processing Config
**Status:** VALIDATED as BEST-PRACTICE (advisory)

**Verification:** CONFIRMED. The `AggregationService.aggregate_for_dashboard` method accepts `metric_agg: str = "sum"` parameter (line 34) but this is not configurable via `ProcessingSettingsDict` in `src/mkobi/models/types.py` or the `ProcessingConfig` model in `src/mkobi/models/data.py`. Users cannot configure this via API, resulting in hardcoded "sum" as the only default aggregation type.

### DP-005: Missing Validation for Processing Config Fields
**Status:** VALIDATED as BEST-PRACTICE (advisory)

**Verification:** CONFIRMED. The processing config settings in `data_worker.py` (lines 207-214) are extracted via raw `.get()` calls without upfront validation. Invalid `column_types` mappings produce warnings in `filter_transforms.py` (line 143) but no validation error.

### DP-006: Documentation Incorrectly States Numeric Literals Not Supported in Formula Parser
**Status:** VALIDATED as DOC-UPDATE (advisory)

**Verification:** CONFIRMED. The documentation in `docs/03-processing/processing-api.md` (line 232) states "numeric literals as operands (e.g., `100 * revenue`) is invalid" but the implementation in `formula_parser.py`:
- `_is_numeric_literal()` function (lines 36-49) correctly identifies numeric literals
- `_parse_formula()` converts numeric literals to `pl.lit()` (lines 119-120, 135-136)
- Tests verify `revenue / 100` (line 133-136) and `revenue * 100` (line 153-158) work correctly

---

## Cross-Phase Conflicts

None detected. No conflicting findings from other audit phases.

---

## Rollout Safety Issues

### DP-002 Sequencing Risk
The fix requires modifying `_store_aggregates` to call `clear_dashboard_values` at the start when in overwrite mode. This change:
- Must be atomic within the existing transaction boundary
- Should be paired with the existing `save_aggregates` clear_old logic
- Risk is MEDIUM for production due to potential for orphaned data during transition

---

## Summary

| Status | Count |
|--------|-------|
| Rejected | 1 |
| Validated (Mandatory) | 1 |
| Validated (Advisory) | 4 |

**Validated Mandatory Fixes:**
1. DP-002: Clear all dashboard filter values when `mode=OVERWRITE` is used

**Validated Advisory Fixes:**
1. DP-003: Add precision rounding to YoY percentage calculations
2. DP-004: Add `metric_agg` field to ProcessingSettingsDict for configurability
3. DP-005: Add upfront validation for processing config fields
4. DP-006: Update documentation to reflect numeric literal support in formula parser