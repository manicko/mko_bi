# Phase 3 Audit Findings — Database Structure

**Executor:** audit-executor
**Template:** .kilo/commands/audit/db/audit-db-structure.md
**Status:** complete

---

## Findings

### DB-001: ProcessingStatus ENUM schema drift — extra "success" value in database not used by Python code

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | MEDIUM |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `alembic/versions/000000000000_initial_migration.py`, `src/mkobi/models/enums.py`, `src/mkobi/db/starter.py` |
| **Classification** | advisory |

**Description:** The PostgreSQL `processing_status` ENUM type includes a `success` value that does not exist in the Python `ProcessingStatus` StrEnum. This creates schema drift between the database and application code, which can cause confusion and potential issues if someone attempts to query for or insert "success" using the Python enum. The value is also referenced in raw SQL in `db/starter.py` line 353, creating a hidden dependency on an unused enum value.

**Evidence:**
- Database ENUM definition (`alembic/versions/000000000000_initial_migration.py`, lines 38-47):
  ```python
  processing_status_enum = ENUM(
      "started",
      "uploaded",
      "processing",
      "success",      # Extra value
      "failed",
      "completed",
      name="processing_status",
  )
  ```
- Python StrEnum (`src/mkobi/models/enums.py`, lines 58-65):
  ```python
  class ProcessingStatus(StrEnum):
      STARTED = "started"
      UPLOADED = "uploaded"
      PROCESSING = "processing"
      COMPLETED = "completed"
      FAILED = "failed"
      # "success" is missing
  ```
- Raw SQL reference (`src/mkobi/db/starter.py`, line 353):
  ```python
  "WHERE started_at < :cutoff AND status IN ('success', 'failed')"
  ```

**Recommendation:** Remove the unused `success` value from the `processing_status` ENUM in the migration, and update the raw SQL in `db/starter.py` to use `ProcessingStatus.COMPLETED.value` instead of the hardcoded string `'success'`. This ensures consistency between Python code and database schema, and eliminates the need for the informational log warning in `test_enum_db_consistency.py`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 0 |

## Advisory Recommendations

- **DB-001:** Remove unused `success` value from `processing_status` PostgreSQL ENUM to align with Python StrEnum. Update `db/starter.py` to use enum values dynamically.

## Doc Updates Needed

No documentation updates are required. The codebase is internally consistent once the schema drift is resolved.

---

## Detailed Analysis

### Enum Mappings Verification

| PostgreSQL ENUM | Values | StrEnum Class | Status |
|---------------|--------|---------------|--------|
| `user_role` | admin, editor, viewer | `UserRole` | Consistent |
| `dashboard_permission_level` | view, edit, admin | `DashboardPermission` | Consistent |
| `graph_type` | bar, line, pie, table | `GraphType` | Consistent |
| `filter_type` | select, multiselect, range, date | `FilterType` | Consistent |
| `processing_status` | started, uploaded, processing, success, failed, completed | `ProcessingStatus` (missing "success") | Schema drift |
| `registration_status` | pending, approved, rejected | `RegistrationStatus` | Consistent |

### Test Coverage

The test file `tests/test_enum_db_consistency.py` correctly identifies this drift:
- Line 173-174: Documents that extra values in PostgreSQL (like 'success') are allowed
- Line 189-196: Logs informational message about extra database values
- Line 90-92: Frontend test expects 6 statuses (includes deprecated SUCCESS mapped to 'completed')