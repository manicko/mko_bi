# Bug Report: Missing Data Export Endpoint

**Date:** 2026-06-17
**Severity:** HIGH
**Status:** UNIMPLEMENTED

## Problem

The task `TASK_061_int020_add_data_export_test.yaml` requests adding an integration test that:
1. Uploads data
2. Requests data export
3. Verifies export format is valid CSV/Excel
4. Verifies exported data matches uploaded data

However, **no data export endpoint exists in the codebase**. The task references "INT-020: Data Export is Untested" but:
- The actual INT-020 finding from `90-integration-validated.md` (line 189-199) is about "Duplicate role update endpoints"
- No `/export` or `/download` endpoint exists in any API route module
- No data export functionality exists in the frontend

## Evidence

### Backend Search
No data export endpoints found:
```bash
# No export/download endpoints in routes
grep -r "/export" src/mkobi/api/routes/  # No results
grep -r "/download" src/mkobi/api/routes/  # No results
grep -r "export_data\|download_data" src/mkobi/  # No results
```

Available data endpoints in `src/mkobi/api/routes/data.py`:
- `GET /data/aggregated` - Returns aggregated data for charts (JSON format)
- No endpoint returns data in CSV or Excel format

### Available Routes (from __init__.py)
- admin, auth, client_errors, dashboards, dashboards_access, dashboards_crud
- dashboards_filters, dashboards_graphs, filter_values, data, graphs
- layouts, processing_configs, processing_logs, upload, users

All endpoints return JSON responses. No file export/return functionality exists.

### Frontend Search
No data export functionality in frontend:
```bash
grep -r "exportData\|downloadData\|export.*csv\|export.*excel" frontend/src/  # No results
```

Frontend data fetching:
- `dashboardApi.getAggregatedData()` returns `AggregatedDataResponse` (JSON)
- All data endpoints use JSON responses

## Current Implementation

Data flow is JSON-only:
1. **Upload**: `POST /api/v1/upload/{dashboard_id}` - uploads CSV, processes, stores in DB
2. **Retrieve**: `GET /api/v1/data/aggregated` - returns aggregated data as JSON for charts
3. **No Export**: No endpoint returns raw data in CSV/Excel format

## Recommendation

The task cannot be completed as-is because the feature does not exist. Two options:

### Option A: Implement Data Export Feature
Add a data export endpoint:
1. Add `GET /data/export` endpoint in `src/mkobi/api/routes/data.py`
2. Accept `dashboard_id` and optional `graph_id` parameters
3. Return aggregated data as CSV or Excel file
4. Then add the integration test

### Option B: Reclassify Task as New Feature
The task appears to be a feature request mislabeled as a bug fix. Should be:
- Moved to feature backlog
- Or re-scoped to test the existing `/data/aggregated` endpoint more thoroughly

## Affected Files

None - this is a missing feature, not a bug in existing code.

## Related Tasks

The task file references the wrong INT finding. The actual INT-020 deals with duplicate user role endpoints, not data export. This may indicate a copy-paste error in task creation.