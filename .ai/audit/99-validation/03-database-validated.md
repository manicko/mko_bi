---
name: 03-database-validated
description: Database Audit Validation Report
status: complete
phase: 03-database
---

# Phase 03 Database — Validation Report

**Validator:** validator agent
**Source findings:** `.ai/audit/03-database/findings.md`
**Scope:** Database Architecture (5 findings)
**Mode:** problems-only

---

## Rejected Findings

### DB-004: Redundant Index on `aggregated_data` Table
- **Original type:** BEST-PRACTICE
- **Original severity:** MEDIUM
- **Rejection reason (INACCURATE PREMISE / INDEX DOES NOT EXIST):** The finding claims the `aggregated_data` table has both a composite index on `(dashboard_id, graph_id)` AND a separate individual index on `dashboard_id`, making the individual index redundant. However, inspection of the current codebase shows:

  - `idx_aggregated_data_dashboard_graph` `(dashboard_id, graph_id)` — exists ONLY in migration `a2153f0f6094` (added later) and in the model `aggregated_data.py:52`. It does **NOT** exist in the initial migration.
  - `idx_aggregated_data_dashboard_id` `(dashboard_id)` — exists in the initial migration `7130ecb0388c:160` and in the model `aggregated_data.py:51`.

  The finding references line 160-161 of the initial migration as containing both the composite and individual indexes, but this is **wrong**. The composite index was added in a **separate migration** (`a2153f0f6094`) — AFTER the individual index already existed. The initial migration `7130ecb0388c` only creates individual indexes on lines 160-161 (`dashboard_id` and `graph_id` respectively) plus the GIN index on `dims` on line 162.

  Now that the composite index has been added by the later migration, the `dashboard_id` index IS technically redundant in databases where both indexes exist. But the finding's **evidence references are incorrect** — it cites the same migration file containing both indexes, which is false. The redundancy was introduced by migration `a2153f0f6094`, not the initial migration.

  Furthermore, the actual optimizer behavior depends on the query planner. PostgreSQL can use the composite index for `dashboard_id`-only queries, but the individual index may still be preferred in some plans. Dropping the individual index requires careful analysis of actual query patterns. The finding provides no evidence of query plans or real-world workload analysis.

  **Verdict: REJECTED.** The finding's evidence is factually wrong (cites wrong source lines for the composite index), and the recommendation to drop an existing index without plan analysis is operationally unsafe. If the redundancy needs to be addressed, it should be done via a new analysis-driven finding, not this one.

---

## Merged Findings

### DB-001 + DB-005 → DB-001
- **DB-001:** Broken Trigger in Initial Migration for Non-Existent Column (CRITICAL, SPEC-DEVIATION)
- **DB-005:** Migration Chain Has Repair Migration Instead of Fixing Root Cause (MEDIUM, SPEC-DEVIATION)
- **Merge rationale:** Both findings address the exact same root cause — the initial migration `7130ecb0388c` creates a trigger `update_graphs_updated_at` on the `graphs` table that references a non-existent `updated_at` column. DB-001 identifies the broken trigger itself (CRITICAL). DB-005 identifies the symptom — a repair migration `ffd23f1f7e2b` that drops the broken trigger (MEDIUM). DB-005 is a direct consequence of DB-001. The fix for DB-001 (remove the broken trigger creation from the initial migration) inherently eliminates DB-005's concern (the repair migration becomes unnecessary). Keeping both would produce duplicate work and conflicting semantic anchors (both target the initial migration file).
- **Retained as:** DB-001 (CRITICAL, SPEC-DEVIATION, mandatory)

---

## Reclassified Findings

### DB-002: Missing GIN Index on `aggregated_data.metrics` Column
- **Original type:** BEST-PRACTICE
- **Reclassified type:** DOC-UPDATE
- **Rationale:** The finding recommends adding a GIN index on `metrics` in anticipation of future metric filtering. However, inspection of `aggregated_data_repo.py:130-178` shows that **all** current filter operations filter exclusively on `dims` (line 141: "Optional dictionary of filters for JSONB field dims", line 161: `.dims[key].astext`). There is zero code path that filters on `metrics`. Adding an index for a query pattern that does not yet exist is premature optimization — it would add write overhead for a read path that doesn't exist.

  The finding also states "the system architecture should support symmetric querying on both dimension and metric data for flexibility" — this is speculative. The current architecture (docs + code) only uses `dims` for filtering. The index documentation at `docs/09-database/indexes.md` should be updated to note that the GIN index covers `dims` (the filter dimension) and that `metrics` is not indexed because it is not used in WHERE clauses — this explains the design decision rather than treating it as an oversight.

  **Reclassified as DOC-UPDATE:** Update `docs/09-database/indexes.md` to document why only `dims` has a GIN index (it is the filter target) and that `metrics` filtering is not currently a query pattern. If metric filtering is later added, the GIN index should be added at that time.

---

## Cross-Phase Conflicts

