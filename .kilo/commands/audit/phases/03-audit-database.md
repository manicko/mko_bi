---
name: 03-database
description: Database architecture audit covering migrations, indexing strategy, consistency guarantees, transactional safety, and scalability risks
agent: audit-executor
alwaysApply: false
problems-only: true
---

# Phase 03 Audit — Database Architecture

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.

---

## Discovery Stage

Before performing audit checks, discover the project's database architecture:

1. **Schema Discovery** — Identify entity tables vs transactional tables, map FK relationships and cascade behavior, discover JSONB usage patterns, identify indexes.
2. **Migration Discovery** — Locate migration tool and version tracking, identify naming conventions, discover propagation mechanism, find rollback procedures.
3. **Environment Discovery** — Identify database instances (dev, test, prod), discover connection configuration, find credentials management, identify test isolation.
4. **Performance & Growth Discovery** — Identify high-volume tables, discover archival strategy, map query patterns to index usage, identify bottlenecks.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R1 — Migration Chain Integrity

Run the migration tool's history, current, and check commands.

- `check` detects migrations that should exist but don't (model/migration drift). Any output is a finding.
- If `current` shows a revision different from history HEAD, the DB is not at the latest migration.
- Examine the migration chain for gaps or branches (multiple heads). Branches are CRITICAL.
- For each migration file: read `upgrade()` and `downgrade()`. Verify `downgrade()` is the logical inverse of `upgrade()`. Empty or incomplete `downgrade()` is a finding.

### Step R2 — Schema vs. Model Drift Detection

Compare the database schema (from the running DB or migration files) against the ORM model definitions:

- For each ORM model class, verify its columns exist in the migration-chain schema.
- For each column in the migration schema, verify it has a corresponding ORM model attribute.
- Mismatches: columns in DB but not in model (dead columns), or columns in model but not in DB (broken app behavior).
- Check ENUM types: verify they exist in the DB and match the model.

### Step R3 — Index Health Analysis

Connect to the database and query for index usage statistics.

- **Unused indexes** (never scanned): each is a finding — they slow down writes for no benefit.
- **Missing indexes**: tables with high sequential scans and no indexes on frequently filtered columns. Check against query patterns from the codebase.
- **Duplicate indexes**: identical index definitions on the same table. Each duplicate is a finding.

### Step R4 — Constraint Verification

Query for constraints that are not validated or are missing:

- Constraints with `NOT VALID` status: existing data may violate them. Finding if the constraint should apply to all data.
- Missing FK constraints: if the model has a relationship but the DB has no FK constraint, that is a data integrity risk.

### Step R5 — Transaction Boundary Verification

Read the service/repository code that performs multi-step database operations:

- For each transaction spanning multiple writes, verify it uses a single transaction context.
- Search for session commits inside loops (N+1 commit pattern). Each occurrence is a finding.
- Verify locking is used where concurrent writes could cause data loss.

### Step R6 — Test Database Isolation Check

Check how tests interact with the database:

- Read test fixtures/setup: does each test run in a transaction that gets rolled back?
- If tests truncate/delete data, verify they cannot affect dev or prod (separate DB or schema).
- Create a test database from the migration chain and verify it matches the expected schema.
- Verify the migration chain is reversible (downgrade to base, then upgrade to head).

---

## Audit Scope

Migration integrity, indexing strategy, consistency guarantees, transactional safety, scalability, test isolation.

---

## Audit Dimensions

### 1. Migration Integrity

| Check | Description |
|-------|-------------|
| Schema changes version-controlled via migrations | No manual schema changes outside the migration tool. |
| Migration chain is linear without forks | Single head, no branches. |
| Migrations are idempotent | Safe to re-run without errors. |
| Migration history matches actual schema | No drift between migrations and DB. |
| Type definitions in migrations match entity definitions | Column types are consistent. |
| ENUM types created safely | Check-first semantics, no errors on re-run. |

**Evidence required:** Step R1 output for chain integrity. Step R2 comparison for drift detection.

### 2. Indexing Strategy

| Check | Description |
|-------|-------------|
| Indexes exist for frequent query predicates | Every common filter has an index. |
| Composite indexes cover join patterns | Join columns are indexed together. |
| JSONB indexes for queried flexible fields | GIN indexes where JSONB fields are filtered. |
| Unique constraints for business keys | No duplicate business keys possible. |
| No missing indexes on large tables | Query analysis shows no full table scans. |
| No redundant or duplicate indexes | Each index serves a purpose. |
| Text search indexes where applicable | Searchable text fields are indexed. |

**Evidence required:** Step R3 output: list of indexes, unused indexes, high seq_scan tables. Read repository query patterns and match each to an index.

### 3. Consistency Guarantees

| Check | Description |
|-------|-------------|
| Foreign key constraints enforce relationships | Every ORM relationship has a DB FK. |
| Cascade/SET NULL behavior is intentional | No accidental data loss on delete. |
| Not-null constraints on required fields | No nullable columns where data is required. |
| Check constraints validate business rules | Business rules enforced at DB level. |
| No constraint drift between migrations and models | Constraints match in both places. |

**Evidence required:** Step R4 output for constraint validation status. For each FK in the model, verify it exists in the DB schema.

### 4. Transactional Safety

| Check | Description |
|-------|-------------|
| Multi-step operations use transactions | No partial writes possible. |
| Rollback on failure occurs correctly | Exception triggers rollback. |
| No partial writes on error | All-or-nothing semantics. |
| Isolation level appropriate for workload | No dirty reads or lost updates. |
| Deadlocks prevented through consistent lock ordering | Consistent access order across transactions. |
| Short transactions (no long-running locks) | No long-held locks. |

**Evidence required:** Read the actual transaction code. Verify `commit` is inside a `try` block with `rollback` on exception. If a service writes to two tables without a transaction wrapper, that is CRITICAL.

### 5. Scalability Invariants

| Check | Description |
|-------|-------------|
| Archival strategy for growing tables | Old data is purged or archived. |
| No unbounded table growth risks | Every table has a growth bound. |
| Full table scan risks identified | No unindexed queries on large tables. |
| Query patterns efficient for data volume | No O(n^2) queries. |
| Batch operations for large data sets | No row-by-row processing of large datasets. |
| Connection pooling configured appropriately | Pool size is bounded. |

**Evidence required:** Check if any table grows monotonically without delete/archival logic. For each repository method that fetches data, verify it uses pagination or is guaranteed small. Read the connection pool configuration.

### 6. Test Isolation

| Check | Description |
|-------|-------------|
| Test database physically separate from dev/prod | No shared mutable state. |
| Each test runs in isolated transaction | Transaction-per-test pattern. |
| Test transactions rolled back after completion | No test data persists. |
| No test data leakage to other environments | Separate connection strings. |
| Test database recreated from migrations | Migrations produce correct test schema. |
| No shared mutable state between tests | Tests are independent. |

**Evidence required:** Step R6: test DB creation from migrations. Read the test conftest/fixtures. Verify transaction-per-test pattern.

---

## Report Output

Write findings to: `.ai/audit/03-database/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `DB-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — migration tool output, DB query results, constraint validation status, model/schema drift.
  2. **Not just:** "violates invariant X" — show the exact migration file, SQL, or ORM model comparison.
