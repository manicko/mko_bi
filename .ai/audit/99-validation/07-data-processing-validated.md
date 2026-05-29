# Phase 07 Validated Findings — Data Processing Pipeline

**Validator:** validator agent
**Input:** .ai/audit/07-data-processing/findings.md
**Validated:** 2026-05-29

---

## Rejected Findings

### DP-003: Upload Endpoint Missing Processing Config Parameter

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Original Type** | SPEC-DEVIATION |
| **Rejection Reason** | Not a spec deviation — the separation is by design. The upload endpoint (`POST /upload/{dashboard_id}`) handles file upload + queuing. Processing config is accepted by the separate `POST /{dashboard_id}/process` endpoint (upload.py:226, `config: ProcessingConfig | None`). The spec states "Processing rules configurable" — they are, via the process endpoint. The two-endpoint pattern follows the data flow: upload first, then configure and trigger processing. No code change needed. |

### DP-007: Processing Log Started_At Timestamp Correctly Set

| Field | Value |
|-------|-------|
| **ID** | DP-007 |
| **Original Type** | BEST-PRACTICE |
| **Rejection Reason** | Null finding — the finding itself concludes "This is correct behavior. No change needed." (processing_log_repo.py:56 confirms `started_at` is set to `datetime.now(UTC)` during log creation). This reports no actual issue and should not have been filed as a finding. |

---

## Reclassified Findings

### DP-004: Task Queue Implementation Not Production-Ready

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Original Type** | SPEC-DEVIATION |
| **Reclassified Type** | BEST-PRACTICE |
| **Rationale** | The finding describes the TaskQueue as "not production-ready" due to in-memory status tracking. However, the spec explicitly documents this as intentional: "Background task queue — In-memory TaskQueue (MVP) with a documented migration path to Redis/RQ" (SPEC.md line 121). The in-memory queue is not a deviation from spec; it is the spec-defined MVP implementation. The actual worker (`data_worker.py`) handles persistence via `_update_processing_log_status` using the `processing_log` table, which is the correct separation. The finding is reclassified as BEST-PRACTICE: the Redis/RQ migration remains a valid future improvement, but it is not a spec deviation. Severity downgraded from HIGH to LOW. |

---

## Validated Findings (Passed — No Changes Required)

The following findings passed validation and are retained as-is. They are listed here for completeness but require no modification to type, severity, or classification.

| ID | Title | Type | Severity | Classification |
|----|-------|------|----------|----------------|
| DP-001 | Transactional Processing in Background Workers | BEST-PRACTICE | MEDIUM | advisory |
| DP-002 | Temporary File Cleanup Silently Ignores Exceptions | BEST-PRACTICE | MEDIUM | mandatory |
| DP-005 | YAML Config Processing Rules Not Integrated | SPEC-DEVIATION | LOW | advisory |
| DP-006 | Formula Parser Limitations Not Documented in API | DOC-UPDATE | MEDIUM | advisory |
| DP-008 | Stale File Cleanup Uses Modification Time Instead of Processing Log | BEST-PRACTICE | LOW | advisory |
| DP-009 | Processing Log Status Transitions Incomplete | SPEC-DEVIATION | MEDIUM | advisory |
| DP-010 | Memory Management for Large Files Uses Lazy Loading Threshold | BEST-PRACTICE | LOW | advisory |

---

## Validated Summary

| Category | Count |
|----------|-------|
| **Total findings reviewed** | 10 |
| **Validated (unchanged)** | 7 |
| **Rejected** | 2 |
| **Reclassified** | 1 |
| **Merged** | 0 |
| **Cross-phase conflicts** | 0 |

### Mandatory Fixes (Validated)

- **DP-002**: Temporary file cleanup on processing failure silently ignores exceptions without logging (`data_worker.py:265` — `except Exception: pass`). The upload.py:193 synchronous `unlink()` in async context also lacks error handling. This remains the only mandatory fix — silent failure on cleanup can leave orphaned temp files and masks debugging information.

### Advisory Recommendations (Validated)

- **DP-001**: Consider wrapping the entire processing workflow in a single transaction for atomicity across status changes and data persistence. Current design uses separate sessions for `_store_aggregates` and `_update_processing_log_status` in production mode.
- **DP-004** (reclassified): Redis/RQ migration for production readiness remains a valid future improvement per the documented migration path.
- **DP-005**: Consolidate config validation between `ProcessingConfig` and `TransformationConfig`, or document the scope split explicitly.
- **DP-006**: Add validation hints or examples to `CustomMetricConfig` docstring, or implement formula validation at the model level.
- **DP-008**: Consider correlating file cleanup with processing log status instead of relying solely on file modification time.
- **DP-009**: Remove or document the unused `COMPLETED` processing status enum value.
- **DP-010**: For truly large file support, consider streaming data in chunks or using Polars' streaming engine rather than `scan_csv().collect()`.

---

## Rollout Safety Analysis

No dependency conflicts detected among validated findings. The findings are largely independent:

- **DP-002** (cleanup logging) is isolated and safe to implement independently.
- **DP-001** (transactional wrapping) should be implemented before **DP-008** (cleanup correlation with processing log) since the latter depends on reliable status tracking.
- **DP-005** (config consolidation) should be done before **DP-006** (formula validation at model level) since both touch the config model hierarchy.
- **DP-009** (remove COMPLETED enum) is safe to do at any time — the value is unused.
- **DP-010** (streaming) is independent but higher risk due to potential Polars API changes.

### Semantic Target Stability

All validated findings target stable anchors:
- Function definitions (`_store_aggregates`, `_process_csv_file_async`, `apply_transformations`, `_parse_formula`)
- Model classes (`ProcessingConfig`, `TransformationConfig`, `CustomMetricConfig`)
- Enum definitions (`ProcessingStatus`)
- Module-level functions (`cleanup_stale_temp_files`, `load_csv`)

No fragile line-based anchors are used. All targets are resilient to unrelated code changes.

---

## Cross-Phase Conflicts

No cross-phase conflicts identified. The data processing pipeline findings are self-contained within the processing layer and do not conflict with findings from other audit phases (backend, frontend, security, database, infrastructure, tests).
