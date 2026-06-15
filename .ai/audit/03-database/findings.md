# Phase 03 Audit Findings — Database Architecture

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DB-001: Inconsistent cleanup timestamp column between starter and repository/service

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/db/starter.py`, `src/mkobi/db/repositories/processing_log_repo.py`, `src/mkobi/services/processing_log_service.py` |
| **Classification** | mandatory |

**Description:** The `DatabaseStarter.cleanup_old_logs()` method in `src/mkobi/db/starter.py` (line 380-382) filters processing logs by `started_at < :cutoff`, while `ProcessingLogRepository.delete_old_logs()` in `src/mkobi/db/repositories/processing_log_repo.py` (line 352-356) and `ProcessingLogService.cleanup_stale_processing()` in `src/mkobi/services/processing_log_service.py` (line 253-254) filter by `finished_at < cutoff`. These two queries target fundamentally different semantics: `started_at` is when processing began, `finished_at` is when it ended. Using `started_at` means the starter's cleanup can delete logs for processes that are still running (started before the cutoff but not yet finished) or recently completed. This creates a data loss risk: the startup cleanup could delete processing log entries that the stale cleanup in the service layer would correctly preserve.

**Evidence:**
- `src/mkobi/db/starter.py:379-382`:
  ```python
  "DELETE FROM processing_logs "
  "WHERE started_at < :cutoff AND status IN (:completed_status, 'failed')"
  ```
- `src/mkobi/db/repositories/processing_log_repo.py:352-356`:
  ```python
  delete(processing_log_model.ProcessingLog)
  .where(
      processing_log_model.ProcessingLog.status.in_(
          [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
      ),
      processing_log_model.ProcessingLog.finished_at < cutoff,
  )
  ```

**Recommendation:** Change `DatabaseStarter.cleanup_old_logs()` to filter on `finished_at` instead of `started_at`, consistent with the repository and service layer. A log entry with a `finished_at` before the cutoff is unambiguously old and safe to delete. Using `started_at` risks deleting logs of long-running processes.

---

### DB-002: layout_service.create_layout commits before null check

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/layout_service.py` |
| **Classification** | mandatory |

**Description:** In `LayoutService.create_layout()` (`src/mkobi/services/layout_service.py:63-67`), `await db.commit()` is called immediately after `layout_repo.create()` but **before** the `if layout_obj is None` check on line 66. If the repository's `create()` method returns `None` (which its type signature allows), the method raises `ValueError("Failed to create layout")` but the transaction has already committed. In the `except Exception` handler on line 71, `db.rollback()` is called, but a successful commit followed by an exception means the rollback is a no-op — the layout row was already persisted. Conversely, in the expected success path, the commit happens before the None check, which is logically incorrect.

**Evidence:**
- `src/mkobi/services/layout_service.py:62-74`:
  ```python
  try:
      layout_obj = await self.layout_repo.create(db=db, name=name, definition=definition)
      await db.commit()  # <-- commits before null check

      if layout_obj is None:
          raise ValueError("Failed to create layout")  # <-- commit already happened

      logger.info("Layout created: id=%s, name=%s", layout_obj.id, layout_obj.name)
      return cast(LayoutRead, LayoutRead.model_validate(layout_obj))
  except Exception as e:
      await db.rollback()
      ...
  ```

**Recommendation:** Move `await db.commit()` after the None check:
```python
layout_obj = await self.layout_repo.create(db=db, name=name, definition=definition)
if layout_obj is None:
    raise ValueError("Failed to create layout")
await db.commit()
```

---

### DB-003: Migration f47ac18b5b9e downgrade recreates redundant index

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `alembic/versions/f47ac18b5b9e_remove_redundant_dashboard_filters_index.py` |
| **Classification** | advisory |

**Description:** Migration `f47ac18b5b9e` removes `idx_dashboard_filters_dashboard_index` because it duplicates the primary key index on `(dashboard_id, filter_id)`. The migration's `downgrade()` function recreates this index as a non-unique index on `(dashboard_id, filter_id)` — exactly the same columns as the PK. The initial migration `000000000000` never created this index (the comment in the migration says "No additional index needed - PK index already covers all queries"). This means the index was created outside the migration chain at some point, and the migration was written to clean it up. However, the `downgrade()` path recreates a redundant index that duplicates the PK, which would cause unnecessary write overhead if ever rolled back on a database that didn't originally have it.

**Evidence:**
- `alembic/versions/000000000000_initial_migration.py:167-175` — only creates PK, no extra index
- `alembic/versions/f47ac18b5b9e_remove_redundant_dashboard_filters_index.py:39-41`:
  ```python
  # Downgrade recreates index on same columns as PK
  op.execute(
      "CREATE INDEX IF NOT EXISTS idx_dashboard_filters_dashboard_id "
      "ON dashboard_filters (dashboard_id, filter_id)"
  )
  ```

**Recommendation:** Either (a) update the migration comment to explain this index was created outside the migration chain and the downgrade is for backward compatibility with databases that had it, or (b) remove the downgrade entirely since this migration cleans up a non-versioned index. Add a comment: "This index was created outside the migration chain; downgrade restores it for backward compat."

---

### DB-004: auth_service.change_password and other service methods lack rollback on commit failure

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/auth_service.py`, `src/mkobi/services/graph_service.py`, `src/mkobi/services/user_service.py` |
| **Classification** | advisory |

**Description:** Several service methods call `await db.commit()` without wrapping in try/except with `db.rollback()`. Specifically:
- `AuthService.change_password()` (`auth_service.py:511`) — commits without rollback
- `AuthService.register_user()` (`auth_service.py:169`) — commits in try/except that re-raises without rollback
- `GraphService.create_graph()` (`graph_service.py:107`) — commits without rollback wrapper
- `UserService.update_last_login()` (`user_service.py:320`) — commits without rollback

While the API route layer catches exceptions and the session context manager will close the session on request end, if `db.commit()` itself fails (e.g., connection lost, serialization error), the session enters a failed state where SQLAlchemy automatically rolls back on next use. However, without explicit rollback, subsequent code in the same request that uses the session (e.g., logging, cleanup in `finally` blocks) may encounter unexpected errors.

**Evidence:**
- `src/mkobi/services/auth_service.py:508-511`:
  ```python
  await self.user_repo.update(
      user_id, db, password_hash=password_hash, force_password_change=False
  )
  await db.commit()  # <-- no try/except with rollback
  ```
- Only `dashboard_service.py`, `file_processing.py`, `layout_service.py`, and `filter_service.py` have explicit `db.rollback()` calls in their service methods.

**Recommendation:** Wrap `db.commit()` calls in try/except with `db.rollback()` in services that manage their own transactions, matching the pattern used in `layout_service.py` and `filter_service.py`. The API routes catch generic exceptions, but explicit rollback in service methods provides clearer failure semantics and prevents confusing session state issues.

Effort: small | Priority: recommended (not mandatory)

---

### DB-005: Starter cleanup_old_logs uses raw SQL with hardcoded 'failed' string

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/starter.py` |
| **Classification** | advisory |

**Description:** In `DatabaseStarter.cleanup_old_logs()` (`src/mkobi/db/starter.py:380-382`), the raw SQL query hardcodes `'failed'` as a string literal instead of using `ProcessingStatus.FAILED.value`. The repository layer uses `ProcessingStatus.COMPLETED, ProcessingStatus.Failed` as enum values. If the enum value for `FAILED` ever changes (e.g., to `'error'`), this raw SQL query would silently stop matching rows, causing old failed logs to accumulate indefinitely.

**Evidence:**
- `src/mkobi/db/starter.py:380-382`:
  ```python
  "DELETE FROM processing_logs "
  "WHERE started_at < :cutoff AND status IN (:completed_status, 'failed')"
  ```
- Compare with `src/mkobi/db/repositories/processing_log_repo.py:353-354`:
  ```python
  [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
  ```

**Recommendation:** Replace the hardcoded `'failed'` with `ProcessingStatus.FAILED.value` passed as a parameter, or use the enum directly. This also relates to finding DB-001 (the `started_at` vs `finished_at` issue).

Effort: trivial | Priority: recommended (not mandatory)

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

1. **DB-001** — Change `DatabaseStarter.cleanup_old_logs()` to filter on `finished_at` instead of `started_at`
2. **DB-002** — Move `db.commit()` after the None check in `LayoutService.create_layout()`

## Advisory Recommendations

1. **DB-003** — Document or fix the downgrade path of migration `f47ac18b5b9e`
2. **DB-004** — Add explicit rollback in service methods that call `db.commit()`
3. **DB-005** — Use `ProcessingStatus.FAILED.value` instead of hardcoded `'failed'` string in raw SQL

## Doc Updates Needed

1. **DB-003** — Add a comment to migration `f47ac18b5b9e` explaining the origin of the redundant index and the purpose of the downgrade path
