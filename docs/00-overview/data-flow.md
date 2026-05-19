---
id: data-flow
domain: overview
tags:
  - data-pipeline
  - upload
  - processing
  - aggregation
  - storage
  - visualization
related:
  - system-overview
  - processing-api
  - schema-core
  - dashboards-api
---

# Data Flow

## End-to-End Flow: Upload to Display

```
User (Browser)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  1. UPLOAD                                              │
│  POST /api/v1/upload/:dashboard_id?mode=overwrite|append │
│  ├─ File saved to temp directory (platformdirs)         │
│  ├─ MIME-type validated (.csv, .csv.gz)                 │
│  ├─ File size checked                                   │
│  └─ Processing task queued (TaskQueue)                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  2. PARSE                                               │
│  ├─ Read file with Polars (UTF-8 encoding)              │
│  └─ Validate structure against processing config        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  3. TRANSFORM                                           │
│  ├─ Apply transformations per LoaderConfig              │
│  ├─ Custom metrics evaluated (formula parser)           │
│  └─ Data types normalized                               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  4. AGGREGATE                                           │
│  ├─ GroupBy operations                                  │
│  ├─ YoY (Year-over-Year) calculations                   │
│  ├─ Share/ratio computations                            │
│  ├─ Custom metric aggregation                           │
│  └─ Full recalculation (all aggregates rebuilt)         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  5. SAVE TO POSTGRESQL                                  │
│  ├─ Write to aggregated_data table (JSONB dims+metrics) │
│  ├─ JSONB keys normalized (sorted) for UPSERT           │
│  └─ Temp file deleted                                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  6. FRONTEND REQUESTS DATA                              │
│  GET /api/v1/data/aggregated                            │
│     ?dashboard_id=:id&graph_id=:id&filters=...          │
│  ├─ Access check (user ↔ dashboard)                     │
│  ├─ Filters applied (backend: SQL/Polars)               │
│  └─ JSON response with chart data                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  7. RENDER                                              │
│  ├─ React SPA receives data via TanStack Query          │
│  ├─ Plotly.js React renders charts                      │
│  └─ Filters update all linked graphs                    │
└─────────────────────────────────────────────────────────┘
```

## Upload Details

* **Formats**: `.csv`, `.csv.gz`
* **Encoding**: UTF-8
* **Lifecycle**: File is uploaded → processed → deleted
* **History**: Not stored (only aggregated results persist)
* **Mode**: `overwrite` (replaces all data) or `append` (adds to existing)

## Processing Details

* **Trigger**: File upload
* **Pipeline**:
  1. Read with Polars
  2. Transform per dashboard configuration
  3. Aggregate: groupby, YoY, shares, custom metrics
* **Result**: Full recalculation, written to PostgreSQL
* **Background**: Processing runs asynchronously via task queue (in-memory `TaskQueue` for MVP; Redis + RQ for production). See [Task Queue](../03-processing/task-queue.md) for the migration plan.
* **File processing service**: `file_processing.py` handles validation, upload, and task orchestration.
* **Background worker**: `data_worker.py` provides `process_csv_background` (async) and `process_csv_background_sync` (sync RQ wrapper) with mode-aware data persistence (`overwrite` clears old data, `append` keeps it).
* **Status tracking**: `processing_logs` table (`started` → `uploaded` → `processing` → `success`/`failed`)

## Storage Details

* **Only aggregated data is stored** (raw files are not persisted)
* **Structure**: Single `aggregated_data` table using JSONB for all dashboards
  * `dims` — dimension values (key-value for filters and axes)
  * `metrics` — metric values (key-value for display)
* **Data is shared** (not user-dependent; access controlled via `dashboard_access` table). See [Access Control](../08-security/access-control.md) for the permission model.
* **JSONB normalization**: `dims` keys are sorted recursively before writes to ensure deterministic UPSERT conflict detection

## Related Documentation

* [Technology Stack — overview.md](./overview.md)
* [Auth & Access Control](../01-auth/auth-api.md) — Authentication and role-based access
* [Database Schema](../09-database/schema-core.md) — Core table definitions for `dashboards`, `graphs`, `filters`
* [Processing Configuration](../03-processing/processing-api.md) — Upload, processing pipeline, and data endpoints
* [Security Overview](../08-security/security-overview.md) — Rate limiting, file upload security, credential enforcement
* [Task Queue](../03-processing/task-queue.md) — Background processing and migration plan
