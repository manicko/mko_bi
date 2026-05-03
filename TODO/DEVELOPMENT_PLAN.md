# Sequential Development Plan for Database Improvements

**Based on:** DATABASES_AUDIT_REPORT_03.md  
**Goal:** Each step accounts for previous development to ensure consistency and avoid rework

## Phase 1: Migration Foundation (Weeks 1-2)
*Establish reliable migration system as foundation for all other changes*

### Step 1.1: Create True Initial Migration
**Dependency:** None (starting point)
**Rationale:** Must establish reproducible baseline before making schema changes
**Action:** 
- Create new migration that creates all tables from scratch matching current SPEC.md
- Ensure migration works on completely empty database
- Update migration chain to depend on this new initial migration

### Step 1.2: Fix aggregated_data.id Type
**Dependency:** Step 1.1 (reliable migrations)
**Rationale:** Critical overflow issue; requires migration which now works reliably
**Action:**
- Create migration to change aggregated_data.id from integer to bigint
- Update sequence type to bigint
- Verify migration applies cleanly on empty DB via Step 1.1

### Step 1.3: Fix layouts.definition ORM and DB Type
**Dependency:** Step 1.1 (reliable migrations)
**Rationale:** ORM-DB inconsistency; requires migration which now works reliably
**Action:**
- Update ORM model to use JSONB instead of JSON
- Create migration to alter layouts.definition column to JSONB
- Verify migration applies cleanly on empty DB via Step 1.1

## Phase 2: Schema Consistency (Weeks 2-3)
*Apply remaining schema improvements using reliable migration foundation*

### Step 2.1: Apply Missing ENUM Types
**Dependency:** Step 1.1 (reliable migrations)
**Rationale:** ORM-DB drift; requires migrations which now work reliably
**Action:**
- Create migration to create missing ENUM types (graph_type, filter_type, processing_status)
- Alter columns to use ENUM types with USING clauses
- Verify migration applies cleanly on empty DB via Step 1.1

### Step 2.2: Add processing_logs.dashboard_id Index
**Dependency:** Step 1.1 (reliable migrations)
**Rationale:** Performance improvement; requires migration which now works reliably
**Action:**
- Create migration to add index on processing_logs(dashboard_id)
- Verify migration applies cleanly on empty DB via Step 1.1

## Phase 3: Test Environment Stability (Weeks 3-4)
*Ensure reliable testing with proper isolation and cleanup*

### Step 3.1: Initialize Test Database with Migrations
**Dependency:** Step 1.1 (reliable migrations)
**Rationale:** Tests must run against correct schema; depends on reliable migrations
**Action:**
- Add pytest fixture to apply migrations to bidb_test before test session
- Verify test database starts with clean schema matching development

### Step 3.2: Implement Test Sequence Reset
**Dependency:** Step 3.1 (test DB initialization)
**Rationale:** Prevents unpredictable test data; builds on initialized test DB
**Action:**
- Modify conftest.py to reset sequences after TRUNCATE
- Specifically reset aggregated_data_id_seq and any other sequences
- Verify test data predictability

### Step 3.3: Remove Hardcoded Test Credentials
**Dependency:** Step 3.1 (test DB initialization)
**Rationale:** Security improvement; uses environment instead of hardcoded values
**Action:**
- Replace hardcoded credentials in conftest.py with environment variables
- Update documentation for test environment setup
- Verify tests pass with environment-based configuration

## Phase 4: Verification and Documentation (Week 4)
*Final validation and knowledge transfer*

### Step 4.1: End-to-End Validation
**Dependency:** All previous steps
**Rationale:** Ensure all changes work together in real workflow
**Action:**
- Run full migration cycle on empty database
- Execute test suite against initialized test database
- Verify application startup and basic functionality

### Step 4.2: Update Documentation
**Dependency:** All previous steps
**Rationale:** Maintain accurate records of changes made
**Action:**
- Update README with database setup instructions
- Document migration workflow for new developers
- Create runbook for database maintenance procedures

## Risk Mitigation Notes:
- Each migration step includes verification on empty database
- Test environment improvements depend on reliable migration foundation
- Schema changes are grouped to minimize migration count
- Critical fixes (aggregated_data.id) addressed early in reliable migration context