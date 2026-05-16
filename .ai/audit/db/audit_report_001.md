# PostgreSQL Database Audit Report

**Project:** mkobi BI Dashboard  
**Audit Date:** 2026-05-16  
**Auditor:** Architecture Audit Team

---

## 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|----------|-------------|---------|--------------|-------------------|
| `bidb` | Production/Development | Primary Application DB | `DATABASE_URL` (from `DATABASE__HOST`, `DATABASE__PORT`, `DATABASE__DBNAME`) | Docker volume (`postgres_data`) |
| `bidb_test` | Test | Test Database | `TEST_DATABASE_URL` (from `DATABASE__TEST_DBNAME`) | Recreated fresh per test run |

### Connection Details

**Primary Database (`bidb`):**
- Host: `localhost` / `db` (Docker)
- Port: `5432`
- Database: `bidb`
- User: `postgres`
- Driver: `postgresql+asyncpg://`

**Test Database (`bidb_test`):**
- Host: `localhost` / `db` (Docker)
- Port: `5432`
- Database: `bidb_test`
- User: `postgres`
- Driver: `postgresql+asyncpg://`

---

## 2. Schema Documentation

### 2.1 Tables Structure

#### users
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `email` | VARCHAR(255) | NO | - | UNIQUE, CHECK (length <= 255) |
| `password_hash` | VARCHAR(255) | NO | - | - |
| `role` | `user_role` | NO | `'viewer'` | - |
| `is_active` | BOOLEAN | NO | `true` | - |
| `created_at` | TIMESTAMPTZ | NO | `now()` | - |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | - |

**Indexes:**
- `idx_users_email` (UNIQUE) - on `email`
- `idx_users_role` - on `role`

---

#### dashboards
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `name` | VARCHAR(255) | NO | - | UNIQUE |
| `description` | TEXT | YES | - | - |
| `config` | JSONB | YES | - | - |
| `layout_id` | UUID | YES | - | FK → layouts.id ON DELETE SET NULL |
| `created_by` | UUID | YES | - | FK → users.id ON DELETE SET NULL |
| `created_at` | TIMESTAMPTZ | NO | `now()` | - |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | - |

**Indexes:**
- `idx_dashboards_name` (UNIQUE) - on `name`

---

#### graphs
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `dashboard_id` | UUID | NO | - | FK → dashboards.id ON DELETE CASCADE |
| `name` | VARCHAR(255) | NO | - | - |
| `type` | `graph_type` | NO | - | - |
| `config` | JSONB | NO | `{}` | - |
| `dimensions` | JSONB | NO | `[]` | - |
| `metrics` | JSONB | NO | `[]` | - |
| `created_at` | TIMESTAMPTZ | NO | `now()` | - |

**Indexes:**
- `idx_graphs_dashboard_name` (UNIQUE) - on `(dashboard_id, name)`
- `idx_graphs_dashboard` - on `dashboard_id`

---

#### layouts
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `name` | VARCHAR(255) | NO | - | UNIQUE |
| `definition` | JSONB | NO | `{}` | - |
| `created_at` | TIMESTAMPTZ | NO | `now()` | - |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | - |

**Indexes:**
- `idx_layouts_name` (UNIQUE) - on `name`

---

#### filters
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `name` | VARCHAR(255) | NO | - | UNIQUE |
| `type` | `filter_type` | NO | - | - |
| `config` | JSONB | NO | `{}` | - |
| `created_at` | TIMESTAMPTZ | NO | `now()` | - |

**Indexes:**
- `idx_filters_name` (UNIQUE) - on `name`

---

#### dashboard_access
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `user_id` | UUID | NO | - | FK → users.id ON DELETE CASCADE |
| `dashboard_id` | UUID | NO | - | FK → dashboards.id ON DELETE CASCADE |
| `permission` | `dashboard_permission_level` | NO | `'view'` | - |

**Primary Key:** `(user_id, dashboard_id)`

**Indexes:**
- `idx_dashboard_access_user` - on `user_id`
- `idx_dashboard_access_dashboard` - on `dashboard_id`

---

#### dashboard_filters (junction table)
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `dashboard_id` | UUID | NO | - | FK → dashboards.id ON DELETE CASCADE |
| `filter_id` | UUID | NO | - | FK → filters.id ON DELETE CASCADE |

