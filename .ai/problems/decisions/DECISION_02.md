# Phase 2: Test Dashboard (test_media_dash) - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

## Phase Boundary

Build a working test dashboard named `test_media_dash` using the existing test data file (`data/test/test_data.csv.gz`), following the current application architecture end-to-end: upload → parse → transform → aggregate → store → retrieve → visualize. Research the existing codebase, identify what is missing, and describe the implementation. All development must assume a multi-dashboard architecture — every piece of functionality must work for any number of dashboards, not hardcoded for this one.

## Implementation Decisions

### Data Pipeline Strategy

- **Full pre-aggregation on upload via Polars** — Raw CSV is never stored. During upload, Polars reads the file, transforms columns, and generates all aggregated rows. Only aggregated results are persisted to `aggregated_data`.
- **Aggregation GROUP BY rule** — Each chart's aggregation groups by `graph dimensions + all dashboard filter dimensions`. Formula: `groupby_columns = graph.dimensions + dashboard.filters.dimensions`.
- **Per-chart aggregation** — Each chart definition drives its own aggregation pass. Graph A (month+brand) and Graph B (month+advertiser) produce separate sets of rows.
- **(dashboard_id, graph_id) as primary aggregation key** — Every `aggregated_data` row belongs to exactly one dashboard and one graph. No raw/unlinked rows.

### Aggregated Row Structure

Each row in `aggregated_data`:

```json
{
  "dashboard_id": "<uuid>",
  "graph_id": "<uuid>",
  "dims": {
    "year": "2024",
    "month": "1",
    "month_label": "Jan",
    "brand": "СБЕР БАНК",
    "targetaudience": "all 18+",
    "category": "УСЛУГИ БАНКОВ"
  },
  "metrics": {
    "tvr": 10.569
  }
}
```

- All dim values stored as **strings** (JSONB convention, frontend parses numbers explicitly).
- `year`, `month` (numeric sort key), and `month_label` (display) are stored as **separate dims** — enables multi-level X-axis (months under years) in Plotly.
- Filter dimensions (`targetaudience`, `category`) included in every row — enables client-side filtering without additional API calls.
- This structure scales to weekly/quarterly grouping: add `week`/`week_label` dims following the same pattern.

### Processing Config (Column Mapping)

Column-to-semantic-field mapping stored in `processing_configs.settings` with **typed mapping**:

```json
{
  "column_mapping": {
    "date":   {"semantic_name": "date",   "role": "dimension", "dtype": "date",   "format": "%d/%m/%Y", "separator": ";"},
    "TVR":    {"semantic_name": "tvr",    "role": "metric",   "dtype": "float",  "decimal_separator": ","},
    "brand":  {"semantic_name": "brand",  "role": "dimension", "dtype": "string"},
    "advertiser": {"semantic_name": "advertiser", "role": "dimension", "dtype": "string"},
    "targetaudience": {"semantic_name": "targetaudience", "role": "filter", "dtype": "string"},
    "category": {"semantic_name": "category", "role": "filter", "dtype": "string"}
  }
}
```

- CSV columns are semicolon-separated (`;`), UTF-8 with BOM.
- Date parsing: `DD/MM/YYYY` format explicitly declared in config.
- Float parsing: comma as decimal separator (`0,187805177`) handled generically via config — `str.replace(",", ".")` in Polars.
- The processing pipeline reads the config and applies conversions declaratively. Different dashboards with different CSV formats have different configs; the code doesn't change.
- **No new tables needed** — uses existing `processing_configs` table.

### Dashboard Configuration (Existing Tables Reused)

All config uses existing tables. **No new tables created.**

- **`graphs`** table — Chart definitions. Single JSONB `definition` column contains the full chart spec:
  ```json
  {
    "chart_type": "bar",
    "x_dim": "month",
    "y_metric": "tvr",
    "legend_dim": "brand",
    "orientation": "v",
    "title": "Monthly TVR by Brand"
  }
  ```
  - For chart-level dims: `groupby_dims: ["month", "brand"]`, `metrics: ["tvr"]`.
  - Existing `POST/GET /api/v1/dashboards/{id}/graphs` endpoints used.

- **`filters`** + **`dashboard_filters`** tables — Filter definitions linked to dashboards.
  - Existing `GET /api/v1/dashboards/{id}/filters` endpoint used.
  - Filter dims are `targetaudience` and `category`.

- **`dashboard_filter_values`** table — New table for pre-computed distinct filter values:
  ```sql
  dashboard_filter_values (
      id PK,
      dashboard_id FK → dashboards.id,
      filter_name,       -- e.g. "targetaudience", "category"
      filter_value       -- e.g. "all 18+", "УСЛУГИ БАНКОВ"
  )
  ```
  - Unique index on `(dashboard_id, filter_name, filter_value)`.
  - Populated during the upload pipeline aggregation pass (same transaction as aggregated data write).
  - Decouples filter reads from `aggregated_data` — fast indexed lookups instead of `SELECT DISTINCT` on JSONB.

