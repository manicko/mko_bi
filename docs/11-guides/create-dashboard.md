---
id: create-dashboard
domain: guides
tags:
  - guide
  - admin
  - dashboard-creation
  - workflow
  - howto
related:
  - dashboards-api
  - processing-api
  - schema-core
  - data-flow
  - docker
  - extend-graphs-filters
---

## Purpose

This guide walks administrators through the end-to-end process of creating a new dashboard in the mkobi BI Dashboard System, including planning, dashboard creation, layout configuration, and graph setup. It assumes familiarity with the application UI and focuses on workflow rather than detailed API field specifications, which are covered in the [Dashboards API](../02-dashboards/dashboards-api.md) reference.

## Prerequisites

You must have the Admin role to create dashboards. Additionally, you should:

- Have identified the data source (CSV file) that will populate the dashboard
- Understand the column structure of your data (dimensions and metrics)
- Know which chart types best represent your data for analysis

## Pre-Creation Planning

Before creating a dashboard, plan the following:

- **Data sources:** Identify the CSV file(s) that will provide the data. Each dashboard expects data with specific column structures.
- **Columns:** Determine which columns represent dimensions (categorical data used for grouping and filtering) versus metrics (numerical values to aggregate).
- **Chart types:** Decide which graphs to create — bar, line, pie, or table — based on how you want to visualize each data relationship.
- **Processing config:** Prepare the processing configuration that defines how CSV columns map to dimensions and metrics. See [Processing API](../03-processing/processing-api.md) for details on loader settings and date column configuration.

## Create the Dashboard

Navigate to the Admin page and select "Create Dashboard" to open the dashboard creation form. The form requires:

- **Name:** A unique identifier for the dashboard across the system
- **Description:** A brief description explaining the dashboard's purpose
- **Layout:** Select an existing layout template or create a new one. Layouts define the grid structure and graph positions. See [Dashboards API](../02-dashboards/dashboards-api.md) for field-level details on layout selection.

> **Note:** Dashboard configuration requires `graph_types` — an array of supported chart types (bar, line, pie, table) that determines which visualization types are available for graphs on this dashboard. This is typically set to `["bar"]` by default or matched to the types of graphs you plan to create.

Submitting this form creates the dashboard and redirects to the dashboard edit view where you can configure the layout and add graphs.

## Configure the Layout

Layouts define the UI composition of a dashboard through a grid system. Each layout organizes graphs in rows and columns, with each graph occupying a slot defined by position and dimensions. Layouts are reusable — multiple dashboards can reference the same layout structure.

Key concepts:

- **Grid:** A responsive grid system where graphs are positioned by x/y coordinates and width/height values
- **Graph slots:** Each slot in the layout corresponds to a graph that will be created
- **Filters:** Layouts can include filter bindings that apply selected dimension values across multiple graphs