**Primary Key:** `(dashboard_id, filter_id)`

---

#### processing_configs
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `dashboard_id` | UUID | NO | - | PK + FK → dashboards.id ON DELETE CASCADE |
| `settings` | JSONB | NO | `{}` | - |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | - |

---

#### aggregated_data
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | BIGINT | NO | `nextval('aggregated_data_id_seq'::regclass)` | PK (BIGSERIAL) |
| `dashboard_id` | UUID | NO | - | FK → dashboards.id ON DELETE CASCADE |
| `graph_id` | UUID | NO | - | FK → graphs.id ON DELETE CASCADE |
| `dims` | JSONB | NO | `{}` | - |
| `metrics` | JSONB | NO | `{}` | - |

**Indexes:**
- `idx_aggregated_data_graph_id` - on `graph_id`
- `idx_aggregated_data_dashboard_id` - on `dashboard_id`
- `idx_aggregated_data_dashboard_graph` - on `(dashboard_id, graph_id)`
- `idx_aggregated_data_dims_gin` - GIN index on `dims`
- `uq_aggregated_data_dashboard_graph_dims` (UNIQUE) - on `(dashboard_id, graph_id, dims::text)`

---

#### processing_logs
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `dashboard_id` | UUID | YES | - | FK → dashboards.id ON DELETE SET NULL |
| `status` | `processing_status` | NO | - | - |
| `message` | VARCHAR(1000) | YES | - | - |
| `started_at` | TIMESTAMPTZ | YES | - | - |
| `finished_at` | TIMESTAMPTZ | YES | - | - |

**Indexes:**
- `idx_processing_logs_dashboard_id` - on `dashboard_id`

---

#### registration_requests
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | PRIMARY KEY |
| `email` | VARCHAR(255) | NO | - | UNIQUE |
| `status` | `registration_status` | NO | `'pending'` | - |
| `requested_by_ip` | INET | YES | - | - |
| `reviewed_by` | UUID | YES | - | FK → users.id ON DELETE SET NULL |
| `reviewed_at` | TIMESTAMPTZ | YES | - | - |
| `created_at` | TIMESTAMPTZ | NO | `now()` | - |

---

### 2.2 Enum Types

| Enum Name | Values |
|-----------|--------|
| `user_role` | `'admin'`, `'editor'`, `'viewer'` |
| `dashboard_permission_level` | `'view'`, `'edit'`, `'admin'` |
| `graph_type` | `'bar'`, `'line'`, `'pie'`, `'table'` |
| `filter_type` | `'select'`, `'multiselect'`, `'range'`, `'date'` |
| `processing_status` | `'started'`, `'uploaded'`, `'processing'`, `'success'`, `'failed'`, `'completed'` |
| `registration_status` | `'pending'`, `'approved'`, `'rejected'` |

---

### 2.3 Extensions

**Required Extension:**
- `pgcrypto` (for `gen_random_uuid()` function)

---

### 2.4 Triggers

The following triggers are created by migration `ce58bba5d461`:
- `update_users_updated_at` - updates `updated_at` on `users` table
- `update_dashboards_updated_at` - updates `updated_at` on `dashboards` table
- `update_processing_configs_updated_at` - updates `updated_at` on `processing_configs` table
- `update_layouts_updated_at` - updates `updated_at` on `layouts` table
- `update_graphs_updated_at` - updates `updated_at` on `graphs` table

---

## 3. Schema Drift Report

| Object | Problem | ORM | Alembic | Real DB | Recommended Source of Truth |
|--------|---------|-----|---------|---------|---------------------------|
| `updated_at` column on `users` | Column added via migration after initial table creation | Present in model | Added in `20260507141843` | After migration | ORM + Alembic (consistent after upgrade) |
| `config` column on `dashboards` | Dropped and re-added multiple times (migrations `a1b2c3d4e5f6`, `a1e404502aac`, `c3cc391beded`) | Present in model | Exists | After migration | ORM (model defines it) |
| `updated_at` column on `layouts` | Added via migration | Present in model | Added in `20260508145000` | After migration | ORM + Alembic (consistent after upgrade) |
| `idx_dashboard_filters_dashboard_filter` | Dropped in `ce58bba5d461` (Task-DB-006), recreated in `c3cc391beded` | N/A | Inconsistent | Depends on migration path | Alembic (should be dropped - redundant with PK) |
| Trigger function `update_updated_at_column()` | Created in migration, not in ORM | N/A | Raw SQL | Only after migration | Alembic (keep as is) |
| GIN index on `aggregated_data.dims` | Expression index pattern correct | N/A | Raw SQL with `postgresql_using` | After migration | Alembic (correct) |
| Index naming inconsistency | Multiple migrations renaming same indexes | Uses `idx_` prefix in models | Mixed `idx_` and `ix_` prefixes | After migration | Standardize to `idx_` prefix |

