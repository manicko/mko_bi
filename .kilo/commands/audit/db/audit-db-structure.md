---
name: audit-db-structure
description: audit-db-structure
agent: auditor
alwaysApply: false
---

# Task: PostgreSQL Database Audit (mkobi BI Dashboard)

> **Prerequisite:** Docker services (especially `db`) must be running. See: `docs/11-guides/docker.md`

## Objective

Based on analysis of existing code, migrations, configuration, and real PostgreSQL databases:

1. **List all required PostgreSQL databases** used by the system.
2. For each database — **extract and document the complete structure**.
3. Identify architectural problems, schema drift, scalability risks, maintainability issues.
4. Provide recommendations:
   - what must be fixed
   - what should be simplified
   - what should be standardized
   - what should be prepared for system growth
   - what docs should be updated when code has evolved beyond them

**Important:**
- Do NOT describe application business logic
- Do NOT analyze UI/API behavior
- Focus ONLY on database architecture, schema lifecycle, and reproducibility
- Schema may diverge from code since the application is still in development
- When schema diverges from docs, recommend updating docs OR fixing schema — whichever is more maintainable

## Recommendation Types

Label every finding:
- `[SPEC-DEVIATION]` — schema differs from docs. Decide: fix schema or update docs.
- `[BEST-PRACTICE]` — improvement beyond current spec. Advisory, not mandatory.
- `[DOC-UPDATE]` — docs should reflect current schema reality.

## Research

Use `websearch` to verify current best practices for:
- PostgreSQL JSONB indexing and query patterns
- Alembic migration strategies for zero-downtime deployments
- PostgreSQL ENUM type management
- asyncpg connection pooling and performance

---

# 2. Execution Stages

---

# 2.1. Code & Environment Audit — File Scanning

Scan the repository and environments (dev/stage/prod).

---

## 2.1.1. Database Inventory

Search in:

- `.env`
- `docker-compose.yml`
- `docker-compose.override.yml`
- `docker-compose.test.yml`
- k8s secrets
- CI/CD configurations
- `config.py` / `settings.py`
- `init_db.sh` / `create_dbs.sql`
- `conftest.py` and pytest fixtures

Check for:

