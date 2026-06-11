# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DP-001: Processing config validation mismatch with actual processing settings

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/processing_config_service.py, src/mkobi/services/aggregation_service.py, src/mkobi/workers/data_worker.py |
| **Classification** | mandatory |

**Description:** The `_validate_settings` method in `ProcessingConfigService` (lines 86-99) validates required fields `loader`, `date_column`, and `timezone`, but these fields are never used in the actual data processing pipeline. The data worker (`data_worker.py` lines 300-384) uses entirely different settings: `separator`, `encoding`, `column_types`, `decimal_separator`, `date_format`, `renames`, `computed_fields`. The test seeder (`test_media_dash.py`) provides a valid processing config without these "required" fields, which would fail API validation but works in the background. This creates an inconsistency where processing configs can be created that won't pass validation on subsequent saves.

**Evidence:**
- `src/mkobi/services/processing_config_service.py:86-99` - Validation requires `loader`, `date_column`, `timezone`
- `src/mkobi/workers/data_worker.py:306-379` - Processing reads `separator`, `encoding`, `column_types`, `decimal_separator`, `date_format`, `renames`, `computed_fields`
- `src/mkobi/db/seeders/test_media_dash.py:207-229` - Valid processing config in seeder without `loader`/`timezone` fields
- `src/mkobi/models/types.py:162-181` - ProcessingSettingsDict defines actual settings fields

**Recommendation:** Either: (a) Remove the validation for unused fields `loader`, `date_column`, `timezone` from `_validate_settings`; or (b) Actually use these fields in the processing pipeline. If option (b), implement usage of `loader` and `timezone` or make them optional. Since the system already works without them, option (a) is recommended - remove this validation to match actual usage.

---

### DP-002: Non-deterministic aggregation due to hardcoded function mapping

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/services/aggregation_service.py |
| **Classification** | mandatory |

**Description:** The `AggregationService.aggregate_for_dashboard` method (lines 68-76) uses a hardcoded `_agg_fn_map` dictionary that maps aggregation function names to Polars expressions. This mapping is hardcoded inside the method and cannot be configured through the processing config. While the `metric_agg` parameter exists and defaults to "sum", the processing config documentation mentions `metric_agg` as a valid field, but the validation in `processing_config_service.py` doesn't validate this field, and the actual aggregation function is hardcoded rather than derived from config.

**Evidence:**
- `src/mkobi/services/aggregation_service.py:68-76` - Hardcoded `_agg_fn_map` inside method
- `src/mkobi/models/types.py:181` - `metric_agg` defined in ProcessingSettingsDict but not validated
- `src/mkobi/services/processing_config_service.py:71-99` - `_validate_settings` does not check `metric_agg`

**Recommendation:** Either: (a) Remove the unused `_agg_fn_map` and make aggregation function fully configurable via processing config `metric_agg` field; or (b) Validate `metric_agg` in `_validate_settings` if the intention is to use it. Currently the system defaults to "sum" regardless of config, which is a divergence between documented capability and actual behavior.

---

### DP-003: Transaction boundary separation incomplete in error paths

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/aggregation_service.py, src/mkobi/db/repositories/dashboard_filter_values_repo.py |
| **Classification** | mandatory |

**Description:** The `_store_aggregates` function in `data_worker.py` performs multiple database operations (graph queries, filter queries, aggregate storage, filter value storage) within a transaction. However, the filter values repository operations (lines 606-625) are not protected by the same transaction boundaries as the main aggregate storage. If filter value storage fails after aggregates are stored, the state becomes partially inconsistent - aggregates exist but filter values are missing.

**Evidence:**
- `src/mkobi/workers/data_worker.py:283-297` - `_run_with_transaction` wraps operations but filter values are after aggregate storage
- `src/mkobi/workers/data_worker.py:606-625` - Filter values saved after aggregates in same transaction (correct), but error handling in `_store_aggregates` doesn't rollback on filter value failures
- `src/mkobi/data/storage/manager.py:10` comment states "Does not manage transactions (commit/rollback is external)"

**Recommendation:** Ensure all database operations in `_store_aggregates` share the same transaction context. The current implementation uses the caller's transaction (passed via `db_session` parameter), which is correct, but exception handling should ensure all-or-nothing behavior. Add try/except around filter value storage to rollback on failure.

---

### DP-004: Missing validation for processing config field types

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/services/processing_config_service.py |
| **Classification** | advisory |

**Description:** The `_validate_settings` method validates field presence but does not validate field types. Processing settings accept arbitrary types in `ProcessingSettingsDict` (TypedDict), but invalid types for critical fields like `separator` (should be str), `column_types` (should be dict[str, str]), `decimal_separator` (should be "," or "."), and `date_format` (should be str) could cause silent failures or confusing errors during processing.

**Evidence:**
- `src/mkobi/services/processing_config_service.py:71-99` - Only validates presence, not types or values
- `src/mkobi/models/types.py:162-181` - ProcessingSettingsDict fields lack runtime type validation

**Recommendation:** Add type validation for critical processing settings fields. For example, validate that `separator` is a single character string, `decimal_separator` is either "," or ".", `column_types` values are valid Polars type names, and `date_format` follows strftime patterns. This would provide clearer error messages before processing begins.

---

### DP-005: Orphaned temp file risk on processing log failure

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/services/file_processing.py |
| **Classification** | advisory |

**Description:** In `process_upload_with_session` (lines 232-268), when the file is moved to final location via `file_path.replace(final_file_path)` and then `enqueue_processing_job` fails, the moved file is cleaned up (line 263). However, if the `db.commit()` at line 268 fails after successful enqueue, the file remains orphaned. While unlikely, this violates the principle of cleaning up temp files on all error paths.

**Evidence:**
- `src/mkobi/services/file_processing.py:232-268` - File moved before commit, cleanup only on enqueue failure
- `src/mkobi/services/file_processing.py:263-265` - Cleanup only if enqueue fails, not if commit fails after

**Recommendation:** Consider moving the file after commit instead of before, or add cleanup in the upload endpoint if db operations fail after the file has been moved. The current flow: (1) validate, (2) create log, (3) move file, (4) enqueue, (5) commit. If commit fails after enqueue, the file and job are orphaned.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 0 |

## Mandatory Fixes

- DP-001: Processing config validation mismatch with actual processing settings
- DP-002: Non-deterministic aggregation due to hardcoded function mapping

## Advisory Recommendations

- DP-003: Transaction boundary separation incomplete in error paths (re-evaluate transaction safety)
- DP-004: Missing validation for processing config field types
- DP-005: Orphaned temp file risk on processing log failure

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `BE-001`, `FE-003`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |