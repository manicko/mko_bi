---
id: upload-ui
domain: frontend
tags:
  - file-upload
  - csv
  - react-dropzone
  - upload-modes
  - processing-status
  - api-integration
  - file-validation
related:
  - frontend-security
  - processing-api
  - pages
  - frontend-architecture
---

# Upload UI

## Overview

The upload feature (`features/upload/`) provides the UI and API integration for uploading CSV and CSV.gz files to a dashboard. The upload page is accessible at `/dashboard/:id/upload` and is restricted to users with `admin` or `editor` roles.

## Upload Page

**Component:** `features/upload/ui/UploadPage.tsx`

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Mode toggle | `ToggleButtonGroup` | "Overwrite" (reset all data) / "Append" (add new rows) |
| File dropzone | `FileDropzone` | Drag-and-drop area; accepts `.csv` and `.csv.gz` |
| File list | List | Selected files with remove buttons and file sizes |
| Upload queue | Paper section | Per-file progress bars with status indicators |
| Start Upload button | `Button` | Begins sequential upload of all files; disabled while uploading |
| Cancel button | `Button` | Returns to dashboard view; disabled while uploading |
| Success alert | `Alert` | Shown when all files are uploaded and processing begins |

### Upload Modes

| Mode | Enum Value | Description |
| --- | --- | --- |
| Overwrite | `UploadMode.OVERWRITE` | Replaces all existing aggregated data for the dashboard |
| Append | `UploadMode.APPEND` | Adds new data rows to existing aggregated data |

## File Dropzone

**Component:** `features/upload/ui/FileDropzone.tsx`

Built on `react-dropzone` with the following configuration:

### Accepted File Types

- **Extensions:** `.csv`, `.csv.gz`
- **MIME types:** `text/csv`, `application/gzip`, `application/x-gzip`

### Client-Side Validation

1. **MIME type check:** Files are filtered by MIME type via the dropzone `accept` prop.
2. **Extension check:** Additional validation ensures the filename ends with `.csv` or `.csv.gz`.
3. **Rejection handling:** Invalid files trigger a toast error message.

### UI States

- **Idle:** "Drag & drop files here, or click to select"
- **Drag active:** Border and background highlight changes; "Drop files here..."
- **Files selected:** File list with name, size, and remove button for each file

## Upload Flow

```
User selects mode (overwrite/append)
       │
       ▼
User drags/drops files onto dropzone
       │
       ▼
Client validates file extensions and MIME types
       │
       ▼
Files appear in the upload queue
       │
       ▼
User clicks "Start Upload"
       │
       ▼
For each file:
  ┌─────────────────────────────────┐
  │ POST /api/v1/upload/:dashboard_id│
  │ Query: mode=overwrite|append     │
  │ Body: multipart/form-data        │
  │ Progress: tracked via callback   │
  └────────────────┬────────────────┘
                   │
                   ▼
  On success: { task_id, log_id, status: "started" }
  On failure: error toast, file marked as ERROR
                   │
                   ▼
All files uploaded → poll processing status
       │
       ▼
GET /api/v1/upload/status/:task_id (polled)
       │
       ▼
Status = 'completed' or 'success'
  → toast success → redirect to /dashboard/:id
```

## API Integration

**Module:** `features/upload/api/uploadApi.ts`

| Function | Method | Endpoint | Description |
| --- | --- | --- | --- |
| `uploadFile` | `POST` | `/api/v1/upload/:dashboard_id` | Uploads a file with progress callback; query param `mode` |
| `useProcessingStatus` | `GET` | `/api/v1/upload/status/:task_id` | TanStack Query hook for polling processing status |

### Upload Request

```
POST /api/v1/upload/:dashboard_id?mode=overwrite
Content-Type: multipart/form-data
Authorization: Bearer <token>

File: <binary data>
```

**Response** (`200 OK`):
```json
{
  "task_id": "<uuid>",
  "log_id": "<uuid>",
  "status": "started"
}
```

### Processing Status Polling

After all files are uploaded, the page polls for processing status:

```
GET /api/v1/upload/status/:task_id
```

**Response:**
```json
{
  "task_id": "<uuid>",
  "status": "processing",
  "message": "Aggregating data..."
}
```

Polling continues until `status` is `'completed'` or `'success'`, at which point the user is redirected to the dashboard view.

## Backend Processing Pipeline

Once the file is uploaded, the backend executes the full processing pipeline:

```
Upload → Parse (Polars) → Transform (LoaderConfig) → Aggregate → Save to PostgreSQL
```

**Important:** Each upload triggers a **full recalculation** of aggregates for the dashboard. There is no incremental aggregation.

### Processing Status Lifecycle

| Status | Description |
| --- | --- |
| `started` | Task created, file upload initiated |
| `uploaded` | File saved to temporary storage |
| `processing` | Pipeline execution in progress |
| `success` | Processing completed successfully |
| `failed` | Processing encountered an error |
| `completed` | Final state |

## File Upload Security

### Client-Side Checks

- File extension validation (`.csv`, `.csv.gz` only).
- MIME type filtering via `react-dropzone` accept configuration.
- User feedback via toast notifications for rejected files.

### Server-Side Enforcement

The backend independently enforces:

- **MIME type validation:** Only `text/csv`, `application/gzip`, `application/x-gzip` are accepted.
- **File size limit:** Maximum file size is enforced on the backend.
- **Rate limiting:** Upload endpoints are rate-limited.
- **Temporary file cleanup:** Files are deleted from temporary storage after processing.

**Note:** Client-side validation is a UX convenience. The backend is the security boundary — all validation is enforced server-side regardless of client behavior.

## Cross-References

- [Frontend Security](frontend-security.md) — File upload security details
- [Processing API](../../03-processing/processing-api.md) — Backend upload and processing endpoints
- [Pages](pages.md) — Upload page UI elements
- [Data Flow](../../00-overview/data-flow.md) — End-to-end upload-to-display pipeline
- [Task Queue](../../03-processing/task-queue.md) — Background processing architecture
