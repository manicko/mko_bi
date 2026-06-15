# Phase 03 Audit Validation Report — Database Architecture

**Validator:** validator
**Source Findings:** `.ai/audit/03-database/findings.md`
**Status:** complete

---

## Validation Summary

5 findings analyzed. 2 validated mandatory, 2 validated advisory, 1 rejected.

---

## Rejected Findings

### DB-004 REJECTED

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Original Type** | BEST-PRACTICE |
| **Rejection Reason** | Evidence references a method `update_last_login` at `user_service.py:320` that does not exist. Line 320 in user_service.py contains `await db.commit()` inside `delete_user()` method, not `update_last_login`. No such method exists anywhere in the codebase. The finding's evidence is stale and inaccurate. |
| **Verification** | Searched `src/mkobi` for `update_last_login` - no matches found. The user_service.py file has 347 lines and ends at `get_all_users()`. The `update_last_login` method referenced in the audit was never implemented or has been removed. |

**Note:** While DB-004's concern about missing rollback patterns in some service methods is partially valid (see analysis below), the specific evidence provided is factually incorrect, making the finding unsupportable as filed.

---

## Validated Findings (Mandatory)

### DB-001 VALIDATED

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory |

**Verification:**
- `starter.py:381-382`: Uses `started_at < :cutoff` in DELETE query
- `processing_log_repo.py:356`: Uses `finished_at < cutoff` in delete_old_logs
- The semantic difference is critical: `started_at` filter can delete logs of long-running processes still in progress, while `finished_at` correctly identifies only completed/failed processes old enough to be safely removed.

**Risk:** Data loss - logs of in-progress processes may be incorrectly deleted on startup.

---

### DB-002 VALIDATED

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory |

**Verification:**
- `layout_service.py:62-74`: Confirms `await db.commit()` at line 64 executes before the `if layout_obj is None` check at line 66.
- `layout_repo.py:105-129`: The `create()` method returns `Layout | None` (None on SQLAlchemy error), meaning the None check is meaningful.
- Even though `db.add()` + `flush()` typically succeeds in creating the object, the transaction semantics are incorrect - commit should only occur after validation.

**Risk:** Transaction completed before business logic validation; rollback in exception handler is ineffective after successful commit.

---

## Validated Findings (Advisory)

### DB-003 VALIDATED

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Classification** | advisory |

**Verification:**
- Initial migration `000000000000_initial_migration.py:164-175` creates `dashboard_filters` table with only PRIMARY KEY on `(dashboard_id, filter_id)` - no additional index created.
- Migration `f47ac18b5b9e` drops `idx_dashboard_filters_dashboard_id` which was not created in the migration chain (the finding incorrectly references `idx_dashboard_filters_dashboard_index`). The index was created manually or in an unversioned migration.
- Downgrade recreates this redundant index on the same columns as the PK.

**Risk:** Low - unnecessary write overhead if downgrade is executed on databases that never had the index originally. The recommendation to document the index's external origin is valid.

### DB-005 VALIDATED

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |

**Verification:**
- `starter.py:382`: Hardcoded `'failed'` string instead of `ProcessingStatus.FAILED.value`
- The enum value (`"failed"`) matches, but using the enum directly is the documented pattern for maintainability

**Recommendation:** Use enum value consistently with repository layer pattern.

---

## Findings Count

| Phase | Mandatory Validated | Advisory Validated | Rejected | Total |
|-------|---------------------|-------------------|----------|-------|
| 03-database | 2 | 2 | 1 | 5 |

---

## Cross-Phase Conflicts

None detected. No conflicts with other audit phases identified.

---

## Actionable Recommendations

### DB-001: Fix `started_at` filter in `cleanup_old_logs` — use `finished_at`

**Severity:** HIGH | **File:** `src/mkobi/db/starter.py:381-382`

**Problem:** The DELETE query in `cleanup_old_logs` filters on `started_at < :cutoff`, which can delete logs of long-running processes that started before the cutoff but are still in progress (not yet in a terminal state). Although the query includes `status IN (:completed_status, 'failed')`, the `started_at` filter is semantically wrong — the repository layer (`processing_log_repo.py:356`) and the `file_cleanup.py:143` service both correctly use `finished_at < cutoff`. The `started_at` filter is redundant given the status check, but if kept, it creates a subtle bug: a process that started 30 days ago, completed yesterday, and has `status = 'completed'` would be deleted even though its `finished_at` is recent, because `started_at` exceeds the cutoff.