**Summary:** Schema drift is primarily around:
1. Index naming inconsistencies caused by multiple migrations renaming the same indexes
2. The `config` column was dropped and re-added, creating a potential gap
3. Redundant index on `dashboard_filters` was dropped then recreated inconsistently

---

## 4. Migration Audit

| Check | Status | Notes |
|-------|--------|-------|
| Migration chain integrity | ⚠️ WARNING | Linear after merge, but multiple branches were merged |
| Reproducibility from scratch | ✅ PASS | `7130ecb0388c` (`true_initial_migration`) handles empty DB |
| No-broken migrations | ✅ PASS | Most migrations use `IF NOT EXISTS` blocks |
| Idempotent migrations | ⚠️ WARNING | Mix of raw SQL and Alembic operations, some inconsistencies |
| No data migrations mixed | ✅ PASS | Pure schema migrations only |
| Migration naming consistency | ⚠️ WARNING | Some migrations have empty descriptions |
| Circular dependencies | ✅ PASS | None detected |
| Down migration safety | ⚠️ WARNING | Some downgrades use `IF EXISTS` but may not fully reverse state |
| Merge migration `f50a4054569c` | ⚠️ INFO | Empty merge head, indicates branching history |

---

## 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|-------------|----|------------------|------|
| Development | `bidb` | ✅ Separated | LOW |
| Production | `bidb` | ✅ Separated | LOW |
| Test | `bidb_test` | ✅ Physically separate DB | LOW |

**Test Isolation Details:**
- Test DB uses separate database name (`bidb_test`)
- `recreate_test_db=true` configuration drops and recreates test DB
- Tests use `NullPool` to avoid connection pooling issues
- SAVEPOINT pattern provides transaction isolation per test

---

## 6. Architectural Problems

| Severity | Area | Problem | Risk | Recommendation |
|----------|------|---------|------|----------------|
| MEDIUM | Migration | Multiple migrations renaming same indexes | Creates non-reproducible states | Consolidate index naming into single migration or use consistent naming from start |
| MEDIUM | Migration | Merge head `f50a4054569c` indicates branching | History complexity, potential confusion | Squash migrations or document branching clearly |
| LOW | Schema Design | Redundant index on `dashboard_filters` | Wasted storage, slower writes | Keep dropped per Task-DB-006 - the PK `(dashboard_id, filter_id)` already covers lookup patterns |
| LOW | Maintainability | Multiple no-op migrations (`e86f3c8f7324`, `57f43a5c499d`) | Code noise | Consider squashing or removing empty migrations |
| LOW | Migration | `idx_agg_dashboard_graph` created then dropped multiple times | Unnecessary operations | Standardize on `idx_aggregated_data_dashboard_graph` naming |

---

## 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|------|------|----------------------|----------------|
| `aggregated_data` table | Unbounded growth | Table will grow with each chart data point; without partitioning, queries will degrade significantly after 10M+ rows | Add `dashboard_id` + `graph_id` composite index (exists), consider time-based partitioning if data grows beyond 100M rows |
| `processing_logs` table | Unbounded growth | Logs accumulate indefinitely; large tables impact DELETE performance | Add retention policy with scheduled cleanup job; consider archiving old logs |
| `aggregated_data.dims` GIN index | Index bloat | JSONB GIN indexes can become large with high cardinality | Monitor index size; consider partial indexes if query patterns are predictable |
| Missing index on `aggregated_data.metrics` | Potential full scan | If queries filter by metrics content, GIN index on `dims` won't help | Add GIN index on `metrics` if querying by metric values becomes common |
| No foreign key index on `registration_requests.reviewed_by` | Slow JOINs | Queries filtering by reviewer will be slow | Add index on `reviewed_by` if reporting by reviewer is needed |

---

