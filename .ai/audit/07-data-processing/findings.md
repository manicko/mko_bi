---
name: audit-findings
description: Data Processing Audit Findings
agent: auditor
alwaysApply: false
---

# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** auditor  
**Template:** .ai/audit/templates/audit-findings.md  
**Status:** complete  
**Validated:** no

---

## Findings

### DP-001: Processing Status Enum Has Duplicate/Split Terminal States

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/models/enums.py, src/mkobi/workers/data_worker.py, docs/03-processing/processing-api.md |
| **Classification** | advisory |

**Description:** The `ProcessingStatus` enum defines both `SUCCESS` (line 124) and `COMPLETED` (line 64) as terminal states, but the actual processing pipeline only uses `COMPLETED`. The state transition helper `valid_transitions()` only references `COMPLETED` and `FAILED` as terminal states (lines 77-78), and all code paths transition to `COMPLETED` on success. However, the API documentation references `SUCCESS` as a valid status in query parameter descriptions (processing_logs.py line 45), and processing_log_service.py has deprecated `update_to_success` method. This creates confusion and potential for incorrect status queries.

**Evidence:** 
- `src/mkobi/models/enums.py:64` - COMPLETED defined
- `src/mkobi/models/enums.py:124` - SUCCESS defined separately  
- `src/mkobi/models/enums.py:77-78` - valid_transitions only lists COMPLETED/FAILED as terminal
- `src/mkobi/workers/data_worker.py:339` - status set to COMPLETED
- `src/mkobi/api/routes/processing_logs.py:45` - docs say "SUCCESS" in description
- `src/mkobi/services/processing_log_service.py:196-197` - deprecated update_to_success method

**Recommendation:** Either remove `SUCCESS` from the enum entirely or consolidate it with `COMPLETED`. If keeping both for backward compatibility, update documentation to clarify that `COMPLETED` is the canonical terminal state. The `update_to_success` method should be removed as it's deprecated.

---

### DP-002: Filter Values Not Fully Cleared on Overwrite Mode When Dashboard Filters Change

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/workers/data_worker.py, src/mkobi/db/repositories/dashboard_filter_values_repo.py |
| **Classification** | mandatory |

**Description:** The documentation states "Each upload triggers a full recalculation — both `aggregated_data` and `dashboard_filter_values` are rebuilt from scratch." However, the implementation only clears filter values for filters currently configured on the dashboard (via `save_filter_values`). If a dashboard filter is removed between uploads (e.g., "region" filter deleted), old filter values remain orphaned in `dashboard_filter_values` table. This causes stale filter values to persist, leading to frontend UI showing filter options that have no corresponding data in the aggregated records.

**Evidence:**
- `src/mkobi/data/storage/manager.py:113-148` - `save_aggregates` with `clear_old=True` performs delete + insert for aggregates
- `src/mkobi/workers/data_worker.py:508-523` - Filter values saved via `save_filter_values` which performs "clear-then-insert" per filter, but this happens AFTER aggregates are saved. No linkage to `mode=overwrite` for clearing all filter values upfront.
- `src/mkobi/db/repositories/dashboard_filter_values_repo.py:69-118` - `save_filter_values` clears existing values but only for specific filter names, not all filters when overwrite mode is used

**Recommendation:** When `mode=OVERWRITE`, clear all dashboard filter values before saving new ones to ensure complete data consistency. Modify `_store_aggregates` to clear dashboard filter values at the start when in overwrite mode.

---

### DP-003: Non-Deterministic Aggregation Due to Floating-Point Math in YoY Calculation

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/data/processing/aggregate_transforms.py |
| **Classification** | advisory |

**Description:** The YoY calculation (`_calculate_yoy`) uses floating-point arithmetic for percentage calculations which can produce slightly different results due to IEEE 754 floating-point precision issues. While the sorting is deterministic (line 183), the floating-point operations on lines 205 and 212-216 may yield slightly different values under certain conditions, potentially causing subtle data drift.

**Evidence:**
- `src/mkobi/data/processing/aggregate_transforms.py:205` - `(pl.col(value_column) - prev_value_expr) / prev_value_expr * 100`
- `src/mkobi/data/processing/aggregate_transforms.py:210-216` - NaN and infinity handling but no precision rounding