**Recommended change:**

Replace line 381-382 in `src/mkobi/db/starter.py`:

```python
# BEFORE:
"WHERE started_at < :cutoff AND status IN (:completed_status, 'failed')"

# AFTER:
"WHERE finished_at < :cutoff AND status IN (:completed_status, :failed_status)"
```

And update the parameters dict on line 384:

```python
# BEFORE:
{"cutoff": cutoff_date, "completed_status": ProcessingStatus.COMPLETED.value}

# AFTER:
{
    "cutoff": cutoff_date,
    "completed_status": ProcessingStatus.COMPLETED.value,
    "failed_status": ProcessingStatus.FAILED.value,
}
```

**Why this approach:**

1. **Semantic correctness:** `finished_at` is the timestamp that indicates when a process truly completed or failed. It is the correct field to determine "age" of a log entry. A log is only safe to delete when the process has *finished* and that finish time exceeds the retention period.
2. **Consistency:** This aligns `starter.py` with the established pattern in `processing_log_repo.py:356` and `file_cleanup.py:143`, both of which use `finished_at < cutoff`.
3. **Fixes DB-005 simultaneously:** Using `ProcessingStatus.FAILED.value` instead of the hardcoded `'failed'` string resolves DB-005 as well.
4. **No schema change needed:** The `processing_logs` table already has a `finished_at` column (nullable, set to `None` until the process reaches a terminal state). The existing composite index `idx_processing_logs_status_finished_at` on `(status, finished_at)` ensures this query is index-backed.

**Alternatives considered:**

- *Keep `started_at` but add `finished_at IS NOT NULL`:* This would prevent deletion of in-process logs but still has the semantic issue of deleting recently-finished logs whose `started_at` is old. Rejected.
- *Remove the time filter entirely, rely only on status:* This would only delete logs when they reach a terminal state regardless of age, defeating the purpose of retention-based cleanup. Rejected.

---

### DB-002: Move `db.commit()` after the `None` check in `create_layout`

**Severity:** MEDIUM | **File:** `src/mkobi/services/layout_service.py:62-74`

**Problem:** `await db.commit()` on line 64 executes before the `if layout_obj is None` check on line 66. If `layout_repo.create()` returns `None` (which its signature `Layout | None` allows), the transaction is already committed before the validation check runs. The `except` block's `await db.rollback()` on line 72 is ineffective after a successful commit. While the current `layout_repo.create()` implementation raises `SQLAlchemyError` rather than returning `None` (the `None` in the return type is from `cast()`), the service layer should not depend on this implementation detail — the `None` check exists precisely to handle the `None` return path.

**Recommended change:**

In `src/mkobi/services/layout_service.py`, lines 62-74, reorder the commit and None check:

```python
# BEFORE (lines 62-74):
try:
    layout_obj = await self.layout_repo.create(db=db, name=name, definition=definition)
    await db.commit()

    if layout_obj is None:
        raise ValueError("Failed to create layout")

    logger.info("Layout created: id=%s, name=%s", layout_obj.id, layout_obj.name)
    return cast(LayoutRead, LayoutRead.model_validate(layout_obj))
except Exception as e:
    await db.rollback()
    logger.error("Error creating layout name=%s: %s", name, e, exc_info=True)
    raise

# AFTER:
try:
    layout_obj = await self.layout_repo.create(db=db, name=name, definition=definition)

    if layout_obj is None:
        raise ValueError("Failed to create layout")

    await db.commit()

    logger.info("Layout created: id=%s, name=%s", layout_obj.id, layout_obj.name)
    return cast(LayoutRead, LayoutRead.model_validate(layout_obj))
except Exception as e:
    await db.rollback()
    logger.error("Error creating layout name=%s: %s", name, e, exc_info=True)
    raise
```

**Why this approach:**

1. **Correct transaction semantics:** Commit only after all business logic validation passes. If `layout_obj is None`, the exception handler's `rollback()` correctly undoes the `flush()` from `layout_repo.create()`.
2. **Minimal change:** Only the order of `await db.commit()` and the `None` check is swapped. No new imports, no signature changes, no architectural changes.
3. **Defensive programming:** The service layer should be robust against the repository's declared return type (`Layout | None`), regardless of the current implementation's behavior.
4. **Follows existing pattern:** Other services in the codebase (e.g., dashboard creation) follow the pattern of validate-then-commit.

**Alternatives considered:**

