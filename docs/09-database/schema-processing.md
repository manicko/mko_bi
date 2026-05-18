---
id: schema-processing
domain: database
tags:
  - aggregated-data
  - processing-logs
  - processing-configs
  - polars
  - jsonb-normalization
  - upsert
related:
  - schema-core
  - schema-access
  - indexes
  - processing-api
  - enums
---

# Processing Schema

## Overview

The processing schema contains tables related to data processing: aggregated data storage, processing logs, and processing configurations. These tables support the CSV upload, transformation, aggregation, and visualization pipeline.

**Schema file:** `src/mkobi/db/models/`

---

## Storage Context

The system stores only aggregated data — raw CSV files are processed and discarded. The processing pipeline:

1. CSV file uploaded to temporary directory (`platformdirs`)
2. File parsed with **Polars**
3. Data transformed per `processing_configs.settings`
4. Aggregations computed (groupby, YoY, shares, custom metrics)
5. Results stored in `aggregated_data` (`dims` + `metrics` JSONB)
6. Temporary file deleted

**JSONB normalization:** `dims` keys are sorted recursively before write operations to ensure deterministic UPSERT conflict detection. PostgreSQL JSONB equality is sensitive to key ordering; without normalization, records with identical semantics but different key insertion orders would be treated as distinct, causing duplicate data.

---

## Tables

### `aggregated_data` — Aggregated Chart Data (CORE)

Stores pre-computed aggregated data for dashboard graphs. Each row represents one chart data point.

```sql
CREATE TABLE aggregated_data (
    id              BIGSERIAL PRIMARY KEY,
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    graph_id        UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    dims            JSONB NOT NULL,
    metrics         JSONB NOT NULL
);
```

| Column        | Type         | Constraints                              | Description                    |
| ------------- | ------------ | ---------------------------------------- | ------------------------------ |
| `id`          | `BIGSERIAL`  | `PRIMARY KEY`                            | Auto-incrementing identifier   |
| `dashboard_id`| `UUID`       | `NOT NULL`, `REFERENCES dashboards(id) ON DELETE CASCADE` | Parent dashboard               |
| `graph_id`    | `UUID`       | `NOT NULL`, `REFERENCES graphs(id) ON DELETE CASCADE` | Associated graph               |
| `dims`        | `JSONB`      | `NOT NULL`                               | Dimension values (key-value)   |
| `metrics`     | `JSONB`      | `NOT NULL`                               | Metric values (key-value)      |

**`dims` JSONB example:**
```json
{
  "year": "2024",
  "month": "January",
  "category": "Electronics"
}
```

**`metrics` JSONB example:**
```json
{
  "revenue": 150000.00,
  "cost": 95000.00,
  "profit": 55000.00
}
```

**Indexes:**
- `idx_aggregated_data_graph_id` — B-tree index on `graph_id`
- `idx_aggregated_data_dashboard_id` — B-tree index on `dashboard_id`
- `idx_aggregated_data_dashboard_graph` — Composite B-tree index on `(dashboard_id, graph_id)`
- `idx_aggregated_data_dims_gin` — GIN index on `dims` (for JSONB containment queries)
- `uq_aggregated_data_dashboard_graph_dims` — Unique index on `(dashboard_id, graph_id, dims::text)` for UPSERT conflict detection

**JSONB normalization note:** The `dims` column uses recursive key sorting before writes. This ensures that `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` produce identical JSONB representations, enabling reliable UPSERT operations via the unique index on `dims::text`.

---

### `processing_logs` — Processing History

Tracks the status of data processing tasks from start to completion or failure.

```sql
CREATE TABLE processing_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE SET NULL,
    status          processing_status NOT NULL,
    message         VARCHAR(1000),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);
```

| Column        | Type            | Constraints                              | Description                    |
| ------------- | --------------- | ---------------------------------------- | ------------------------------ |
| `id`          | `UUID`          | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique identifier              |
| `dashboard_id`| `UUID`          | `REFERENCES dashboards(id) ON DELETE SET NULL` | Associated dashboard (optional) |
| `status`      | `processing_status` | `NOT NULL`                           | Current processing status      |
| `message`     | `VARCHAR(1000)` | Nullable                                 | Error or status message        |
| `started_at`  | `TIMESTAMPTZ`   | Nullable                                 | Processing start timestamp     |
| `finished_at` | `TIMESTAMPTZ`   | Nullable                                 | Processing end timestamp       |

**ENUM type:** `processing_status` = `('started', 'uploaded', 'processing', 'success', 'failed', 'completed')`

**Status lifecycle:**
```
started → uploaded → processing → success → completed
                            ↘ failed
```

**Indexes:**
- `idx_processing_logs_dashboard_id` — B-tree index on `dashboard_id`

---

### `processing_configs` — Processing Configuration

Stores data processing settings for each dashboard. One-to-one relationship with `dashboards`.

```sql
CREATE TABLE processing_configs (
    dashboard_id    UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
    settings        JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

| Column        | Type         | Constraints                              | Description                    |
| ------------- | ------------ | ---------------------------------------- | ------------------------------ |
| `dashboard_id`| `UUID`       | `PRIMARY KEY`, `REFERENCES dashboards(id) ON DELETE CASCADE` | Dashboard ID (also primary key) |
| `settings`    | `JSONB`      | `NOT NULL`                               | Processing configuration       |
| `updated_at`  | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()`             | Last update timestamp          |

**`settings` JSONB example:**
```json
{
  "loader": "sales_loader",
  "date_column": "event_date",
  "timezone": "UTC"
}
```

**Note:** This table stores configuration only, not business logic. Processing logic is implemented in the service layer (`src/mkobi/services/`).

---

## Entity Relationship Diagram (Processing)

```
dashboards (1) ──────── (*) aggregated_data
  │                      │
  │                      │ (*)
  │                      │
  │ (1)                  graphs
  │
  │ (1) ──────── (1) processing_configs
  │
  │ (1) ──────── (*) processing_logs
```

---

## Cross-References

- [Core Schema](./schema-core.md) — `users`, `layouts`, `dashboards`, `graphs`, `filters`
- [Access Schema](./schema-access.md) — `dashboard_access`, `registration_requests`, `dashboard_filters`
- [Indexes](./indexes.md) — All index definitions
- [Enums](./enums.md) — All StrEnum definitions
- [Processing API](../03-processing/processing-api.md) — Upload and processing endpoints
- [Task Queue](../03-processing/task-queue.md) — Background processing architecture
- [Data Flow](../00-overview/data-flow.md) — End-to-end data processing pipeline
- [Admin API](../04-admin/admin-api.md) — Processing log viewer