**Recommendation:** Consider adding a precision rounding step (e.g., `.round(4)`) to YoY percentage calculations to ensure consistent results. This is particularly important for percentage values where `49.999999999999` and `50.000000000001` should both be treated as `50.0`.

---

### DP-004: Configuration Fields "metric_agg" and "aggregation_function" Not Exposed in Processing Config

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/models/types.py, src/mkobi/services/aggregation_service.py |
| **Classification** | advisory |

**Description:** The `AggregationService.aggregate_for_dashboard` method has a `metric_agg` parameter (default: "sum") that allows configuring the aggregation function, but this is not exposed in `ProcessingSettingsDict` or the processing config model. Users cannot configure this via the API, resulting in hardcoded "sum" being the only available aggregation type for dashboard filters.

**Evidence:**
- `src/mkobi/services/aggregation_service.py:34` - `metric_agg: str = "sum"` parameter with no way to configure from processing config
- `src/mkobi/models/types.py:162-181` - `ProcessingSettingsDict` does not include `metric_agg` field

**Recommendation:** Add `metric_agg` field to `ProcessingSettingsDict` to allow users to configure the default aggregation function (sum, mean, min, max, count) per dashboard.

---

### DP-005: Missing Validation for Processing Config Fields

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/workers/data_worker.py |
| **Classification** | advisory |

**Description:** While `TransformationConfig` validates transformation rules (transformations.py line 87-91), the processing config fields are not validated before use in the worker. Invalid config could cause silent failures or unexpected behavior. For example, if `settings["column_types"]` maps a column to an invalid Polars type like "foobar", the code continues without validation error.

**Evidence:**
- `src/mkobi/workers/data_worker.py:207-208` - Settings extracted without validation
- `src/mkobi/data/processing/filter_transforms.py:129-143` - Unknown types are logged as warnings but not validated upfront
- `src/mkobi/data/processing/transformations.py:86-91` - Validates `TransformationConfig` but other config fields are raw dict access

**Recommendation:** Add validation for processing config fields including column_types (valid Polars types only), separator (valid delimiter characters), and aggregation functions (valid enum values). Return clear error messages if config is malformed rather than silently skipping invalid entries.

---

### DP-006: Documentation Incorrectly States Numeric Literals Not Supported in Formula Parser

| Field | Value |
|-------|-------|
| **ID** | DP-006 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | docs/03-processing/processing-api.md |
| **Classification** | advisory |

**Description:** The documentation states "numeric literals as operands (e.g., `100 * revenue`) is invalid" but the formula parser implementation correctly supports numeric literals. Tests verify this works (`revenue * 100` successfully produces `250.0`), and the parser code explicitly handles numeric literals via `_is_numeric_literal()` and `pl.lit()` conversion. The documentation limit on parentheses and operator precedence is accurate, but the claim about numeric literals is incorrect.

**Evidence:**
- `docs/03-processing/processing-api.md:232` - Claims numeric literals not supported
- `src/mkobi/data/processing/formula_parser.py:36-49` - `_is_numeric_literal` function handles parsing numeric literals
- `src/mkobi/data/processing/formula_parser.py:135-136` - Numeric literals converted to `pl.lit()`
- `tests/test_data_transformations.py:133` - Test verifies `revenue / 100` works correctly
- `tests/test_data_transformations.py:153-158` - Test verifies `revenue * 100` works correctly

**Recommendation:** Update the documentation to remove the claim that numeric literals are not supported. Add examples showing valid numeric literal usage: `revenue * 100`, `profit / revenue * 100`, etc.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

- DP-002: Filter values not cleaned up on overwrite mode (data inconsistency risk)

## Advisory Recommendations

- DP-001: Processing status enum has duplicate/split terminal states
- DP-003: Non-deterministic aggregation due to floating-point math in YoY calculation
- DP-004: Configuration fields "metric_agg" and "aggregation_function" not exposed in processing config
- DP-005: Missing validation for processing config fields
- DP-006: Documentation incorrectly states numeric literals not supported in formula parser

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `DP-001`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction |
| `classification` | enum | `mandatory` or `advisory` |