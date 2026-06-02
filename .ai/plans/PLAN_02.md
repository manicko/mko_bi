---
phase: 02
title: "Test Dashboard (test_media_dash) Implementation"
domain: "Full-stack BI dashboard — backend aggregation pipeline, new DB table, API endpoint, frontend hooks and ChartRenderer"
created: "2026-06-01"
status: planned
depends_on:
  - "01-project-setup"
---

# PLAN_02: Test Dashboard (test_media_dash)

## Phase Goal

Implement a working test dashboard (`test_media_dash`) that ingests a semicolon-separated UTF-8 BOM CSV with DD/MM/YYYY dates and comma decimal separators, performs per-chart Polars GROUP BY aggregation (graph dimensions + dashboard filter dimensions), stores results in `aggregated_data` JSONB, exposes filter values via a new `dashboard_filter_values` table + API endpoint, and renders two bar charts with interactive MUI filters on the frontend.

## Architecture Decisions (LOCKED — from discuss-phase)

1. **Full pre-aggregation on upload** — Raw CSV never stored; all aggregation done via Polars at upload time.
2. **GROUP BY rule** — `groupby_columns = graph.dimensions + dashboard.filters.dimensions` (per chart).
3. **Per-chart aggregation** — Each graph definition drives its own aggregation pass.
4. **(dashboard_id, graph_id)** as primary aggregation key.
5. **All dim values stored as strings**; `year`, `month` (numeric sort key), `month_label` (display) as separate dims.
6. **`dashboard_filter_values` table** — New table `(id PK, dashboard_id FK, filter_name, filter_value)` with unique index on `(dashboard_id, filter_name, filter_value)`.
7. **AggregationService** — New service in `services/aggregation_service.py`.
8. **data_worker.py orchestrates** parse → transform → aggregate → save.
9. **CSV format** — semicolon-separated, UTF-8 BOM, DD/MM/YYYY dates, comma decimal separator.
10. **Frontend** — Separate TanStack Query calls per entity; ChartRenderer reads `graphs.definition` JSONB; MUI Checkbox groups for filters; client-side filtering.
11. **Test dashboard specifics** — Dashboard name: `test_media_dash`; Chart 1: Monthly TVR by Brand (bar); Chart 2: Monthly TVR by Advertiser (bar); Filters: `targetaudience`, `category`.

## Waves

### Wave 1: Database Layer (foundation — no deps)
- **TASK_001** — `dashboard_filter_values` DB model + Alembic migration
- **TASK_002** — `DashboardFilterValuesRepository`

### Wave 2: Backend Aggregation Pipeline (depends on Wave 1)
- **TASK_003** — `AggregationService` for per-chart Polars GROUP BY
- **TASK_004** — Wire CSV parsing config from processing_config into `data_worker` → `CSVLoader`
- **TASK_005** — Refactor `_store_aggregates` to per-chart aggregation with filter dims + filter values extraction

### Wave 3: API Layer (depends on Wave 2)
- **TASK_006** — Filter values API endpoint (`GET /dashboards/{id}/filter-values`) with FilterValuesService + router registration
- **TASK_009** — Seed `test_media_dash` DB records (dashboard, graphs, filters, processing_config)

### Wave 4: Frontend (depends on Wave 3)
- **TASK_007** — Frontend `useFilterValues` hook + DashboardFilters dynamic value integration
- **TASK_008** — `ChartRenderer` component (bar chart only; line/pie deferred)

### Wave 5: Verification (depends on Waves 1-4)
- **TASK_010** — Full phase verification (build, lint, mypy, smoke test upload → aggregate → render)

## Dependency Graph

```
Wave 1:
  TASK_001 (model+migration) ──→ TASK_002 (repo)
  TASK_001 ────────────────────→ TASK_005 (store filter values)

Wave 2:
  TASK_002 ──→ TASK_003 (AggregationService uses repo)
  TASK_004 ──→ TASK_005 (wires config → refactor uses it)
  TASK_003 ──→ TASK_005

Wave 3:
  TASK_002 ──→ TASK_006 (API uses repo via FilterValuesService)
  TASK_005 ──→ TASK_009 (pipeline ready before seeding)
  TASK_006 ──→ TASK_009

Wave 4:
  TASK_006 ──→ TASK_007 (frontend calls API)
  TASK_006 ──→ TASK_008 (frontend chart rendering)

Wave 5:
  TASK_001..009 ──→ TASK_010
```

## must_haves (goal-backward validation)

1. `dashboard_filter_values` table exists with correct schema + unique index.
2. `AggregationService.aggregate_for_dashboard()` performs per-chart `groupby().agg()` with `graph.dimensions + dashboard.filters.dimensions` GROUP BY.
3. All dim values stored as strings; `year`, `month`, `month_label` present as separate dims.
4. CSV parsing correctly handles semicolon separator, UTF-8 BOM, DD/MM/YYYY dates, comma decimal separator.
5. `_store_aggregates` replaced with per-chart aggregation (no row-by-row iteration).
6. After upload, `dashboard_filter_values` is repopulated with distinct values per filter.
7. `GET /dashboards/{id}/filter-values?filter_name={name}` returns distinct values via FilterValuesService.
8. Frontend `useFilterValues` hook fetches filter values from the new API endpoint (always called unconditionally; uses enabled flag).
9. `DashboardFilters` component uses dynamic values from API when `config.source === 'data'`.
10. `ChartRenderer` component renders bar charts (line/pie deferred).
11. `test_media_dash` exists in DB with 2 bar graphs + 2 filters bound + processing_config with CSV settings.
12. End-to-end: upload `test_data.csv.gz` → charts render with TVR data, filters show targetaudience/category values.
