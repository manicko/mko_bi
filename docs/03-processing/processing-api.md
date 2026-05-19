---
id: processing-api
domain: processing
tags:
  - upload
  - csv
  - polars
  - aggregation
  - background-tasks
  - data-endpoints
  - processing-logs
related:
  - task-queue
  - dashboards-api
  - schema-processing
  - data-flow
  - security-overview
---

# Processing API

## Overview

The processing API handles CSV file upload, data processing (via Polars), background task execution, and aggregated data retrieval. All endpoints are part of the `/api/v1` route group.

**Processing trigger:** File upload initiates a full recalculation of all aggregates for the target dashboard.

**Base path:** `/api/v1`

---

## Data Upload

### Upload CSV File

Upload a CSV or CSV.gz file to a specific dashboard. The file is saved to a temporary directory (`platformdirs`), processed, and then deleted. File history is not retained.

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `POST`                                             |
| **Path**       | `/api/v1/upload/:dashboard_id`                     |
| **Auth level** | Editor+                                            |
| **Query param**| `mode` — `overwrite` (default) or `append`         |
| **Body**       | `multipart/form-data` with file field              |

**Request headers:**

```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Constraints:**

- Allowed file extensions: `.csv`, `.csv.gz`
- Allowed MIME types: `text/csv`, `application/gzip`, `application/x-gzip`
- Encoding: UTF-8
- Rate limiting is enforced on upload endpoints
- Maximum file size is enforced on the backend
- Temporary files are deleted after processing

**Response** (`200 OK`):

```json
{
  "task_id": "<uuid>",
  "log_id": "<uuid>",
  "status": "started"
}
```

---

## Processing Pipeline

### Pipeline Stages

The data processing pipeline is triggered automatically after file upload or manually via the process endpoint.

```
Upload → Parse (Polars) → Transform (LoaderConfig) → Aggregate → Save to PostgreSQL
```

### Stage Details

| Stage | Description |
| ----- | ----------- |
| **1. Upload** | File saved to temporary directory via `platformdirs` |
| **2. Parse** | File read using Polars; encoding validated as UTF-8 |
| **3. Transform** | Data transformed according to the dashboard's `processing_configs` settings |
| **4. Aggregate** | GroupBy, YoY, share calculations, and custom metrics computed |
| **5. Save** | Results written to `aggregated_data` table (JSONB `dims` + `metrics`) |
| **6. Cleanup** | Temporary file deleted |

**Important:** Each upload triggers a **full recalculation** of aggregates for the dashboard. There is no incremental aggregation.

### Processing Modes

| Mode | Enum Value | Description |
| ---- | ----------- | ----------- |
| Overwrite | `UploadMode.OVERWRITE` | Replaces all existing aggregated data for the dashboard |
| Append | `UploadMode.APPEND` | Adds to existing aggregated data |

---

## Background Processing

CSV loading and processing runs asynchronously through a background task queue.

### Task Lifecycle

```
started → uploaded → processing → success/failed
```

| Status | Enum Value | Description |
| ------ | ----------- | ----------- |
| Started | `ProcessingStatus.STARTED` | Task created, file upload initiated |
| Uploaded | `ProcessingStatus.UPLOADED` | File saved to temporary storage |
| Processing | `ProcessingStatus.PROCESSING` | Pipeline execution in progress |
| Success | `ProcessingStatus.SUCCESS` | Processing completed successfully |
| Failed | `ProcessingStatus.FAILED` | Processing encountered an error |
| Completed | `ProcessingStatus.COMPLETED` | Final state (alias for success in some contexts) |

### Task Queue

The current implementation uses an in-memory `TaskQueue` (MVP). For production, a migration to Redis/RQ is planned. See [Task Queue Migration](task-queue.md) for the complete migration plan.

### Trigger Processing (Manual)

Manually trigger processing for a previously uploaded file.

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `POST`                                             |
| **Path**       | `/api/v1/upload/:dashboard_id/process`             |
| **Auth level** | Editor+                                            |
| **Query param**| `task_id` — UUID of the processing task            |

**Constraints:**

- **Task ownership validation:** The endpoint validates that the requested task belongs to the specified dashboard. If the task's `dashboard_id` does not match the URL parameter, the request is rejected. This prevents cross-dashboard task triggering.

**Response** (`200 OK`):

```json
{
  "task_id": "<uuid>",
  "status": "processing"
}
```

### Check Processing Status

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `GET`                                              |
| **Path**       | `/api/v1/upload/status/:task_id`                   |
| **Auth level** | Editor+                                            |

**Response** (`200 OK`):

```json
{
  "task_id": "<uuid>",
  "status": "processing",
  "message": "Aggregating data..."
}
```

### Get Processing Result

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `GET`                                              |
| **Path**       | `/api/v1/upload/result/:task_id`                   |
| **Auth level** | Editor+                                            |

**Response** (`200 OK`):

```json
{
  "task_id": "<uuid>",
  "status": "success",
  "rows_processed": 15000,
  "graphs_affected": 4
}
```

---

## Custom Metrics (Formula Parser)

Custom metrics are defined as formulas referencing column names with basic arithmetic operators.

### Supported Syntax

- Simple binary expressions with column names: `revenue - cost`, `profit / revenue * 100`
- Operators: `+`, `-`, `*`, `/`

### Limitations [HIGH-RISK]

The formula parser has the following limitations:

- **Not supported:** parentheses, nested expressions
- **Not supported:** numeric literals as operands (e.g., `100 * revenue` is invalid)
- **Not supported:** column names with special characters or spaces
- **Not supported:** unary operators

Formulas are validated before processing. Invalid formulas produce clear error messages indicating the position and nature of the syntax error.

---

## Data Endpoints

### Get Aggregated Data

Retrieve aggregated data for dashboard visualization. Supports filtering by graph and dimension values.

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `GET`                                              |
| **Path**       | `/api/v1/data/aggregated`                          |
| **Auth level** | Viewer+                                            |
| **Query params**| `dashboard_id`, `graph_id`, `filters` (optional)  |

**Request headers:**

```
Authorization: Bearer <token>
```

**Query parameters:**

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `dashboard_id` | UUID | Yes | Target dashboard |
| `graph_id` | UUID | No | Specific graph (returns all graphs if omitted) |
| `filters` | JSON string | No | Filter values (e.g., `{"year": "2024", "category": "A"}`) |

**Response** (`200 OK`):

```json
{
  "dashboard_id": "<uuid>",
  "graph_id": "<uuid>",
  "data": [
    {
      "dims": {"year": "2024", "category": "A"},
      "metrics": {"revenue": 100000, "cost": 60000}
    }
  ]
}
```

**Notes:**

- Data is filtered on the backend (SQL/Polars)
- Global filters (year, category, brand) apply to all graphs
- `dims` keys are sorted recursively before storage to ensure deterministic UPSERT conflict detection (PostgreSQL JSONB equality is sensitive to key ordering)

---

## Processing Config Endpoints

### Get Processing Configuration

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `GET`                                              |
| **Path**       | `/api/v1/processing-configs/:dashboard_id`         |
| **Auth level** | Viewer+                                            |

**Response** (`200 OK`):

```json
{
  "dashboard_id": "<uuid>",
  "settings": {
    "loader": "sales_loader",
    "date_column": "event_date",
    "timezone": "UTC"
  },
  "updated_at": "2026-05-18T12:00:00Z"
}
```

### Update Processing Configuration

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `PUT`                                              |
| **Path**       | `/api/v1/processing-configs/:dashboard_id`         |
| **Auth level** | Editor+                                            |

**Request body:** JSON with `settings` object.

### Delete Processing Configuration

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `DELETE`                                           |
| **Path**       | `/api/v1/processing-configs/:dashboard_id`         |
| **Auth level** | Editor+                                            |

---

## Processing Logs (Admin)

### List Processing Logs

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `GET`                                              |
| **Path**       | `/api/v1/admin/logs`                               |
| **Auth level** | Admin                                              |
| **Query params**| `status`, `dashboard_id`, `date_from`, `date_to`, `skip`, `limit`     |

**Response** (`200 OK`): List of `ProcessingLogRead` objects, filtered and sorted by `started_at` DESC.

### Get Single Processing Log

| Attribute      | Value                                              |
| -------------- | -------------------------------------------------- |
| **Method**     | `GET`                                              |
| **Path**       | `/api/v1/admin/logs/:log_id`                       |
| **Auth level** | Admin                                              |

---

## Data Storage

Only aggregated data is stored. The structure uses a single `aggregated_data` table with JSONB columns for all dashboards:

- `dims` — dimension values (key-value pairs for filters and axes)
- `metrics` — metric values (key-value pairs for display)
- One row equals one data point for a graph
- Data is shared across users (not user-specific)

---

## Cross-References

- [Task Queue Migration](task-queue.md) — In-memory to Redis/RQ migration plan
- [Dashboards API](../02-dashboards/dashboards-api.md) — Dashboard, graph, and filter CRUD
- [Authentication API](../01-auth/auth-api.md) — JWT auth and role definitions
- [Database Schema](../09-database/schema-core.md) — `aggregated_data`, `processing_configs`, `processing_logs` table definitions
- [Security Overview](../08-security/) — Rate limiting, MIME-type validation, file size limits
- [Overview](../00-overview/overview.md) — System architecture and data flow
- [Data Flow](../00-overview/data-flow.md) — End-to-end upload-to-display pipeline
- [Upload UI](../07-frontend/upload-ui.md) — Frontend upload modal and file handling
