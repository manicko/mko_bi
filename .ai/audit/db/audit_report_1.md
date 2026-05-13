# PostgreSQL Database Audit Report

**Project:** mkobi BI Dashboard  
**Date:** 2026-05-13  
**Auditor:** AI Assistant

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Tables | 9 |
| Primary Keys | 8 UUID, 1 BIGSERIAL |
| Foreign Keys | 8 |
| Indexes | 13 |
| Enums | 5 |
| Migrations | 15 files |
| Schema Drift Issues | 1 critical |

**Status:** Database is functional but has a critical extension mismatch between ORM code and production schema.

---

## Database Inventory

| Environment | Database | Purpose |
|-------------|----------|---------|
| Development | `bidb` | Local development |
| Testing | `bidb_test` | Test database |
| Production | `bidb` | Production data (from schema dump) |

**Connection:** `postgresql+asyncpg://postgres:***@localhost:5432/{dbname}`

---

## Schema Analysis

### Tables Overview

| Table | PK Type | Purpose |
|-------|---------|---------|
| `users` | UUID | User accounts, auth |
| `registration_requests` | UUID | User registration workflow |
| `layouts` | UUID | Dashboard UI structure |
| `dashboards` | UUID | BI dashboards |
| `graphs` | UUID | Chart definitions |
| `filters` | UUID | Reusable filters |
| `dashboard_filters` | Composite | Many-to-many dashboard↔filter |
| `dashboard_access` | Composite | User↔dashboard permissions |
| `aggregated_data` | BIGSERIAL | Pre-aggregated chart data |
| `processing_configs` | UUID (PK) | Data processing settings |
| `processing_logs` | UUID | Processing history |

### Enum Types

| Enum Name | Values | Usage |
|-----------|--------|-------|
| `user_role` | admin, editor, viewer | `users.role` |
| `dashboard_permission_level` | view, edit, admin | `dashboard_access.permission` |
| `graph_type` | bar, line, pie, table | `graphs.type` |
| `filter_type` | select, multiselect, range, date | `filters.type` |
| `processing_status` | started, uploaded, processing, success, failed, completed | `processing_logs.status` |

### Index Inventory

| Table | Index | Type | Columns |
|-------|-------|------|---------|
| `users` | `idx_users_email` | UNIQUE | email |
| `users` | `idx_users_role` | btree | role |
| `layouts` | `idx_layouts_name` | UNIQUE | name |
| `dashboards` | `idx_dashboards_name` | UNIQUE | name |
| `graphs` | `idx_graphs_dashboard_name` | UNIQUE | dashboard_id, name |
| `graphs` | `idx_graphs_dashboard` | btree | dashboard_id |
| `filters` | `idx_filters_name` | UNIQUE | name |
| `dashboard_filters` | `idx_dashboard_filters_dashboard_filter` | btree | dashboard_id, filter_id |
| `dashboard_access` | `idx_dashboard_access_user` | btree | user_id |
| `dashboard_access` | `idx_dashboard_access_dashboard` | btree | dashboard_id |
| `aggregated_data` | `idx_aggregated_data_dashboard_id` | btree | dashboard_id |
| `aggregated_data` | `idx_aggregated_data_graph_id` | btree | graph_id |
| `aggregated_data` | `idx_aggregated_data_dims_gin` | GIN | dims |
| `aggregated_data` | `uq_aggregated_data_dashboard_graph_dims` | UNIQUE | dashboard_id, graph_id, dims::text |
| `processing_logs` | `idx_processing_logs_dashboard_id` | btree | dashboard_id |

---

## Schema Drift Analysis

### Critical Issue: Extension Mismatch

| Source | Extension | Default Function |
|--------|-----------|------------------|
| Schema dump (`bidb_schema.sql`) | `uuid-ossp` | `uuid_generate_v4()` |
| ORM models (`user.py`, `dashboard.py`, etc.) | `pgcrypto` | `gen_random_uuid()` |

**Impact:** The production database uses `uuid-ossp` extension but the ORM code specifies `gen_random_uuid()`. Both generate UUIDs but belong to different extensions. If the schema is recreated from scratch using migrations, UUIDs will fail unless `pgcrypto` is installed instead.

**Recommendation:** Standardize on `pgcrypto` (preferred in PostgreSQL 13+) which provides `gen_random_uuid()`. Update the schema dump and ensure all migrations use the same extension.