### DB-003 (test compose uses postgres superuser) vs. Phase 01 BE-005 (access control)
- **Conflict type:** Security posture inconsistency across audit phases.
- **Details:** DB-003 identifies that the test compose uses the `postgres` superuser while production uses the `mkobi_app` limited-privilege role. Phase 01 finding BE-005 (validated as SPEC-DEVIATION, mandatory) flags missing dashboard access verification on global graph endpoints. If tests run with superuser (`postgres`), they bypass all privilege checks, meaning the tests validated in Phase 01 would pass even if BE-005's missing access control were exploited via permissions. Fixing DB-003 (switching tests to `mkobi_app`) BEFORE fixing BE-005 could cause previously-passing tests to fail, surfacing the access issue — this is a safe interaction. However, the reverse order (fix BE-005 first, test with superuser) means the access control fix is never properly exercised by the test suite.
- **Recommendation:** Fix DB-003 (use `mkobi_app` in tests) FIRST, then fix BE-005 (add access checks). This ensures the test suite properly validates access control.

---

## Rollout Safety Issues

### DB-001 (remove broken trigger from initial migration) — Migration integrity risk
- **Risk:** The initial migration `7130ecb0388c` is the root of the migration DAG. Modifying it after `ffd23f1f7e2b` (which depends on it) and `a2153f0f6094` (which depends on that) has been applied is dangerous. Any environment that has already run the full migration chain has already applied `ffd23f1f7e2b` which drops the broken trigger. Removing the trigger creation from `7130ecb0388c` would leave migration `ffd23f1f7e2b` doing nothing (dropping a trigger that the initial migration no longer creates), creating an idempotent no-op.
- **Safe approach:** In environments where migrations have already been applied, the broken trigger is already dropped by `ffd23f1f7e2b`. The fix should be applied as a NEW migration that:
  1. Removes the trigger creation code from the initial migration (for fresh database creation), OR
  2. Depends on the current HEAD and simply documents that the trigger is no longer created.
- **Alternative safer approach:** Leave `7130ecb0388c` untouched (it's already been applied everywhere) and leave `ffd23f1f7e2b` as the fix (it already works). Accept the minor migration history inconsistency as resolved technical debt. This is the safest path — the system works correctly today.
- **Recommendation:** The safest rollout is to do nothing beyond what `ffd23f1f7e2b` already achieved. The trigger is already dropped. Modifying already-applied root migrations risks breaking environments that have already migrated past that point. Reclassify DB-001 as resolved-with-acceptable-debt rather than modifying migration history.

### DB-002 (GIN index) — No rollout risk
- If the DOC-UPDATE reclassification is followed (document current design instead of adding an index), there is zero rollout risk — it is a documentation-only change.

### DB-003 (test user role) — Low risk, isolated
- Changing `DATABASE__USER` from `postgres` to `mkobi_app` in `docker-compose.test.yml` is a single-line change in a single file. Risk: tests that inadvertently depend on superuser privileges (e.g., DDL operations, bypassing RLS) will fail. This is a feature, not a bug — it surfaces hidden assumptions.
- **Recommendation:** Apply the change and run the full test suite. Any test failures indicate tests that are testing with inappropriate privileges.

---

## Validated Counts

| Category | Count |
|----------|-------|
| **Total findings** | 5 |
| **Rejected** | 1 (DB-004) |
| **Merged** | 1 pair (DB-005 into DB-001) |
| **Reclassified** | 1 (DB-002: BEST-PRACTICE → DOC-UPDATE) |
| **Validated as-is** | 2 (DB-001 as merged anchor, DB-003) |
| **Mandatory fixes (post-validation)** | 2 (DB-001, DB-003) |
| **Advisory recommendations (post-validation)** | 1 (DB-002 as DOC-UPDATE) |

### Mandatory fixes
- **DB-001:** Broken Trigger in Initial Migration for Non-Existent Column — SPEC-DEVIATION
  - The `update_graphs_updated_at` trigger created in the initial migration references a nonexistent `updated_at` column on the `graphs` table. Already mitigated by repair migration `ffd23f1f7e2b` which drops the trigger. Safest fix: leave migrations as-is (already resolved). For clean history, optionally add a new idempotent migration rather than modifying already-applied root migration.
  - Absorbs DB-005 (repair migration concern) via merge.
- **DB-003:** Inconsistent Database Role Usage in Test Configuration — SPEC-DEVIATION
  - `docker-compose.test.yml:90-91` uses `postgres` superuser for `test-app` service while production `docker-compose.yml:84` uses limited-privilege `mkobi_app` role. Fix: change to `mkobi_app` with matching `MKOBI_APP_PASSWORD` env var. Cross-phase note: apply BEFORE BE-005 fix from Phase 01.

### Advisory recommendations
- **DB-002:** Missing GIN Index on `aggregated_data.metrics` Column — DOC-UPDATE (reclassified)
  - Update `docs/09-database/indexes.md` to document that only `dims` has a GIN index because it is the sole JSONB filter target. `metrics` is stored but not queried via WHERE clauses, so no index is warranted. If metric filtering is added later, a GIN index should be added at that time.