- *Remove the `None` check entirely since `create()` raises instead of returning `None`:* This would work today but creates a hidden coupling to the repository's internal error-handling behavior. If the repository is ever refactored to return `None` on certain errors instead of raising, the service would break silently. Rejected.
- *Move commit into the repository layer:* This would violate the current architecture where the service layer manages transactions and the repository layer only handles data access with `flush()`. Rejected.

---

### DB-003: Document the externally-created index in migration `f47ac18b5b9e`

**Severity:** LOW | **File:** `alembic/versions/f47ac18b5b9e_remove_redundant_dashboard_filters_index.py`

**Problem:** The index `idx_dashboard_filters_dashboard_id` was not created by any versioned Alembic migration — the initial migration's `dashboard_filters` table definition only has `PRIMARY KEY (dashboard_id, filter_id)`. The index was created externally (manually, or via a non-versioned migration). The downgrade recreates this index on `(dashboard_id, filter_id)`, which is the same column set as the primary key, making it truly redundant. The migration's docstring should explain the index's origin so future maintainers understand why `DROP INDEX IF EXISTS` is used and why the downgrade recreates something that was never in the migration chain.

**Recommended change:**

Update the module docstring and downgrade docstring in `alembic/versions/f47ac18b5b9e_remove_redundant_dashboard_filters_index.py`:

```python
"""Remove redundant index on dashboard_filters table.

The PRIMARY KEY constraint on (dashboard_id, filter_id) already creates
a unique index (dashboard_filters_pkey) that serves all queries. The
non-unique idx_dashboard_filters_dashboard_id index was created externally
(e.g., manually or via a non-versioned migration) and is redundant — it
covers the same column set as the PK and only adds unnecessary write overhead.

This migration uses DROP INDEX IF EXISTS to safely handle databases where
the index may or may not exist.

Revision ID: f47ac18b5b9e
Revises: b749bc53b1ee
Create Date: 2026-06-10 22:00:00.000000

"""
```

And update the `downgrade()` docstring:

```python
def downgrade() -> None:
    """Recreate the redundant index for rollback compatibility.

    Recreates idx_dashboard_filters_dashboard_id which was originally
    created externally (not via Alembic). The index is redundant with
    the PRIMARY KEY on (dashboard_id, filter_id) and is only recreated
    to support downgrade paths on databases where it previously existed.

    Note: This index is safe to leave in place if downgrade is executed
    on a database that never had it — it will simply be an unused index.
    """
```

**Why this approach:**

1. **Documents the anomaly:** The key information future maintainers need is that the index was *not* created by the migration chain. Without this context, the `DROP INDEX IF EXISTS` and the downgrade's `CREATE INDEX IF NOT EXISTS` look like mistakes.
2. **No code changes needed:** The migration logic is correct — `IF EXISTS` / `IF NOT EXISTS` guards handle all cases safely. Only the documentation is updated.
3. **Prevents future "correction":** Without documentation, a future developer might "fix" the migration by removing the downgrade or changing the column list, not understanding the index's external origin.

**Alternatives considered:**

- *Remove the downgrade entirely:* This would break Alembic's ability to roll back past this migration. The downgrade is harmless (creates an unused index) and maintains migration chain integrity. Rejected.
- *Change the downgrade to drop the PK index instead:* This would be incorrect — the PK index is structural and cannot be dropped independently. Rejected.

---

### DB-005: Replace hardcoded `'failed'` with `ProcessingStatus.FAILED.value`

**Severity:** LOW | **File:** `src/mkobi/db/starter.py:382`

**Problem:** Line 382 uses a hardcoded `'failed'` string literal in the SQL query's `IN` clause, while line 384 already uses `ProcessingStatus.COMPLETED.value` for the completed status. This inconsistency means a future rename of the `FAILED` enum value (or a typo in the hardcoded string) would cause a silent query bug — the DELETE would no longer match failed logs.

**Note:** This fix is already included in the DB-001 recommendation above. The DB-001 fix changes the query to use `ProcessingStatus.FAILED.value` as a bound parameter (`:failed_status`) instead of a hardcoded string. Implementing DB-001 automatically resolves DB-005.

**Recommended change:** See DB-001. No separate action needed.

**Why no separate fix:**

The DB-001 fix replaces the entire WHERE clause and parameter dict, which inherently replaces the hardcoded `'failed'` with `ProcessingStatus.FAILED.value`. Applying a separate fix for DB-005 would conflict with the DB-001 change.