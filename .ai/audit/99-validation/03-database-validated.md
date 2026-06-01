# Validation Report — Phase 03: Database Architecture

**Validator:** validator agent
**Date:** 2026-06-01
**Input:** `.ai/audit/03-database/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted | Rejected | Reclassified | Merged |
|----------------|-------|----------|----------|--------------|--------|
| Mandatory | 4 | 3 | 0 | 1 | 0 |
| Advisory | 6 | 5 | 1 | 0 | 0 |
| **Total** | **10** | **8** | **1** | **1** | **0** |

---

## Rejected Findings

### DB-10: Storage Service Creates Model Object Outside Transaction, References It After Potential Rollback — REJECTED

**Rejection reason:** The finding mischaracterizes the actual risk in `LayoutService.create_layout`. Close reading of `layout_service.py:62-74` reveals:

1. `layout_repo.create()` (line 63) calls `db.flush()` and `db.refresh()` — if it fails, it raises `SQLAlchemyError`, caught by the `except` block at line 71 which calls `db.rollback()`.
2. `db.commit()` (line 64) — if it raises, the same `except` block catches it and rolls back.
3. `LayoutRead.model_validate(layout_obj)` (line 70) is **only reached if commit succeeded**. The control flow is safe.
4. The `if layout_obj is None` check at line 66 is indeed dead code (the repo raises rather than returning None), but this is a minor code quality issue, not a transaction safety problem.

The finding claims "if commit raises an exception after the object was temporarily assigned an ID during flush, the object may be in a detached or invalid state" — but the exception handler rolls back and re-raises, so `model_validate` is never reached in the failure path. The transaction pattern `create → commit → validate` with try/except rollback is **safe**. The dead code is worth noting but does not justify a BEST-PRACTICE finding about transaction safety.

**Recommendation:** Reject DB-10. If desired, log a minor advisory note about the dead `if layout_obj is None` check separately.

---

## Reclassified Findings

### DB-02: Reclassified `RUNTIME-ERROR` → `SPEC-DEVIATION`

| Field | Original | Updated |
|-------|----------|---------|
| **ID** | DB-02 | DB-02 |
| **Severity** | HIGH | HIGH |
| **Type** | RUNTIME-ERROR | SPEC-DEVIATION |
| **Classification** | mandatory | mandatory |
| **Status** | ACCEPTED (reclassified) | — |

**Rationale:** The finding describes a structural mismatch between ORM model declarations (`unique=True`, `UniqueConstraint`) and migration DDL (`CREATE UNIQUE INDEX`). This is confirmed — SQLAlchemy's autogenerate sees these as different objects, causing `alembic check` to always report drift. However, this is **not a runtime error**: the database functions correctly (uniqueness is enforced either way), and no code path crashes. The problem is a **migration/ORM alignment deviation** — the migration DDL should use `op.create_unique_constraint()` instead of raw `op.execute("CREATE UNIQUE INDEX ...")` to match SQLAlchemy's representation. The `RUNTIME-ERROR` type overstates the severity; `SPEC-DEVIATION` accurately captures the nature of the issue.

**Recommendation adjusted:** Keep the same fix (replace raw SQL with proper Alembic API calls), but classify as `SPEC-DEVIATION` since the database works correctly today — it is the tooling (`alembic check`, autogenerate) that is broken, not the application.

---

## Cross-Phase Conflicts

### DB-07 ↔ Phase 01 (Backend) Test Infrastructure

DB-07 reports the test database has 60 columns vs production's 61, missing `force_password_change`. This is an **environment/bootstrap issue**, not a code defect. The migration code (`a1b2c3d4e5f6`) and ORM model (`user.py:67-72`) both correctly include the column. The issue is that the test database on port 5433 was not recreated after the branch migration was added. No conflict with Phase 01 — Phase 01 did not make claims about test DB schema completeness.

### DB-02 Reclassification ↔ Phase 01 Findings

DB-02 was reclassified from `RUNTIME-ERROR` to `SPEC-DEVIATION`. Phase 01 also reclassified a `RUNTIME-ERROR` (BE-001) to `SPEC-DEVIATION`. Both reclassifications follow the same principle: the `RUNTIME-ERROR` type should be reserved for issues that cause actual runtime failures, not tooling/migration misalignments. No conflict — consistent validation approach.

---

## Rollout Safety Analysis

### DB-01 (Migration Branch Elimination): MODERATE RISK

- **Risk:** Squashing 6 migrations into one (`7130ecb0388c` through `64730d3d3446`) requires dropping and recreating the test database. For production, if the migrations have already been applied (which they have, since the DB has the `force_password_change` column), a squash requires manual intervention: stamp the new squashed revision rather than running `alembic upgrade`.
- **Dependency:** Must be done before DB-02 fix, because DB-02's fix (replacing raw SQL with Alembic API) should be applied to the squashed migration, not the original branched ones.
- **Mitigation:** In development/test, `dropdb + createdb + alembic upgrade head` is sufficient. In production, use `alembic stamp` to mark the new revision as applied without re-running DDL.

### DB-02 (Unique Constraint Alignment): LOW RISK

- **Risk:** Replacing `CREATE UNIQUE INDEX` with `op.create_unique_constraint()` in a migration that runs after the table already exists with the index would drop the index and recreate it as a constraint. On a large table, this could briefly lock the table.
- **Dependency:** Should be done after DB-01 (squash), since the squashed migration would incorporate the fix directly.
- **Mitigation:** If tables are small (expected for a BI dashboard), the lock duration is negligible. For safety, use `op.execute('ALTER TABLE ... ADD CONSTRAINT ... USING INDEX ...')` which converts an existing index to a constraint without rebuilding.

### DB-06 (Drop Redundant Index): LOW RISK

- **Risk:** Dropping `idx_dashboard_filters_dashboard_id` via migration. Concurrent queries using this index would need to switch to the primary key index. PostgreSQL's `DROP INDEX CONCURRENTLY` avoids locks but cannot be used inside a transaction block in Alembic by default.
- **Migration sequencing:** This is independent of other findings. Can be done in any order.

### DB-07 (Test Database Recreation): LOW RISK

- **Risk:** None to production. Only affects test environment.
- **Action:** Before recreation, ensure `docker compose down -v` destroys the test DB volume, then `alembic upgrade head` replays all migrations linearly (after DB-01 squash).

### DB-03, DB-04, DB-05 (Add Missing Indexes): LOW RISK

- **Risk:** `CREATE INDEX CONCURENTLY` is the safe default for adding indexes on live tables. Three independent migrations, can be applied in any order or combined into one.
- **Dependency:** None. Each index is on a different table.

### DB-08 (Composite Index on processing_logs): LOW RISK

- **Risk:** Adding a composite index on `(status, started_at)` via `CREATE INDEX CONCURRENTLY`. Independent of other findings.
- **Dependency:** None.

### DB-09 (Transaction Boundary in DashboardService): MEDIUM RISK

- **Risk:** Changing the transaction boundary pattern in `create_dashboard` from implicit (flush in service, commit in route) to explicit (`async with db.begin()`) changes the session lifecycle. If other services or the route handler assume commit authority, this could cause double-commit or commit-after-rollback errors.
- **Dependency:** None. Self-contained to `DashboardService`.
- **Mitigation:** The fix should also update the route handler (`dashboards_crud.py:125`) to remove the `await db.commit()` call, since the service would now manage its own transaction. This is a two-file change that must be atomic.

---

## Rollout Sequencing Recommendation

1. **DB-01** first — squash migrations to eliminate the branch (foundational; other migration fixes should target the squashed chain).
2. **DB-07** in parallel — recreate test DB (environment fix, independent of code).
3. **DB-02** second — fix unique constraint alignment in the squashed migration.
4. **DB-03, DB-04, DB-05, DB-06, DB-08** — can be done in any order or combined into one migration.
5. **DB-09** last — transaction boundary refactor, requires coordinated change across service + route handler.

---

## Summary of Actions Required

1. **DB-01:** Validated. Accepted as-is. Squash branched migrations into a single linear chain.
2. **DB-02:** Reclassified `RUNTIME-ERROR` → `SPEC-DEVIATION`. Mandatory fix remains; type correction only.
3. **DB-03 through DB-06, DB-07, DB-08, DB-09:** Validated as-is. No corrections needed.
4. **DB-10:** Rejected. The transaction pattern is safe; the dead code is a minor quality issue not warranting a BEST-PRACTICE finding.
5. **No merges** — no findings share duplicate root causes.
6. **One cross-phase note** — DB-07's environment issue is consistent with the branched migration chain (DB-01). Once DB-01 is squashed, test DB recreation will correctly apply all migrations linearly.