- `DATABASE_URL`
- `TEST_DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- Additional PostgreSQL DSNs

### Result

| Logical Name | DSN Variable | Environment | Purpose | Creation Method |
|---|---|---|---|---|
| bidb | DATABASE_URL | dev/prod | Main application database | Docker / manual |
| bidb_test | TEST_DATABASE_URL | test | Test database (isolated) | Auto-recreated on startup |

---

## 2.1.2. Table Schema, Relationships, Indexes per Database

Sources:

- `alembic/versions/*.py`
- SQLAlchemy models (`src/mkobi/db/models/`)
- Raw SQL migrations
- Init scripts
- Fixtures
- Interactive PostgreSQL audit

For each table document:

- schema/table name
- columns/types
- constraints
- indexes
- FK
- triggers
- sequences
- extensions
- comments

### Special Attention

Verify:

- UUID consistency (all entity tables use UUID PK except `aggregated_data` which uses BIGSERIAL)
- JSONB usage (vs JSON/TEXT)
- Timezone-aware timestamps (TIMESTAMPTZ, not TIMESTAMP)
- Nullable correctness
- Async-compatible types/drivers (asyncpg)

### Result

Markdown document with complete DB schema.

---

## 2.1.2.1. Schema Drift Detection (ORM vs Alembic vs Real DB)

Verify consistency between:

- ORM (SQLAlchemy models in `src/mkobi/db/models/`)
- Alembic migrations (`alembic/versions/`)
- Real PostgreSQL schema

Detect:

- Missing tables
- Missing columns
- Type mismatches
- Constraint discrepancies
- Index discrepancies
- Manual DB changes
- Legacy columns/tables

### Special Attention

- UUID vs INTEGER for PKs
- JSONB vs JSON/TEXT for flexible columns
- TIMESTAMPTZ vs TIMESTAMP
- asyncpg driver usage
- `aggregated_data.id` is BIGSERIAL (not UUID — intentional design)

### Result

Schema Drift Report.

---

## 2.1.2.2. Migration Audit & Schema Reproducibility

Verify:

- Migration chain integrity
- Reproducibility from scratch
- No broken revisions
- No circular dependencies
- Ability to run `alembic upgrade head` on a completely empty database

Detect:

- Manual SQL changes outside migrations
- Non-idempotent migrations
- State-dependent migrations
- Migration drift
- Mixed schema/data migrations

### PostgreSQL ENUM Types

Verify ENUM types are created with `checkfirst=True` for idempotency:

```python
user_role_enum = ENUM('admin', 'editor', 'viewer', name='user_role')
user_role_enum.create(op.get_bind(), checkfirst=True)
```

Expected ENUM types:

| PostgreSQL ENUM | Values | StrEnum Class |
|---|---|---|
| `user_role` | admin, editor, viewer | `UserRole` |
| `dashboard_permission_level` | view, edit, admin | `DashboardPermission` |
| `graph_type` | bar, line, pie, table | `GraphType` |
| `filter_type` | select, multiselect, range, date | `FilterType` |
| `processing_status` | started, uploaded, processing, success, failed, completed | `ProcessingStatus` |
| `registration_status` | pending, approved, rejected | `RegistrationStatus` |

### Result

Migration Audit Report.

---

## 2.1.3. Roles & Permissions

Search in:

- SQL scripts
- Docker init scripts
- Terraform/Ansible
- PostgreSQL grants

Document:

- Roles
- Permissions
- Ownership
- Migration users
- Runtime users

### Verify

- Separation of privileges
- Least privilege principle
- No superuser usage by application

### Result

Role & Permissions Report.

---

## 2.1.4. Test Database Specifics

Verify:

- Isolation (separate `bidb_test` database)
- Recreate strategy (drop + recreate when `RECREATE_TEST_DB=true` or `ENV=test`)
- Fixtures
- Schema cleanup (SAVEPOINT rollback per test)
- Transactional tests

### Verify

- Test DB is physically separate (`bidb_test` ≠ `bidb`)
- Separate DSN (`TEST_DATABASE_URL`)
- No access to prod/dev from test
- Migrations don't affect production
- Test engine uses `NullPool` (no connection pooling issues)
- Each test runs in a SAVEPOINT that is rolled back after completion
- Test database is dropped and recreated on session setup when `RECREATE_TEST_DB=true`

### Result

Test Isolation Report:
- SAFE
- RISKY
- UNSAFE

---

# 2.2. Architectural Audit of Database Layer

## Goal

Not only describe the current structure, but also determine:

- What will break as the system grows
- What will complicate maintenance
- Where architectural bottlenecks exist
- What decisions already create technical debt

---

## 2.2.1. Maintainability Audit

Verify:

- Consistent naming conventions
- Consistent UUID strategy (UUID for entities, BIGSERIAL for aggregated_data)
- Consistent timestamp strategy (TIMESTAMPTZ everywhere)
- Consistent FK strategy (CASCADE for dependent children, SET NULL for optional refs)
- Consistent index naming (`idx_<table>_<column>`)
- Schema organization (core, access, processing tables)
- Migration organization (descriptive names, correct order)

Detect:

- Chaotic naming conventions
- Mixed ID strategies
- Inconsistent defaults
- Duplicate structures
- Hardcoded schema assumptions
- Hidden coupling between tables

---

## 2.2.2. Scalability Audit

Verify:

- Potential bottlenecks
- Heavy JSONB overuse
- Missing needed indexes
- Full table scans
- Oversized tables
- Missing archival strategy for log/event tables
- Aggregation hotspots
- Growth risks

### Pay Special Attention To

- `processing_logs` table (unbounded growth — consider archival)
- `aggregated_data` table (grows with each upload × graphs × dimension combinations)
- `registration_requests` table (grows over time)

### Detect

- Potential N+1 patterns in repository queries
- Expensive joins
- Unbounded growth tables
- Missing archival/purging strategy

---

## 2.2.3. Schema Design Quality Audit

Verify:

- Normalization
- Justified denormalization (JSONB for flexible configs)
- Constraint consistency
- Nullable correctness
- FK correctness
- Cascade behavior correctness

### Cascade Behavior Reference

| Parent | Child | On Delete |
|---|---|---|
| dashboards | graphs | CASCADE |
| dashboards | aggregated_data | CASCADE |
| dashboards | dashboard_access | CASCADE |
| dashboards | dashboard_filters | CASCADE |
| dashboards | processing_configs | CASCADE |
| dashboards | processing_logs | SET NULL |
| layouts | dashboards | SET NULL |
| users (created_by) | dashboards | SET NULL |
| users (reviewed_by) | registration_requests | SET NULL |
| graphs | aggregated_data | CASCADE |
| filters | dashboard_filters | CASCADE |
| users | dashboard_access | CASCADE |

### Detect

- Weak integrity
- Orphan risks
- Missing constraints
- Duplicated data
- Incompatible data types
- Dangerous cascade deletes

---

## 2.2.4. Operational Stability Audit

Verify:

- Reproducibility (schema recreatable from scratch via Alembic)
- Backup compatibility
- Restore compatibility
- Migration safety
- Rollback safety
- Startup safety (auto-migration works)

Detect:

- Schema states impossible to recreate
- Manual-only steps
- Hidden runtime dependencies
- Environment-dependent behavior

---

## 2.2.5. Async Compatibility Audit

For FastAPI async architecture verify:

- Async DB driver (asyncpg)
- No sync engine usage in async context
- No blocking DB access in request handlers
- Connection lifecycle management
- Pool configuration (asyncpg pool)
- Transaction handling (async SQLAlchemy sessions)

Detect:

- Sync SQLAlchemy inside async runtime
- Blocking migrations during requests
- Leaked sessions/connections

---

## 2.2.6. Future Extensibility Audit

Verify readiness for:

- New dashboards (schema supports any number)
- New aggregation types (JSONB config is flexible)
- Multi-tenant support (no tenant_id currently — assess if needed)
- Data volume growth (indexing strategy, archival)
- New environments (migration-based schema management)

### Detect

- Schema rigidity
- Hardcoded assumptions
- Tightly coupled structures
- Migration fragility
- Impossibility of safe refactoring

---

# 3. Expected Results

Create file: `C:\py_dev\mkobi\.ai\audit\db\audit_report_<number>.md` (next available number)

### 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|

---

### 2. Schema Documentation

For each database:
- tables
- types
- FK
- indexes
- triggers
- extensions
- sequences
- roles

---

### 3. Schema Drift Report

| Object | Problem | ORM | Alembic | Real DB | Recommended Source of Truth |
|---|---|---|---|---|---|

---

### 4. Migration Audit

| Check | Status | Notes |
|---|---|---|

---

### 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|---|---|---|---|

---

### 6. Architectural Problems

| Severity | Type | Area | Problem | Risk | Recommendation |
|----------|------|------|---------|------|----------------|
| HIGH | [SPEC-DEVIATION] | Indexing | aggregated_data missing composite index | full table scan | add index or update spec |
| MEDIUM | [BEST-PRACTICE] | Scaling | processing_logs unbounded growth | table bloat | add archival strategy |
| LOW | [DOC-UPDATE] | Schema | ENUM types differ from docs | confusion | update docs to match |

Type column: `[SPEC-DEVIATION]`, `[BEST-PRACTICE]`, or `[DOC-UPDATE]`.

Severity: CRITICAL, HIGH, MEDIUM, LOW

---

### 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|

---

### 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|

---

### 9. Required Architectural Improvements

Goal: simple, understandable, predictable, maintainable, extensible architecture.
NOT maximum "enterprise architecture".
NOT introducing complex patterns.
NOT abstractions for abstractions' sake.

### Recommendations must ONLY be made if they:

- Reduce error probability
- Simplify maintenance
- Reduce coupling
- Simplify system evolution
- Eliminate a real bottleneck
- Eliminate a real architectural risk
- Eliminate schema drift
- Improve reproducibility
- Make system behavior more predictable

---

### Do NOT consider as problems:

- Small number of tables
- Simple structure
- No microservices
- No CQRS
- No event sourcing
- No repository pattern (SQLAlchemy sessions used directly)
- No complex abstraction layers
- No premature partitioning/sharding
- No complex caching architecture
- No premature optimization

---

### Consider as problems ONLY if they affect:

- Maintainability
- Reproducibility
- Scalability
- Integrity
- Operational stability
- Migration safety
- Debugging complexity
- Onboarding complexity
- Test isolation
- Predictable behavior

---

### Forbidden to recommend without explicit reason:

- Partitioning
- Sharding
- Message brokers
- Distributed systems
- CQRS
- Event sourcing
- Multi-database split
- Complex abstraction layers
- Generic repositories
- Unnecessary normalization
- Premature denormalization
- Async rewrite without necessity

---

### Each recommendation must answer:

What specifically will become:
- easier to maintain
- easier to extend
- safer to change
- more stable to operate

after implementing the change.

If there is no answer — do not add the recommendation.

### Format

For each problem:

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|

Where:

- `Severity`: CRITICAL, HIGH, MEDIUM, LOW
- `Category`: Schema Design, Migrations, Indexing, Constraints, Scaling, Maintainability, Async Compatibility, Test Isolation, Environment Separation, Security, Reproducibility
- `Object`: specific table, index, migration, role, schema, env config, DB connection layer

---

### Recommendation Requirements

Each recommendation must:
- Be tied to a specific object
- Describe a real problem
- Explain: why it's a problem, when the system will degrade, what risk is created
- Contain a specific change
- Not contain abstract advice
- Include label: `[SPEC-DEVIATION]`, `[BEST-PRACTICE]`, or `[DOC-UPDATE]`

---

### Forbidden recommendation phrases:

- "improve architecture"
- "add scalability"
- "use best practices"
- "consider optimization"
- "make code cleaner"

---

### Only concrete recommendations allowed

Good example:

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| HIGH | Indexing | aggregated_data | missing composite index on (dashboard_id, graph_id) | full table scan as data grows | add composite btree index | dashboard aggregation queries will degrade after table growth |

---

### For scalability problems, specify:

- What exactly will become a bottleneck
- At what type of growth: row growth, dashboard growth, concurrent users, aggregation volume
- Which component will suffer: inserts, filtering, joins, migrations, startup, backup/restore

---

### For maintainability problems, specify:

- What complicates maintenance
- Why this creates technical debt
- What will be harder: migrations, debugging, onboarding, schema evolution, refactoring

---

### For migration problems, specify:

- Whether DB recovery from scratch is possible
- Which migrations are non-reproducible
- Which migrations depend on runtime state
- Which migrations are dangerous for production

---

### For environment/test isolation, specify:

- Whether test environment can damage dev/prod
- Whether shared DB usage exists
- Whether shared credentials exist
- Whether accidental destructive operations are possible

---

# 4. Acceptance Criteria

Audit is considered complete if:

- All PostgreSQL databases are identified and described
- Complete schema structure is restored
- Schema drift between ORM / Alembic / real DB is identified
- Schema reproducibility is verified
- Architectural problems are identified
- Scalability risks are identified
- Migration risks are documented
- Technical debt and maintainability risks are described
- Concrete improvement recommendations are provided
- Recommendations contain no unnecessary enterprise overengineering
- Conclusions are based on actual code, migrations, and DB structure
