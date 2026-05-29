---
name: 03-database
description: Database architecture audit covering migrations, indexing strategy, consistency guarantees, transactional safety, and scalability risks
agent: audit-executor
alwaysApply: false
---

# Phase 03 Audit — Database Architecture

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's database architecture:

1. **Schema Discovery**
   - Identify entity tables vs transactional/operational tables
   - Map foreign key relationships and their cascade behavior
   - Discover JSONB/flexible schema usage patterns
   - Identify indexes and their performance purpose

2. **Migration Discovery**
   - Locate migration tool and version tracking mechanism
   - Identify migration naming/versioning convention
   - Discover how schema changes are propagated
   - Find rollback/recovery procedures

3. **Environment Discovery**
   - Identify database instances (dev, test, prod)
   - Discover connection configuration strategy
   - Find credentials/secrets management approach
   - Identify isolation mechanisms for testing

4. **Performance & Growth Discovery**
   - Identify high-volume tables ("big tables")
   - Discover data archival/purge strategy
   - Map query patterns to table/index usage
   - Identify potential bottlenecks

---

## Audit Dimensions

### 1. Migration Integrity

Verify schema evolution is controlled and reproducible:

| Check | Status | Evidence |
|-------|--------|----------|
| Schema changes version-controlled via migrations | | |
| Migration chain is linear without forks | | |
| Migrations are idempotent (safe to re-run) | | |
| Migration history matches actual schema | | |
| No manual schema changes outside migrations | | |
| Type definitions in migrations match entity definitions | | |
| ENUM types created safely (check-first semantics) | | |

---

### 2. Indexing Strategy

Verify performance optimization and query efficiency:

| Check | Status | Evidence |
|-------|--------|----------|
| Indexes exist for frequent query predicates | | |
| Composite indexes cover join patterns | | |
| JSONB indexes for queried flexible fields | | |
| Unique constraints for business keys | | |
| No missing indexes on large tables (query analysis) | | |
| No redundant or duplicate indexes | | |
| Text search indexes where applicable | | |

---

### 3. Consistency Guarantees

Verify data integrity is protected:

| Check | Status | Evidence |
|-------|--------|----------|
| Foreign key constraints enforce relationships | | |
| Cascade/SET NULL behavior is intentional | | |
| Not-null constraints on required fields | | |
| No null values where data is required | | |
| Check constraints validate business rules | | |
| No constraint drift between migrations and models | | |

---

### 4. Transactional Safety

Verify ACID properties are maintained:

| Check | Status | Evidence |
|-------|--------|----------|
| Multi-step operations use transactions | | |
| Rollback on failure occurs correctly | | |
| No partial writes on error | | |
| Isolation level appropriate for workload | | |
| Deadlocks prevented through consistent lock ordering | | |
| Short transactions (no long-running locks) | | |

---

### 5. Scalability Invariants

Verify database can grow without degradation:

| Check | Status | Evidence |
|-------|--------|----------|
| Archival strategy for growing tables | | |
| No unbounded table growth risks | | |
| Full table scan risks identified | | |
| Query patterns efficient for data volume | | |
| Batch operations for large data sets | | |
| Connection pooling configured appropriately | | |

---

### 6. Test Isolation

Verify test environment safety:

| Check | Status | Evidence |
|-------|--------|----------|
| Test database physically separate from dev/prod | | |
| Each test runs in isolated transaction | | |
| Test transactions rolled back after completion | | |
| No test data leakage to other environments | | |
| Test database recreated from migrations | | |
| No shared mutable state between tests | | |

---

## Report Output

Write findings to: `.ai/audit/03-database/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `DB-` for finding IDs.