Create or modify layouts in the Admin interface. For the exact JSONB structure defining grid positions and filter bindings, see [Dashboards API](../02-dashboards/dashboards-api.md#layout-endpoints).

## Add Graphs

Graphs are the visualizations within a dashboard. Each graph belongs to exactly one dashboard and defines how aggregated data is rendered.

**Graph types available:**

| Type | Description |
| ---- | ----------- |
| `bar` | Vertical or horizontal bar charts for comparing values across categories |
| `line` | Line charts for trend analysis over time or continuous data |
| `pie` | Pie or donut charts for showing proportions of a whole |
| `table` | Tabular display of raw aggregated data |

**Dimensions vs. Metrics:**

- **Dimensions** are categorical fields used for grouping and X-axis values. For example: `month`, `category`, `region`
- **Metrics** are numerical fields that are aggregated (summed) for display on the Y-axis. For example: `revenue`, `cost`, `profit`

When creating a graph, specify the `name`, `type`, `dimensions`, and `metrics`. The `config` field contains chart-specific options like axis labels, colors, and YoY (year-over-year) mode. See [Dashboards API](../02-dashboards/dashboards-api.md#graph-endpoints) and [Dashboards API](../02-dashboards/dashboards-api.md#graph-types) for complete details on graph configuration options.

## Add/Bind Filters

Filters allow users to interactively narrow down the data displayed in graphs. Each filter has a type that determines its UI control and behavior.

**Filter types available:**

| Type | Description | UI Control |
| ---- | ----------- | ---------- |
| `select` | Single value selection from a dropdown | Dropdown |
| `multiselect` | Multiple values selection | Multi-select with checkboxes |
| `range` | Numeric range filtering (min/max) | Range slider |
| `date` | Date or date range selection | Date picker |

**Binding filters to a dashboard:**

Filters are created globally and then bound to specific dashboards. To add filters:

1. Navigate to the Admin page and open the Filters management section
2. Create new filters or select existing ones, specifying the filter name and type
3. For each filter, set the `config.field` to match a dimension name in your data
4. Set `config.source` to `"dims"` for static options or `"data"` for dynamic values extracted from uploaded data
5. Bind filters to your dashboard using the "Bind Filter" action in the dashboard editor

Once bound, filters appear in the dashboard's filter panel and automatically apply to all graphs. See [Dashboards API](../02-dashboards/dashboards-api.md#filter-endpoints) for the complete API specification.

## Set Up Processing Config

The processing config defines how CSV data is parsed and transformed before aggregation. It controls separators, encodings, date handling, and other loader-specific settings.

Key settings include:

- **loader** — Identifier for the processing profile (e.g., `"sales_loader"`, `"marketing_loader"`)
- **date_column** — Name of the column containing dates for YoY calculations
- **encoding** — Character encoding (default: `"utf-8"`)
- **separator** — CSV delimiter character (default: `","`)
- **timezone** — Timezone for date operations (default: `"UTC"`)

Navigate to the Admin page and select "Processing Config" for your dashboard. The `settings` JSONB object accepts loader-specific configurations. See [Processing API](../03-processing/processing-api.md#processing-config-endpoints) for field-level detail on settings structure. Annotated examples are provided in the [Appendix](#appendix).

## Upload Data

After setting up graphs, filters, and processing config, upload your CSV data to populate the dashboard.

**Upload endpoint:** `POST /api/v1/upload/{dashboard_id}`

| Attribute | Value |
| --------- | ----- |
| **Method** | `POST` |
| **Path** | `/api/v1/upload/:dashboard_id` |
| **Auth level** | Editor+ |
| **Query param** | `mode` — `overwrite` (default) or `append` |
| **Body** | `multipart/form-data` with file field |

**File constraints:**

- Allowed extensions: `.csv`, `.csv.gz`
- Allowed MIME types: `text/csv`, `application/gzip`, `application/x-gzip`
- MIME type detection uses server-side content sniffing (`python-magic`), not the client header
- Encoding: UTF-8 by default
- Rate limiting enforced on the upload endpoint
- Maximum file size enforced on the backend

**Upload modes:**

- **overwrite** — Replaces all existing aggregated data for the dashboard
- **append** — Adds to existing aggregated data

**Task queue lifecycle:**

When a file is uploaded, it transitions through these states:

```
started → uploaded → processing → success/failed
```

Check processing status via `GET /api/v1/upload/status/:task_id`. See [Processing API](../03-processing/processing-api.md) for complete endpoint details.

## Verify Results

After upload completes, verify the results to ensure data was processed correctly.

**Check processing status:**

Use `GET /api/v1/upload/status/:task_id` to monitor the task. A successful status returns `"success"` with `rows_processed` count in the result.

**View uploaded data:**

Open the dashboard view to see graphs rendered with your data. If graphs show data, the upload and processing completed successfully. Use the filter panel to test filter functionality.

**Apply filters:**

Select values in the filter panel to verify that:
- Filter options populate correctly (especially for `source: "data"` filters)
- Graph data updates appropriately based on selections
- Multiple filters work together as expected

See [Data Flow](../00-overview/data-flow.md) for the complete end-to-end pipeline.

## Grant Dashboard Access

Share your dashboard with other users by granting access permissions.

**Endpoint:** `/api/v1/dashboards/{dashboard_id}/access`

| Action | Method | Auth level |
| ------ | ------ | ---------- |
| Grant access | `POST` | Admin |
| List access | `GET` | Admin |
| Revoke access | `DELETE` | Admin |

**Permission levels:**

| Level | Description |
| ----- | ----------- |
| `view` | Read-only access to dashboard and its data |
| `edit` | Can upload data and trigger processing |
| `admin` | Full control including dashboard management and access grants |

To grant access, send a request with `user_id`, `dashboard_id`, and `permission` level. To list current access, use the GET endpoint to see all users with access. To revoke, use DELETE with both `dashboard_id` and `user_id` path parameters.

See [Dashboards API](../02-dashboards/dashboards-api.md#dashboard-access-management) for API details and [Access Schema](../09-database/schema-access.md) for the table structure.

## Ongoing Operations

Dashboard management continues after initial setup. Common ongoing tasks include:

**Re-uploading data:**

Upload new data files at any time. Each upload triggers a full recalculation of aggregates. Use `overwrite` mode to replace existing data or `append` mode to add to it.

**Modifying processing config:**

Update the processing configuration via `PUT /api/v1/processing-configs/:dashboard_id` when your CSV format changes. Changes take effect on the next upload.

**Managing filters:**

- Bind/unbind filters via the dashboard editor or API endpoints
- Re-upload data to update dynamic filter values (when `source: "data"`)
- Modify filter configuration through filter update endpoints

**Re-granting access:**

Access permissions are persistent. Users retain their permission level until revoked. You can change a user's permission level by granting new access (the system updates the existing record).

## Troubleshooting

Common issues and their resolutions:

**Upload rejected:**

- Verify file extension is `.csv` or `.csv.gz`
- Check that MIME type is `text/csv` or `application/gzip`
- Ensure file size is within backend limits
- Confirm you have Editor+ role on the dashboard

**Processing stuck:**

- Check processing logs via Admin → Processing Logs
- Verify the CSV structure matches the processing config
- Ensure all required columns are present in the data
- Check for malformed data rows that might cause parsing failures

**No data after upload:**

- Verify graphs have correct `dimensions` and `metrics` configured
- Check that processing completed with `"success"` status
- Ensure at least one graph exists on the dashboard
- Review processing config settings (separator, encoding) for mismatches

**Filter not working:**

- Verify filter is bound to the dashboard
- Check `config.field` matches a dimension name in your data
- For `source: "data"` filters, re-upload to populate filter values
- Ensure filter values exist in the aggregated data

**Access grant not working:**

- Confirm you are an Admin on the dashboard
- Verify the target user exists in the system
- Check that `dashboard_id` in request body matches the URL parameter
- Ensure the user does not already have conflicting access

## Appendix

**Simple processing config example:**

```json
{
  "loader": "basic_loader",
  "encoding": "utf-8",
  "separator": ","
}
```

A minimal configuration for standard CSV files with comma separator and UTF-8 encoding.

**Medium processing config example (with date parsing):**

```json
{
  "loader": "sales_loader",
  "date_column": "sale_date",
  "timezone": "Europe/Moscow",
  "encoding": "utf-8",
  "separator": ","
}
```

Includes date column specification for YoY calculations and timezone for date operations.

**Complex processing config example (custom separators, multiple mappings):**

```json
{
  "loader": "financial_loader",
  "date_column": "period",
  "timezone": "UTC",
  "separator": ";",
  "encoding": "utf-8",
  "dimension_columns": ["year", "quarter", "region", "product"],
  "metric_columns": ["revenue", "cost", "profit"],
  "decimal_separator": ","
}
```

Uses semicolon separator (common in European CSV files) and explicitly maps dimension/metric columns. Also specifies decimal separator for float parsing.

## DB/API Reference

| Table | Purpose | Key Columns | Docs |
| ----- | ------- | ----------- | ---- |
| `dashboards` | Dashboard definitions | `id`, `name`, `description`, `layout_id` | [schema-core.md](../09-database/schema-core.md) |
| `processing_configs` | CSV parsing settings | `dashboard_id`, `settings` (JSONB) | [schema-processing.md](../09-database/schema-processing.md) |
| `processing_logs` | Task status tracking | `id`, `dashboard_id`, `status`, `message` | [schema-processing.md](../09-database/schema-processing.md) |
| `dashboard_access` | User permissions | `user_id`, `dashboard_id`, `permission` | [schema-access.md](../09-database/schema-access.md) |
| `dashboard_filters` | Dashboard-filter links | `dashboard_id`, `filter_id` | [schema-access.md](../09-database/schema-access.md) |
| `dashboard_filter_values` | Cached filter options | `dashboard_id`, `filter_name`, `filter_value` | [schema-processing.md](../09-database/schema-processing.md) |
| `aggregated_data` | Stored chart data points | `dashboard_id`, `graph_id`, `dims`, `metrics` | [schema-processing.md](../09-database/schema-processing.md) |

## Cross-Links

- [Dashboards API](../02-dashboards/dashboards-api.md) — CRUD for dashboards, graphs, filters, access management
- [Processing API](../03-processing/processing-api.md) — Upload, processing, and data endpoints
- [Core Schema](../09-database/schema-core.md) — Table definitions for users, dashboards, layouts, graphs, filters
- [Processing Schema](../09-database/schema-processing.md) — Table definitions for aggregated data, processing configs, processing logs
- [Access Schema](../09-database/schema-access.md) — Table definitions for dashboard_access, dashboard_filters
- [Data Flow](../00-overview/data-flow.md) — End-to-end upload-to-display pipeline
- [Extend Graphs & Filters](./extend-graphs-filters.md) — How to add new graph types and filter capabilities