# Phase 07 Audit Validation Report — Data Processing Pipeline

**Validator:** audit-validate
**Source Findings:** `.ai/audit/07-data-processing/findings.md`
**Date:** 2026-06-11

---

## Rejected Findings

### DP-003 REJECTED: Transaction boundary separation incomplete in error paths

**Finding:** The `_store_aggregates` function in `data_worker.py` performs multiple database operations within a transaction, but filter values repository operations are not protected by the same transaction boundaries as the main aggregate storage.

**Evidence Against Finding:**
- `src/mkobi/workers/data_worker.py:559-560` (test mode) - Uses provided `db_session` without nested transaction
- `src/mkobi/workers/data_worker.py:629-693` (production mode) - Wraps ALL operations in `async with session.begin():` block including filter value storage
- `src/mkobi/data/storage/manager.py:9` comment explicitly states "Does not manage transactions (commit/rollback is external)"
- All operations (aggregate storage AND filter value storage) share the same transaction context via the caller-provided `db_session` parameter
- Any exception in the transaction block triggers automatic rollback via `session.begin()` context manager

**Reason:** The finding is factually incorrect. Both test and production code paths use the same transaction context for ALL operations. The `_store_aggregates` function correctly relies on the caller's transaction, and no separate transaction boundaries exist for filter values. The code comment in `manager.py` confirms this design intent.

---

## Confirmed Findings

### DP-001 CONFIRMED: Processing config validation mismatch with actual processing settings

**Original Type:** SPEC-DEVIATION
**Validated Type:** SPEC-DEVIATION (confirmed)

**Finding:** The `_validate_settings` method validates required fields `loader`, `date_column`, `timezone`, but these fields are never used in the actual data processing pipeline.

**Analysis:**
- `src/mkobi/services/processing_config_service.py:86-99` validates `loader`, `date_column`, `timezone` as required fields
- `src/mkobi/db/seeders/test_media_dash.py:207-229` includes `date_column` but is missing `loader` and `timezone` fields
- `src/mkobi/models/types.py:162-181` defines `loader: str` (not optional) and `timezone: str` (not optional) in ProcessingSettingsDict
- **Actual usage in data_worker.py:300-311:** Uses `separator`, `encoding`, `column_types` from settings
- **Actual usage in data_worker.py:341-376:** Uses `decimal_separator`, `date_format`, `renames`, `computed_fields`
- `loader` and `timezone` are never read/used in `data_worker.py` or elsewhere in the processing pipeline
- `date_column` is validated but also never used - `date_format` is used instead for date parsing

**Root Cause:** The validation requirements in `_validate_settings` require fields that are documented but unused in actual processing. The SPEC documents `loader`, `date_column`, `timezone` as processing config fields, but the implementation never consumes them.

**Recommendation:** Update `_validate_settings` in `processing_config_service.py` to remove `loader`, `date_column`, `timezone` from required fields since they are documented but never used in the actual processing pipeline.

### DP-002 RECLASSIFIED: Non-deterministic aggregation due to missing metric_agg wiring

**Original Type:** BEST-PRACTICE (mandatory)
**New Type:** SPEC-DEVIATION (reclassified)

**Finding:** The `AggregationService.aggregate_for_dashboard` method supports `metric_agg` parameter but the processing config `metric_agg` value is never extracted and passed to the function.

**Evidence:**
- `src/mkobi/services/aggregation_service.py:34` - `metric_agg: str = "sum"` parameter supports configurable aggregation
- `src/mkobi/services/aggregation_service.py:68-76` - Implementation correctly uses `metric_agg` when provided
- `docs/03-processing/processing-api.md:112` - Documentation states "Metric aggregation default: `sum` (configurable via `metric_agg` parameter)"
- **Critical issue:** `src/mkobi/workers/data_worker.py:582` and `650` - `aggregate_for_dashboard` called WITHOUT extracting `metric_agg` from `processing_config_dict` settings

**Root Cause:** The SPEC documents `metric_agg` as configurable, and the `AggregationService` implementation supports it. However, in `_store_aggregates`, the call to `aggregate_for_dashboard` hardcodes the default "sum" by not extracting `metric_agg` from settings. This is a missing wire-up, not a design limitation.

**Reason:** This should be classified as SPEC-DEVIATION - the documented capability exists ("configurable via `metric_agg` parameter") but the implementation fails to wire the config value. Users cannot actually configure aggregation via `metric_agg` despite documentation claiming it's supported.

---

## Validated Findings (No Changes)

The following findings pass validation without change:
- DP-004: Missing validation for processing config field types (MEDIUM, advisory) - correctly identifies lack of type validation
- DP-005: Orphaned temp file risk on processing log failure (MEDIUM, advisory) - correctly identifies edge case cleanup gap

---

## Cross-Phase Consistency Check

No conflicts detected with other audit phases. The data processing architecture follows the documented patterns in SPEC.md (Phase 07: Data Processing).

---

## Summary

| Finding ID | Original Type | Validated Status | Reason |
|------------|---------------|------------------|--------|
| DP-001 | SPEC-DEVIATION | KEEP AS SPEC-DEVIATION | Validation requires fields that are documented but unused in processing pipeline |
| DP-002 | BEST-PRACTICE | SPEC-DEVIATION | Documented capability exists but `metric_agg` is never wired from config to aggregation function |
| DP-003 | SPEC-DEVIATION | REJECTED | Transaction boundaries are correctly shared; finding is factually incorrect |
| DP-004 | BEST-PRACTICE | APPROVED | Correct identification of missing type validation |
| DP-005 | BEST-PRACTICE | APPROVED | Correct identification of cleanup edge case |

---

## Required Actions

### Mandatory (from SPEC-DEVIATION findings):

**DP-001 (SPEC-DEVIATION - Confirmed):** Update `_validate_settings` in `processing_config_service.py` to remove `loader`, `date_column`, `timezone` from required fields since they are documented but never used in the actual processing pipeline.

**DP-002 (SPEC-DEVIATION - Confirmed):** In `_store_aggregates` function in `data_worker.py`, extract `metric_agg` from `processing_config_dict["settings"]` and pass it to `aggregate_for_dashboard` call. Currently lines 582 and 650 call the method without this parameter, making the documented "configurable" feature non-functional.

### Advisory (non-blocking improvements):

- DP-004: Consider adding type validation for `separator`, `decimal_separator`, `column_types`, `date_format` for earlier error detection
- DP-005: Consider moving file to final location after commit, or adding cleanup for commit failure path