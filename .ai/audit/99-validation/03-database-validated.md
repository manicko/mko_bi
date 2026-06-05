---
name: 03-database-validated
description: Validated database audit findings
agent: validator
alwaysApply: false
problems-only: true
---

# Phase 03 Validation Report — Database Structure

**Validator:** validator
**Source:** .ai/audit/03-database/findings.md
**Mode:** problems-only

---

## Merged Findings

| Original IDs | Merged ID | Rationale |
|---|---|---|
| DB-001 (Phase 03), INT-003 (Phase 90) | DB-001 | Both findings address the same root cause: the PostgreSQL `processing_status` ENUM contains an extra `"success"` value not present in the Python `ProcessingStatus` StrEnum. DB-001 focuses on the schema drift and raw SQL dependency in `db/starter.py`; INT-003 focuses on the frontend-backend type inconsistency arising from the same enum mismatch. Merged under DB-001 as the database-phase finding is the more complete description. |

### Merged Finding: DB-001 — ProcessingStatus ENUM schema drift

| Field | Value |
|-------|-------|
| **ID** | DB-001 (merged; INT-003 subsumed) |
| **Severity** | MEDIUM |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `alembic/versions/000000000000_initial_migration.py`, `src/mkobi/models/enums.py`, `src/mkobi/db/starter.py`, `frontend/src/shared/types/enums.ts` |
| **Classification** | advisory |

**Validated Description:** The PostgreSQL `processing_status` ENUM type includes a `"success"` value that does not exist in the Python `ProcessingStatus` StrEnum. The Python enum has `COMPLETED` but no `SUCCESS`. The raw SQL in `db/starter.py:353` hardcodes `'success'` in a WHERE clause, creating a hidden dependency on an unused enum value. The frontend `enums.ts` has a deprecated `SUCCESS` alias mapped to `"completed"`, adding further confusion.

**Evidence Verified:**
- Migration ENUM (`alembic/versions/000000000000_initial_migration.py:38-47`): Contains `"success"` — confirmed present.
- Python StrEnum (`src/mkobi/models/enums.py:58-65`): No `SUCCESS` value — confirmed absent. Has `COMPLETED` instead.
- Raw SQL (`src/mkobi/db/starter.py:353`): `WHERE started_at < :cutoff AND status IN ('success', 'failed')` — confirmed hardcoded `'success'` string.
- Test (`tests/test_enum_db_consistency.py:173-196`): Explicitly documents the drift as informational — confirmed.

**Validated Recommendation:** Remove the unused `"success"` value from the `processing_status` ENUM in the migration, and update the raw SQL in `db/starter.py` to use `ProcessingStatus.COMPLETED.value` instead of the hardcoded string `'success'`. The frontend should remove the deprecated `SUCCESS` alias. This ensures consistency across all three layers (database, backend, frontend).

**Rollout Safety:**
- This is a schema migration change (removing an ENUM value). It requires:
  1. A new Alembic migration to remove `"success"` from the `processing_status` ENUM.
  2. Code change in `db/starter.py` to replace hardcoded `'success'` with `ProcessingStatus.COMPLETED.value`.
  3. No data migration is needed if no rows reference `'success'` status — must be verified before deployment.
- **Risk:** If any `processing_log` rows have `status = 'success'`, the ENUM alteration will fail. A data migration step is required to update those rows to `'completed'` before the ENUM change.
- **Rollback:** Safe — adding an ENUM value back is straightforward.
- **Sequencing:** Must run before any frontend changes that depend on enum consistency.

---

## Cross-Phase Conflicts

| Conflict | Finding IDs | Resolution |
|----------|-------------|------------|
| Same root cause: extra `"success"` in DB ENUM | DB-001 (Phase 03), INT-003 (Phase 90) | Merged into DB-001. INT-003 is a duplicate finding from the integration phase that describes the same schema drift from a frontend-backend type alignment perspective. No conflict — both describe the same problem. |

---

## Validated Counts

| Category | Count |
|----------|-------|
| Mandatory fixes | 0 |
| Advisory recommendations | 1 (DB-001 merged with INT-003) |
| **Total validated** | **1** |

### Advisory
- **DB-001:** Remove unused `"success"` value from `processing_status` PostgreSQL ENUM to align with Python StrEnum. Update `db/starter.py` to use enum values dynamically. Remove deprecated `SUCCESS` alias from frontend enums.

---

## Rollout Safety Analysis

**Dependency Graph:**
```
DB-001:
  1. Verify no rows in processing_logs have status='success'
  2. Data migration: UPDATE processing_logs SET status='completed' WHERE status='success' (if needed)
  3. Schema migration: Remove 'success' from processing_status ENUM
  4. Code change: db/starter.py line 353 — replace 'success' with ProcessingStatus.COMPLETED.value
  5. Frontend cleanup: Remove deprecated SUCCESS alias from enums.ts
```

**Risks:**
- **Data dependency:** If rows exist with `status='success'`, step 3 will fail. Must verify before deployment.
- **Raw SQL coupling:** The hardcoded `'success'` in `db/starter.py:353` means the code is already broken if someone queries for `'success'` status via the Python enum (which doesn't have it). This is a latent bug, not just a schema cleanup.
- **Frontend alignment:** The deprecated `SUCCESS` alias in the frontend creates confusion but is not a runtime error since it maps to `"completed"`.

**Execution Safety:** All steps are isolated and sequential. No circular dependencies. Safe parallel execution of steps 4 and 5 after step 3 completes.

---

## Execution Warnings

1. **ENUM alteration in PostgreSQL:** Removing a value from a PostgreSQL ENUM requires `ALTER TYPE ... DROP VALUE` (PG 10+) or a recreate-and-reassign approach. Verify PostgreSQL version compatibility before writing the migration.
2. **No `print()` in migration:** Ensure the migration uses `op.execute` with proper Alembic constructs, not raw `print()` statements.
3. **Test update required:** `test_enum_db_consistency.py` lines 189-196 log an informational message about extra DB values. After the fix, this informational path should no longer trigger. The test should be updated to assert zero extra values, not just log them.