### Missing Migration for registration_requests

The `registration_requests` table was added in migration `a1e404502aac` but the `bidb_schema.sql` does not include it. This indicates the schema dump may be outdated.

### No-op Migrations Present

Two migrations are explicit no-ops:
- `e86f3c8f7324_schema_adjustments.py` - "true_initial_migration already creates everything correctly"
- `57f43a5c499d_change_json_to_jsonb_for_postgresql.py` - "true_initial_migration already uses JSONB"

These should be removed in a cleanup to avoid confusion.

### Merge Migration Created

Migration `f50a4054569c_merge_heads.py` merges two heads:
- `20260507141843` (add updated_at to users)
- `a1e404502aac` (add registration_requests table)

This indicates divergent migration history that was resolved with a merge.

---

## Relationship Analysis

```
users (1) ──< registration_requests
   │
   └──< dashboard_access >── dashboards (1)
                               │
                               ├──< graphs
                               │      └──< aggregated_data
                               │
                               ├──< dashboard_filters >── filters
                               │
                               ├──< dashboard_access (via junction)
                               │
                               └── processing_config
                                        │
                                        └── processing_logs
```

**Foreign Key Constraints:**
- `aggregated_data.dashboard_id` → `dashboards.id` ON DELETE CASCADE
- `aggregated_data.graph_id` → `graphs.id` ON DELETE CASCADE
- `dashboards.layout_id` → `layouts.id` ON DELETE SET NULL
- `dashboards.created_by` → `users.id` ON DELETE SET NULL
- `dashboard_access.user_id` → `users.id` ON DELETE CASCADE
- `dashboard_access.dashboard_id` → `dashboards.id` ON DELETE CASCADE
- `registration_requests.reviewed_by` → `users.id` ON DELETE SET NULL

---

## Data Flow Assessment

**Upload Process:**
1. Files uploaded to `data/tmp_uploads` (platformdirs)
2. Polars parses CSV/CSV.GZ
3. Data transformed and aggregated by `ProcessingConfig`
4. Results stored in `aggregated_data` (JSONB dims + metrics)
5. Frontend fetches via `/data/aggregated` endpoint

**Critical Data Characteristics:**
- `aggregated_data` grows unbounded (no partitioning)
- Large JSON blobs in `metrics` and `dims` columns
- GIN index on `dims` for fast dimension filtering

---

## Recommendations

### High Priority

1. **Fix Extension Mismatch**
   - Install `pgcrypto` extension (provides `gen_random_uuid()`)
   - Update `bidb_schema.sql` to use `pgcrypto` instead of `uuid-ossp`
   - Ensure Alembic migrations create `pgcrypto` if needed

2. **Clean Up No-op Migrations**
   - Remove `e86f3c8f7324_schema_adjustments.py` and `57f43a5c499d_change_json_to_jsonb_for_postgresql.py`
   - Rebuild migration history from `7130ecb0388c true_initial_migration` forward

### Medium Priority

3. **Partition aggregated_data**
   - Table will grow significantly with dashboard usage
   - Consider range partitioning by `created_at` (when added) or `dashboard_id`

4. **Add updated_at to aggregated_data**
   - ORM model has `updated_at` but schema dump doesn't show it
   - Verify schema matches model

### Low Priority

5. **Document registration_requests missing from schema dump**
   - Update `bidb_schema.sql` to include all tables
   - Consider automated schema dump generation

---

## Reproducibility Assessment

| Requirement | Status | Notes |
|-------------|--------|-------|
| Schema from migrations | ✅ | `7130ecb0388c` creates all tables |
| Extension support | ⚠️ | `uuid-ossp` in dump vs `pgcrypto` in code |
| Test database | ✅ | `bidb_test` configured in `conftest.py` |
| Data seeding | ❌ | No seed data defined |

**Migration Replay:** Running `alembic upgrade head` from clean database should work, but requires `pgcrypto` extension for UUID generation.

---

## Appendix: File References

| File | Purpose |
|------|---------|
| `src/mkobi/db/models/*.py` | SQLAlchemy ORM definitions |
| `bidb_schema.sql` | Production schema dump |
| `alembic/versions/` | 15 migration files |
| `tests/conftest.py` | Test database configuration |
| `docker-compose.yml` | Main DB service (bidb) |
| `docker-compose.test.yml` | Test DB service (bidb_test) |
| `src/mkobi/config.py` | Database connection settings |