## 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|------|------|--------|---------------------|
| Migration history | Branching with merge head | Complex history, difficult to understand evolution | MEDIUM - consider squashing migrations |
| Index naming | Multiple migrations rename same indexes | Non-reproducible states, confusion | MEDIUM - consolidate into single migration |
| No-op migrations | Empty migrations in history | Code noise, slower CI | LOW - clean up or squash |
| Raw SQL in migrations | Mixed Alembic API and raw SQL | Inconsistent style, harder to maintain | LOW - refactor to use Alembic operations where possible |

---

## 9. Required Architectural Improvements

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|----------|----------|--------|-----------------|--------------|-----------------|----------------|
| HIGH | Indexing | `aggregated_data` | Missing GIN index on `metrics` column | If queries filter by metrics, will require full table scan | Add `CREATE INDEX CONCURRENTLY idx_aggregated_data_metrics_gin ON aggregated_data USING GIN (metrics)` | Dashboard performance will degrade when filtering aggregated data by metric values |
| MEDIUM | Migrations | Index naming | Multiple migrations rename same indexes inconsistently | Non-reproducible schema states when running migrations on fresh DB | Create single consolidated migration that standardizes all index names | Ensures consistent, reproducible deployments |
| MEDIUM | Scaling | `aggregated_data` table | No partitioning strategy | Table will become slow after 10M+ rows | Add time-based partitioning when table exceeds 100M rows | Prevents query degradation as data grows |
| MEDIUM | Maintainability | Migration history | Merge head and no-op migrations create noise | Development friction, CI slowdowns | Squash migrations to linear history | Cleaner history, faster CI |
| LOW | Schema Design | `dashboard_filters` index | Redundant index exists after migration conflict | Wasted storage, slower writes | Drop `idx_dashboard_filters_dashboard_filter` (per Task-DB-006) | Primary key covers same query pattern |
| LOW | Constraints | Missing NOT NULL on `processing_logs.message` | Allows data inconsistency | Application may fail on NULL message | Consider adding meaningful default or making NOT NULL | Data integrity |

---

## 10. Recommendations Summary

### Critical Actions (Do Now)
1. **Drop redundant index** on `dashboard_filters` - PK `(dashboard_id, filter_id)` already covers lookups
2. **Add GIN index on `aggregated_data.metrics`** if queries filter by metrics content

### Medium-Term Actions
1. **Consolidate migrations** - squash or clean up migration history to remove:
   - Empty merge head `f50a4054569c`
   - No-op migrations `e86f3c8f7324`, `57f43a5c499d`
   - Index renaming migrations that have conflicting operations

2. **Standardize index naming** - create single migration that ensures consistent `idx_` prefix for all indexes

### Long-Term Planning
1. **Plan partitioning strategy** for `aggregated_data` when approaching 100M rows
2. **Add retention policy** for `processing_logs` with automated cleanup
3. **Monitor index sizes** for JSONB GIN indexes as data grows

---

## 11. Appendix: Migration Dependency Graph

```
7130ecb0388c (true_initial_migration) - root
├── e86f3c8f7324 (schema_adjustments) - no-op
│   ├── 57f43a5c499d (change_json_to_jsonb) - no-op
│   │   └── 2aa835fe1fac (add_composite_index)
│   │       └── 840a99edb818 (standardize_index_naming)
│   │           └── 3f7a1b2c9d0e (add_processing_logs_index)
│   │               └── ce58bba5d461 (add_constraints_and_fix_schema)
│   │                   └── a1e404502aac (add_registration_requests)
│   │                       └── f50a4054569c (merge_heads) ←┐
│   │                           &                           │
│   └── 20260507141843 (add_updated_at_to_users) ───────────┤
│       └── f50a4054569c (merge_heads) ─────────────────────┘
│
└── a1b2c3d4e5f6 (add_config_to_dashboards)
    └── a2b3c4d5e6f7 (fix_unique_constraint)
        └── 20260508145000 (add_updated_at_to_layouts)
            └── c3cc391beded (add_config_and_fix_indexes)
                └── 4bfb28b3732d (add_processing_logs_index)
                    └── 91f5436a3098 (add_unique_constraint)
                        └── a2b3c4d5e6f7 (fix_unique_constraint)
```

**Note:** `f50a4054569c` is a merge head joining two branches. The history shows branching and merging which complicates the linear migration path.