### Filter Values Strategy

- **Stored in `dashboard_filter_values` table** — Pre-computed during upload, not derived at query time.
-理由: filter values are per-dashboard (not per-graph), DISTINCT on JSONB is slower than indexed table reads, atomic update with data upload.

### Frontend Rendering

- **Data fetching: separate API calls via TanStack Query** — Dashboard metadata, graphs, filters, and filter values each fetched by separate `useQuery` hooks:
  - `GET /api/v1/dashboards/{id}` — dashboard metadata
  - `GET /api/v1/dashboards/{id}/graphs` — graph definitions
  - `GET /api/v1/dashboards/{id}/filters` — filter definitions
  - `GET /api/v1/data/aggregated?dashboard_id={id}&graph_id={id}` — aggregated data per graph
  - `GET /api/v1/dashboards/{id}/filter-values` — distinct filter values
  - Each query caches and invalidates independently. After upload, multiple queries invalidate simultaneously.

- **Chart rendering: Hybrid** — `ChartRenderer` component reads `graphs.definition` JSONB, receives aggregated data + active filters, builds Plotly traces client-side. Component is chart-type-aware (bar, line, etc. via `chart_type` field). API returns generic data; frontend handles visualization.

- **Filter UI: MUI Checkbox groups** — Multi-select filter values via `<FormGroup>` + `<Checkbox>` from `@mui/material` (no extra libraries). User selects multiple values, charts update instantly.

- **Filtering behavior: Client-side** — All aggregated data loaded once. Filter selection filters rows in the browser: `rows.filter(row => selectedCategories.includes(row.dims.category))`. No additional API calls on filter change. Instant UX. TanStack Query caches data across navigation.

- **Multi-level X-axis** — Plotly X-axis shows months (`Jan`, `Feb`, ...) grouped by year (`2024`, `2025`, ...) using separate `year`/`month`/`month_label` dims.

### Service Layer Architecture

```
services/
├── data_service.py            # Raw data: CRUD, parse, basic transforms
├── aggregation_service.py      # NEW: Per-chart GROUP BY, Polars aggregation
└── file_processing_service.py  # Orchestrates: parse → transform → aggregate → save
```

- **`AggregationService`** is a new service — separate from `DataService`.
  - `DataService` handles raw data operations (loading, parsing, basic transforms).
  - `AggregationService` takes a Polars DataFrame + graph definitions + filter dim names → returns aggregated rows ready for `aggregated_data` insert.
  - Easily testable in isolation: input DataFrame + config → output rows.
- `file_processing_service.py` orchestrates the pipeline: parse CSV → transform columns (via processing_config) → aggregate (via AggregationService) → save to `aggregated_data` + `dashboard_filter_values`.
- Background worker (`data_worker.py`) calls this pipeline for async processing.

### Test Dashboard Specifics (Reference Implementation)

- **Dashboard name:** `test_media_dash`
- **Test data:** `data/test/test_data.csv.gz` — semicolon-separated, UTF-8 BOM, `DD/MM/YYYY` dates, comma decimal separator.
- **Required CSV columns:** `date`, `TVR`, `advertiser`, `brand`, `targetaudience`, `category`.
- **Chart 1:** Monthly TVR by Brand — Bar chart, X=month (grouped by year), Y=TVR, legend=brand. GROUP BY `month`, `brand` + filter dims.
- **Chart 2:** Monthly TVR by Advertiser — Bar chart, X=month (grouped by year), Y=TVR, legend=advertiser. GROUP BY `month`, `advertiser` + filter dims.
- **Filters:** `targetaudience` (single value "all 18+" in test data), `category` (multiple Russian-language values like "УСЛУГИ БАНКОВ").

## Specific Ideas

- The `month_label` dim should use English 3-letter abbreviations (`Jan`, `Feb`, ...) for chart axis labels, even though the rest of the UI may display Russian text.
- `year` dim stored as string `"2024"` to match JSONB string convention, not integer.
- The `dashboard_filter_values` table is the only new table in this phase — everything else reuses existing schema.
- Processing config `decimal_separator` and `date_format` fields make the pipeline generic — any CSV format can be handled by config, not code changes.

## Deferred Ideas

- **Week/quarter aggregation** — Same pattern as monthly (add `week`/`week_label` or `quarter`/`quarter_label` dims). Not part of this phase but the architecture supports it without changes.
- **Additional chart types** (line, pie, scatter) — `ChartRenderer` is designed to be extended via `chart_type` in `graphs.definition`. Not part of this phase.
- **Raw data retention** — Currently raw CSV is deleted after processing. If raw data storage is needed later, a new `raw_data` table would be a separate phase.
- **Filter value search/autocomplete** — For filters with very large value sets. Current checkbox group is sufficient for the test dashboard scale.

---

_Phase: 02-test-media-dashboard_
_Context gathered: 2026-06-01_
