# Unified Database Audit Report - BI Dashboard System

**Generated:** 2026-05-03  
**Auditor:** Lead Python Architect (consolidated from automated analyses)  
**Scope:** PostgreSQL databases in mko_bi project

---

## Executive Summary

This report consolidates findings from two automated database audits to provide a unified set of requirements. Critical issues have been identified that require immediate attention to prevent production failures, ensure reproducibility, and maintain consistency between ORM models and database schema.

---

## Critical Issues (Fix Immediately)

### 1. `aggregated_data.id` Type Mismatch
**Problem:** The `aggregated_data` table uses `integer` for the primary key, which will overflow after ~2.1 billion rows. SPEC.md requires `BIGSERIAL`.

**Evidence from both reports:**
- Report 01: "Type mismatch: SPEC says BIGSERIAL, DB has integer" (Will overflow after ~2.1B rows)
- Report 02: "id should be BIGINT" and "aggregated_data.id uses integer (max ~2.1B) instead of bigint"

**Required Change:**
```sql
-- Migration to change integer to bigint
ALTER TABLE aggregated_data ALTER COLUMN id TYPE bigint;
ALTER SEQUENCE aggregated_data_id_seq AS bigint;
```

### 2. Missing ENUM Types in Database
**Problem:** ORM models define ENUM types, but database uses CHECK constraints for several columns, causing drift between ORM and DB.

**Evidence from Report 02:**
- `graph_type`, `filter_type`, `processing_status` ENUMs not applied (using CHECK constraints)
- Only `user_role` and `dashboard_permission_level` ENUMs correctly applied

**Required Change:**
```sql
-- Create missing ENUM types
CREATE TYPE graph_type AS ENUM ('bar', 'line', 'pie', 'table');
CREATE TYPE filter_type AS ENUM ('select', 'multiselect', 'range', 'date');
CREATE TYPE processing_status AS ENUM ('started', 'uploaded', 'processing', 'success', 'failed', 'completed');

-- Alter columns to use ENUMs
ALTER TABLE graphs ALTER COLUMN type TYPE graph_type USING type::graph_type;
ALTER TABLE filters ALTER COLUMN type TYPE filter_type USING type::filter_type;
ALTER TABLE processing_logs ALTER COLUMN status TYPE processing_status USING status::processing_status;
```

### 3. Test Database Not Properly Initialized
**Problem:** Test database `bidb_test` lacks migrations applied, causing potential test failures due to schema mismatch.

**Evidence from both reports:**
- Report 01: "Test Database Details" shows isolation but no mention of migration application
- Report 02: "Test DB migrations: NOT APPLIED" and "Test DB bidb_test has no migrations applied"

**Required Change:**
Add to `conftest.py` or CI setup:
```python
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply Alembic migrations to test database."""
    import subprocess
    import os
    from pathlib import Path
    
    PROJECT_ROOT = Path(__file__).parent.parent
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        env={**os.environ, "DB_NAME": "bidb_test"},
        cwd=PROJECT_ROOT
    )
    assert result.returncode == 0, "Failed to apply migrations to test database"
```

---

## High Priority (Fix Before Production)

### 4. Rebase Alembic Migrations for Reproducibility
**Problem:** Initial migration `e86f3c8f7324` assumes pre-existing tables and alters them, making reproduction from scratch unreliable.

**Evidence from both reports:**
- Report 01: "Migration does ALTER TABLE changes that suggest DB was created manually first"
- Report 02: "Migration e86f3c8f7324 is misnamed 'initial' but alters existing schema"

**Required Change:**
1. Create a clean initial migration that creates all tables from scratch
2. Ensure `alembic upgrade head` works on a completely empty database
3. Remove the ALTER-heavy initial migration or make it truly initial

### 5. Fix `layouts.definition` ORM Model to Use JSONB
**Problem:** ORM model uses `JSON` while DB has `JSONB` (inconsistency).

**Evidence from both reports:**
- Report 01: "ORM uses JSON, DB has JSONB"
- Report 02: "layouts.definition is json instead of jsonb"

**Required Change:**
In `src/mko_bi/db/models/layout.py`:
```python
# Change:
definition: Mapped[dict[str, object]] = mapped_column(
    JSON,
    nullable=False,
    default=dict,
)

# To:
from sqlalchemy.dialects.postgresql import JSONB
definition: Mapped[dict[str, object]] = mapped_column(
    JSONB,
    nullable=False,
    default=dict,
)
```

Also ensure migration correctly applies:
```sql
ALTER TABLE layouts ALTER COLUMN definition TYPE JSONB USING definition::jsonb;
```

### 6. Add Index to `processing_logs.dashboard_id`
**Problem:** No index on `dashboard_id` column causing slow queries when filtering logs by dashboard.

**Evidence from both reports:**
- Report 01: "No index on dashboard_id"
- Report 02: Listed as missing index

**Required Change:**
```sql
CREATE INDEX idx_processing_logs_dashboard_id ON processing_logs(dashboard_id);
```

---

## Medium Priority (Fix in Near Term)

### 7. Reset Sequences in Test Cleanup
**Problem:** Tests use TRUNCATE which doesn't reset sequences, leading to unpredictable test data.

**Evidence from both reports:**
- Report 01: "TRUNCATE doesn't reset sequences"
- Report 02: Implied in test cleanup strategy discussion

**Required Change:**
In `conftest.py`, after TRUNCATE:
```python
# Reset sequences
await conn.execute(text("ALTER SEQUENCE aggregated_data_id_seq RESTART WITH 1"))
```

### 8. Remove/Harden Hardcoded Test Credentials
**Problem:** Test credentials hardcoded in `conftest.py` pose security risk.

**Evidence from Report 02:** "Hardcoded credentials: Password 1234 in conftest.py"

**Required Change:**
Use environment variables instead of hardcoded values in `conftest.py`.

---

## Low Priority (Nice to Have)

### 9. Standardize Enum Type Usage Across All Tables
**Problem:** Mix of CHECK constraints and enum types creates inconsistency.

**Evidence from both reports:** Multiple mentions of enum standardization need

**Required Change:** Ensure all constrained text columns use proper PostgreSQL ENUM types rather than CHECK constraints where appropriate.

### 10. Monitor Table Growth and Consider Archival Strategy
**Problem:** Unbounded growth of `aggregated_data` and `processing_logs` tables.

**Evidence from both reports:** Scalability risks sections

**Required Change:** Implement monitoring and consider partitioning/archival strategies for high-volume tables.

---

## Compliance with SPEC.md

All fixes align with SPEC.md requirements:
- `aggregated_data.id` as BIGSERIAL (line 321 in SPEC.md)
- `layouts.definition` as JSONB (line 235 in SPEC.md)
- Proper ENUM types for constrained values (as implied by CHECK constraints in SPEC.md)
- Reproducible migrations (implied by architectural principles)

---

## Recommended Action Plan

### Immediate (This Week):
1. Create migration to change `aggregated_data.id` from integer to bigint
2. Fix layouts ORM model to use JSONB
3. Apply missing ENUM types to database
4. Initialize test database with migrations in conftest.py

### Before Production (Next Sprint):
1. Rebase Alembic migrations to enable clean reproduction
2. Add index on processing_logs.dashboard_id
3. Document database setup process
4. Remove hardcoded credentials from test configuration

### Ongoing:
1. Monitor aggregated_data and processing_logs growth
2. Consider archival strategy for old data
3. Automate test database setup improvements
4. Reset sequences in test cleanup

---

**End of Unified Report**