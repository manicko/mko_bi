# PostgreSQL Database Audit Report — mkobi BI Dashboard

**Audit Date:** 2026-05-19
**Report Number:** 03
**Database Version:** PostgreSQL 16.13
**Audit Scope:** Schema architecture, drift detection, migration integrity, scalability, maintainability, operational safety

---

## 1. Database Inventory (Verified)

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|
| `bidb` | dev/prod | Main application database | `DATABASE_URL` (built from `DATABASE__*` env vars) | Docker volume / manual |
| `bidb_test` | test | Isolated test database | `TEST_DATABASE_URL` (built from `DATABASE__*` + `test_dbname`) | Auto-recreated via `DatabaseStarter.recreate_test_database()` |
| `postgres` | — | Default admin database | — | PostgreSQL default |

### DSN Construction (verified from `src/mkobi/config.py`):
- Main: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}` → `bidb`
- Test: Same pattern but `path={test_dbname}` → `bidb_test`

---

## 2. Schema Documentation — Verified Structure

### Tables Summary (10 tables + alembic_version)

| Table | PK Type | FK Count | JSONB Columns | Special Features |
|---|---|---|---|---|
| `users` | UUID | 1 (registration_requests.reviewed_by) | 0 | ENUM role, TIMESTAMPTZ |
| `layouts` | UUID | 1 (dashboards.layout_id) | 1 | Updated_at trigger |
| `dashboards` | UUID | 3 (graphs, aggregated_data, etc.) | 1 | Updated_at trigger, CASCADE to children |
| `graphs` | UUID | 2 (aggregated_data) | 3 | **BUG: trigger exists but no updated_at column** |
| `filters` | UUID | 1 (dashboard_filters) | 1 | Many-to-many junction |
| `dashboard_access` | Composite | 0 | 0 | Composite PK, **Missing server_default** |
| `dashboard_filters` | Composite | 0 | 0 | Junction table |
| `processing_configs` | UUID (PK) | 0 | 1 | Updated_at trigger |
| `aggregated_data` | BIGSERIAL | 0 | 2 | GIN index on dims, unique constraint |
| `processing_logs` | UUID | 1 | 0 | ENUM status, SET NULL on delete |
| `registration_requests` | UUID | 1 | 0 | INET type, ENUM status |

---

## 3. Schema Drift Verification — Confirmed Issues

### Critical Bug: `graphs.updated_at` trigger
- **Status:** ✅ Confirmed - trigger exists in DB but `updated_at` column does NOT exist
- **Impact:** First UPDATE on graphs table will crash with `column "updated_at" does not exist`
- **Location:** Trigger `update_graphs_updated_at` on `graphs` table
- **Fix Required:** `DROP TRIGGER IF EXISTS update_graphs_updated_at ON graphs;`

### High Priority: `dashboard_access.permission` default drift
- **ORM:** `server_default=text("'view'")` 
- **Migration:** No DEFAULT clause
- **Real DB:** `column_default = NULL`
- **Impact:** Raw SQL INSERTs without permission will fail

### Medium Priority: `create_db.sql` divergence
- **Status:** ✅ Confirmed - 6+ places diverge from actual schema
- **Recommendation:** Delete or regenerate from pg_dump

---

## 4. Migration Audit — Verified

| Check | Status | Notes |
|---|---|---|
| Single migration file | ✅ PASS | Only one migration: `7130ecb0388c` |
| Idempotent ENUM creation | ✅ PASS | Uses `checkfirst=True` |
| Idempotent table creation | ✅ PASS | Uses `CREATE TABLE IF NOT EXISTS` |
| Reproducibility from scratch | ⚠️ ISSUE | Requires fixing `graphs` trigger |

---

## 5. Environment Isolation — Verified

| Environment | Database | Isolation Status | Verification |
|---|---|---|---|
| Development | `bidb` | ✅ Isolated | `DATABASE__DBNAME=bidb` |
| Test | `bidb_test` | ✅ Physically separate | NULLPool, SAVEPOINT rollback |
| Production | `bidb` | ⚠️ Same DB name as dev | Relies on Docker separation |

### Test Isolation Features:
- Separate physical database ✅
- NullPool for test engine ✅
- SAVEPOINT rollback per test ✅
- Migration applied to test DB after recreation ✅

**Verdict: SAFE** (with documented caveats)

---

## 6. Architectural Problems — Updated Severity

| Severity | Category | Object | Current Problem | Required Change |
|---|---|---|---|---|
| **CRITICAL** | Schema Design | `graphs` table | Trigger on non-existent column | `DROP TRIGGER update_graphs_updated_at ON graphs` |
| **HIGH** | Schema Drift | `dashboard_access.permission` | ORM default not in DB | Add DB default or remove ORM default |
| **HIGH** | Reproducibility | `create_db.sql` | Diverges from actual schema | Delete or regenerate |
| **MEDIUM** | Maintainability | `updated_at` | Trigger + onupdate redundancy | Choose one mechanism |
| **MEDIUM** | Security | `postgres` role | Superuser for app operations | Create limited-privilege role |

---

## 7. Scalability Risks — Verified

| Table | Risk | Current Size Factor | Recommendation |
|---|---|---|---|
| `aggregated_data` | Unbounded growth | High (upload × graphs × dims) | Retention policy, partitioning |
| `processing_logs` | Unbounded growth | Medium | Wire up `cleanup_old_logs()` |
| Connection pool | 20 max connections | Default config | Monitor under load |

---

## 8. Technical Debt — Updated

| Item | Priority | Action Required |
|---|---|---|
| `graphs` trigger bug | CRITICAL | Fix immediately |
| `create_db.sql` drift | HIGH | Delete or regenerate |
| `dashboard_access.permission` drift | HIGH | Align ORM/DB |
| Redundant `updated_at` | MEDIUM | Choose trigger OR onupdate |
| Superuser for app | MEDIUM | Create app role |
| `cleanup_old_logs()` not called | MEDIUM | Wire to lifecycle |

---

## 9. Additional Findings — New in Report 03

### 9.1. `bidb_schema.sql` Encoding Issue
- **Issue:** File has UTF-16 BOM and binary prefix (`\restrict...`)
- **Impact:** Cannot be parsed as valid SQL
- **Recommendation:** Remove or regenerate with `pg_dump --schema-only --no-owner`

### 9.2. Single Migration File Consideration
- **Current:** All schema in one migration `7130ecb0388c`
- **Trade-off:** 
  - ✅ Simple, no chain issues
  - ⚠️ Hard to track incremental changes
- **Recommendation:** Keep as-is for current stage; split when schema grows

### 9.3. GIN Index on `aggregated_data.dims`
- **Current:** `idx_aggregated_data_dims_gin` 
- **Consideration:** JSONB GIN indexes can become expensive with writes
- **Monitoring:** Track index size vs table size ratio

---

## 10. Summary

### What Works Well
1. Clean single-migration architecture with idempotent operations
2. Proper ENUM usage with `StrEnum` backing
3. TIMESTAMPTZ everywhere (correct for time zones)
4. JSONB for flexible columns
5. Test isolation with separate database and SAVEPOINT rollback
6. Async throughout with `asyncpg`
7. Consistent UUID PKs (BIGSERIAL only for `aggregated_data`)

### Immediate Actions Required
1. **CRITICAL:** Drop `update_graphs_updated_at` trigger from `graphs` table
2. **HIGH:** Align `dashboard_access.permission` default between ORM and DB
3. **HIGH:** Delete or regenerate `create_db.sql`

---

*Audit completed. This report (#03) supplements audit_report_02.md with additional verification and updated findings based on code inspection.*