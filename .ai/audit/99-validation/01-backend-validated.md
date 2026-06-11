---
name: 01-backend-validated
description: Validated backend audit findings
agent: validator
alwaysApply: false
---

# Phase 01 Audit Findings Validation — Backend

**Validator:** validator  
**Source:** `.ai/audit/01-backend/findings.md`  
**Mode:** problems-only

---

## Rejected Findings

### BE-004: Incompatible Type Assignment in ProcessingConfig Validation

**Status:** INVALID — No issue exists

**Evidence:**
- `data_worker.py:127-129` iterates `for metric in config.metrics` and calls `metric.items()`
- `ProcessingConfig.metrics` is typed as `list[dict[str, str]] | None` (data.py:127)
- The code correctly iterates over `dict[str, str]` items

**Rationale:** The audit finding confuses `config.metrics` with `config.custom_metrics`. The `metrics` field uses `dict[str, str]`. The `custom_metrics` field (lines 111-124 in data_worker.py) uses `CustomMetricConfig` with `name` and `expr` attributes. The code at line 129 is valid and no mypy error would occur for the `metrics` iteration.

---

## Reclassified Findings

### BE-001: Behavior Clarification (Type Mismatch Remains Valid)

**Original Type:** SPEC-DEVIATION  
**New Classification:** SPEC-DEVIATION (confirmed valid) with behavioral analysis

**Analysis:** The type mismatch is valid - `log.dashboard_id` (`UUID | None`) is passed to `delete(dashboard_id: UUID)`. However, the behavioral concern differs from the original finding:
- When `dashboard_id` is `None`, the SQL `WHERE dashboard_id == NULL` evaluates to UNKNOWN and deletes zero rows
- This silently fails to delete orphaned logs instead of raising an error
- The current behavior is inconsistent with the method's purpose (deleting all logs for a dashboard)

**Recommendation:** Add null check before calling delete. If `dashboard_id` is `None`, either raise an error or log a warning since the operation cannot proceed meaningfully.

---

## Cross-Finding Dependencies

### BE-002 and BE-003: Shared Root Cause

Both findings originate from `ProcessingLogRead.dashboard_id` being nullable while passed to non-nullable `UUID` parameters:

| Finding | Location | Target |
|---------|----------|--------|
| BE-002 | data_service.py:325,353 | check_dashboard_access(dashboard_id: UUID) |
| BE-003 | data_service.py:364 | get_by_dashboard_id(dashboard_id: UUID) |

**Unified Fix:** Add null guards in `data_service.py` before calls to these methods. If `dashboard_id` is `None`, raise `ValueError` since a processing log without dashboard cannot be meaningfully accessed.

---

## Rollout Safety Issues

### BE-007: Temp File Accumulation

**Evidence:** 172 files currently in `data/tmp_uploads/` from previous test runs.

**Risk:** Disk exhaustion in CI environments; test isolation issues.

**Current Cleanup:**
- Production: `data_worker.py` cleans up temp files on success (line 430) and error (lines 458-467, 491-498)
- Tests: Only `test_file_cleanup.py` has cleanup via `setup_temp_dir_fixture`

**Recommendation:** Add session-scoped autouse cleanup fixture in `conftest.py` to call `cleanup_stale_temp_files()` after all tests complete.

---

## Valid Findings Summary

| Severity | Valid Findings | Classification |
|----------|---------------|----------------|
| HIGH | 2 (BE-001, BE-007) | Mandatory |
| MEDIUM | 2 (BE-002, BE-003) | Mandatory |
| LOW | 3 (BE-005, BE-006, BE-008) | Advisory |

**Total Rejected:** 1 (BE-004)

---

**Validator Signature:** Trust evidence, not claims. Code has priority over assumptions.