# 02 Test Dashboard (test_media_dash) - Research

**Researched:** 2026-06-01
**Domain:** Full-stack BI dashboard implementation (FastAPI + React + Polars + PostgreSQL/JSONB)
**Confidence:** HIGH

---

## Summary

This research investigates the implementation of Phase 02: a test dashboard named `test_media_dash` with two bar charts (Monthly TVR by Brand, Monthly TVR by Advertiser) and two filters (targetaudience, category). The phase reuses the entire existing data pipeline — upload, parse, transform, aggregate, store, retrieve, render — which is already implemented in the codebase. The key work involves: (1) creating dashboard/graph/filter DB records for test_media_dash, (2) a Polars-based aggregation that GROUPs BY graph dimensions + dashboard filter dimensions, (3) a `dashboard_filter_values` lookup table, and (4) frontend ChartRenderer and filter components.

The existing codebase is ~80% ready. The upload pipeline (`POST /upload/{dashboard_id}` -> `file_processing_service.py` -> `data_worker.py` -> `StorageManager`) is fully implemented. The data retrieval endpoint (`GET /data/aggregated`) exists with JSONB filter support. The frontend already has a `DashboardView` with `PlotlyChart`, `BarChart`, `LineChart`, and `DashboardFilters` components. The primary new work is in the aggregation logic (per-chart Polars GROUP BY), the `dashboard_filter_values` table, and the wiring needed to bring test_media_dash to life.

**Primary recommendation:** Reuse the existing pipeline end-to-end. The `AggregationService` is a thin orchestration layer on top of existing `CSVLoader`, `apply_transformations`, and `StorageManager`. The `_store_aggregates` function in `data_worker.py` needs refactoring to perform per-chart aggregation (currently it does row-level iteration without GROUP BY). No new frontend components are needed — ChartRenderer reads from `graphs.definition` JSONB and shows Plotly traces; `DashboardFilters` uses MUI Checkbox groups with values fetched from a new filter-values API.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (existing) | REST API | Already in use, async-native |
| Polars | (existing) | Data processing | Already in use, pandas forbidden |
| SQLAlchemy 2.0 async | (existing) | ORM + Core | Already in use, asyncpg driver |
| Pydantic v2 | (existing) | Validation | Already in use everywhere |
| Alembic | (existing) | DB migrations | Already in use for schema versioning |
| React 18+TypeScript | (existing) | UI | Already in use |
| TanStack Query | (existing) | Server state | Already in use for data fetching |
| MUI | (existing) | Component library | Already in use for filters/layout |
| Plotly.js (react-plotly.js) | (existing) | Charts | Already in use |
| StrEnum | (std library) | Constants | Required by project convention |

### Supporting

| Library | Purpose | When to Use |
|---------|---------|-------------|
| `data/storage/manager.py` | Save/upsert aggregated data to PostgreSQL JSONB | For persisting aggregation results |
| `data/processing/transformations.py` | Apply filters, sorting, dtype casts, computed fields | In worker pipeline after CSV load |
| `data/processing/aggregate_transforms.py` | GROUP BY aggregations, YoY, share | For Polars `groupby().agg()` operations |
| `data/processing/filter_transforms.py` | Row filtering with operators | For dtype casting, filter application |
| `workers/data_worker.py` | Background CSV processing | Called from task queue after upload |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom aggregation SQL | Polars GROUP BY | SQL would bypass Polars; decisions mandate Polars |
| pandas | Polars | Forbidden by project rules (SPEC.md) |
| Manual chart config | Plotly JSON from `graphs.definition` | Client-side rendering is already implemented |
| Separate filter value queries | `dashboard_filter_values` table | New table needed for filter checkbox population |

**Installation:** No new packages needed. All libraries are already installed.

---

## Architecture Patterns

### Recommended Project Structure

The new files for this phase follow the existing structure:

```
src/mkobi/
├── db/
│   ├── models/
│   │   └── dashboard_filter_values.py    # NEW - dashboard_filter_values table
│   └── repositories/
│       └── dashboard_filter_values_repo.py  # NEW - repo for filter values
├── services/
│   ├── aggregation_service.py            # NEW - per-chart Polars GROUP BY
│   └── file_processing_service.py        # EXISTING - orchestrates pipeline
├── api/
│   └── routes/
│       └── filter_values.py              # NEW - GET /filter-values endpoint
├── workers/
│   └── data_worker.py                    # EXISTING - calls _store_aggregates
└── data/
    └── processing/
        └── (existing modules)            # Reuse transformations, aggregate_transforms

frontend/src/
├── features/
│   └── dashboards/
│       ├── api/
│       │   └── dashboardApi.ts           # EXISTING - add filterValues query
│       └── ui/
│           ├── DashboardView.tsx         # EXISTING - already wires charts+filters
│           ├── DashboardFilters.tsx      # EXISTING - MUI checkbox/select filters
│           └── charts/
│               ├── BarChart.tsx          # EXISTING - bar chart wrapper
│               ├── ChartRenderer.tsx     # NEW - reads graphs.definition JSONB
│               └── PlotlyChart.tsx       # EXISTING - generic Plotly.js wrapper
└── shared/
    └── types/
        ├── api.types.ts                  # ADD new filter value types
        └── enums.ts                      # EXISTING - add FilterValueSource if needed
```

### Pattern 1: Full Pre-Aggregation Pipeline (Locked Decision)

**What:** During upload, Polars reads the entire CSV, transforms columns, and generates all aggregated rows. Raw CSV is never stored persistently.

**When to use:** Always, for every upload to any dashboard.

**Existing code path:**
1. `POST /api/v1/upload/{dashboard_id}` → `upload.py:upload_file_endpoint()`
2. File streamed to temp dir (8KB chunks via `aiofiles`)
3. `data_service.py:process_upload()` → `file_processing_service.py:process_upload_with_session()`
4. File moved to final path after DB commit
5. Background worker enqueued: `enqueue_processing_job()` → `data_worker.py:process_csv_background()`
6. Worker: `CSVLoader.load_csv()` → `apply_transformations()` → `calculate_aggregations()` → `_store_aggregates()`

**Key gap:** The current `_store_aggregates()` in `data_worker.py` (lines 278-411) iterates row-by-row over the raw DataFrame and all graphs, splitting each row into dims/metrics per graph. This does NOT perform the per-chart GROUP BY aggregation required by Phase 02.

**Recommendation:** Create a new `AggregationService` that, given a Polars DataFrame, graph definitions, and dashboard filter definitions, produces per-chart aggregated DataFrames. The aggregation GROUP BY columns = graph.dimensions + dashboard.filters.dimensions. Each unique combination becomes one row with aggregated metric values.

```python
# Conceptual AggregationService (locked decision: full pre-aggregation)
async def aggregate_for_dashboard(
    df: pl.DataFrame,
    graphs: list[Graph],
    dashboard_filters: list[Filter],
) -> list[dict]:
    """
    For each graph:
    1. groupby_columns = graph.dimensions + dashboard.filters.dimensions
    2. metrics = graph.metric columns (e.g., TVR)
    3. aggregation = sum (or as defined in processing_config)
    4. Produces rows like: {dashboard_id, graph_id, dims: {brand: "X", targetaudience: "Y", category: "Z"}, metrics: {TVR_sum: 1.23}}
    """
    results = []
    dashboard_filter_dims = [f.name for f in dashboard_filters]
    
    for graph in graphs:
        groupby_cols = graph.dimensions + dashboard_filter_dims
        
        # Validate groupby cols exist in DataFrame
        valid_groupby = [c for c in groupby_cols if c in df.columns]
        valid_metrics = [c for c in graph.metrics if c in df.columns]
        
        if not valid_groupby or not valid_metrics:
            continue
        
        # Use existing aggregate_transforms.calculate_aggregations()
        agg_df = calculate_aggregations(
            df=df,
            groupby=valid_groupby,
            aggregations=[
                {"column": m, "function": "sum", "alias": f"{m}_sum"}
                for m in valid_metrics
            ],
        )
        
        # Add to results with dashboard_id, graph_id
        for row in agg_df.to_dicts():
            dims = {k: str(v) for k, v in row.items() if k in groupby_cols}
            metrics = {k: v for k, v in row.items() if k not in groupby_cols}
            results.append({
                "dashboard_id": graph.dashboard_id,
                "graph_id": str(graph.id),
                "dims": dims,
                "metrics": metrics,
            })
    
    return results
```

Source: Based on existing `aggregate_transforms.py:_apply_groupby_aggregations()` pattern + `storage/manager.py:save_aggregates()` for `StorageManager` integration.

### Pattern 2: dashboard_filter_values Table (Locked Decision)

**What:** A new table storing distinct filter values extracted from aggregated data, used to populate filter UI checkboxes.

**Schema (recommended):**

```python
class DashboardFilterValue(Base):
    __tablename__ = "dashboard_filter_values"
    __table_args__ = (
        Index(
            "uq_dashboard_filter_values",
            "dashboard_id", "filter_name", "filter_value",
            unique=True,
        ),
        Index("idx_dashboard_filter_values_lookup", "dashboard_id", "filter_name"),
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dashboard_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("dashboards.id", ondelete="CASCADE"))
    filter_name: Mapped[str] = mapped_column(String(255))
    filter_value: Mapped[str] = mapped_column(String(1024))
```

**When to use:** After every successful aggregation (full recalculation), repopulate filter values. When filters are applied on the frontend, query this table for available values.

**Repository method:**
```python
class DashboardFilterValuesRepository:
    async def save_filter_values(self, dashboard_id, filter_name, values, db)
    async def get_filter_values(self, dashboard_id, filter_name, db) -> list[str]
    async def clear_dashboard_values(self, dashboard_id, db)
```

### Pattern 3: Per-Chart API Response (Locked Decision)

**What:** The frontend makes separate TanStack Query calls for dashboard metadata, graphs, filters, filter values, and aggregated data per graph.

**Existing endpoint pattern** (from `data.py:get_aggregated_data_endpoint()`):
```
GET /api/v1/data/aggregated?dashboard_id={id}&filters={json}
→ Returns { graphs: [{ graph_id, type, name, data: [...] }] }
```

**New endpoint needed:**
```
GET /api/v1/dashboards/{id}/filter-values?filter_name={name}
→ Returns { filter_name, values: ["value1", "value2", ...] }
```

**Frontend data fetching pattern** (from existing `dashboardApi.ts`):
```typescript
// Already exists for dashboard + aggregated data
useDashboard(id)         // GET /dashboards/{id}
useAggregatedData(id, filters)  // GET /data/aggregated

// New hook needed
useFilterValues(dashboardId, filterName)
  // GET /dashboards/{id}/filter-values?filter_name={name}
  // Returns values for MUI checkbox groups
```

### Anti-Patterns to Avoid

- **Raw data retention:** Do not store the raw CSV data in the database. Only aggregated data goes to `aggregated_data`. The temp file is deleted after processing (already implemented in `data_worker.py`).
- **Grouping only by graph dimensions:** Must include dashboard filter dimensions in GROUP BY. If a chart groups by `brand` but the dashboard has `targetaudience` and `category` filters, the GROUP BY must be `brand + targetaudience + category`. This ensures every filter value combination has a row for client-side filtering.
- **Row-by-row aggregation:** The current `_store_aggregates` iterates raw rows. For Phase 02, use Polars `groupby().agg()` for proper aggregation.
- **Raw SQL via f-strings:** Use SQLAlchemy Core or ORM exclusively. No f-string SQL anywhere.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| CSV parsing | Custom parser | `data/loaders/loader.py:CSVLoader` | Already supports .csv.gz, UTF-8 BOM, semicolon separator, type transforms |
| Data aggregation SQL | Raw SQL GROUP BY | `data/processing/aggregate_transforms.py:calculate_aggregations()` | Existing Polars-based aggregation with sum/mean/count/min/max/etc. |
| JSONB Upsert | Custom UPSERT logic | `data/storage/manager.py:StorageManager.save_aggregates()` | Existing, handles chunked insert/upsert with key normalization |
| Chart rendering | Custom D3/Canvas | `features/dashboards/ui/charts/PlotlyChart.tsx` + `BarChart.tsx` | Already wraps react-plotly.js |
| Filter component | Custom dropdown | `features/dashboards/ui/DashboardFilters.tsx` | Already has select/multiselect/range/date MUI filters |
| File upload streaming | Read entire file | `aiofiles` with 8KB chunks | Already implemented in `upload.py` |
| Processing status polling | WebSocket | `GET /upload/status/{task_id}` polling | Already implemented frontend polling pattern |
| Dashboard access control | Custom permission logic | `core/permissions.py:check_dashboard_access()` | Already checks dashboard_access table + admin bypass |

**Key insight:** The existing pipeline is ~80% complete. The primary gap is the per-chart Polars GROUP BY in the worker and the `dashboard_filter_values` API. Everything else — upload, parsing, storage, retrieval, rendering — is already wired.

---

## Common Pitfalls

### Pitfall 1: Missing Filter Dimensions in GROUP BY

**What goes wrong:** Charts aggregate only by `graph.dimensions` (e.g., `brand`), omitting dashboard filter dimensions (e.g., `targetaudience`, `category`). Client-side filtering then has missing rows — selecting a filter value shows no data because those combinations don't exist.

**Why it happens:** Natural tendency to group only by what the chart visualizes.

**How to use:** Always compute `groupby_columns = graph.dimensions + dashboard.filters.dimensions`. Both sets of columns must be present in every aggregated row.

**Warning signs:** Filter selection causes charts to show "No data available."

### Pitfall 2: Numeric Dim Values in JSONB

**What goes wrong:** Storing `year` or `month` as integers in the `dims` JSONB while `month_label` is stored separately. If the worker doesn't explicitly create `year`, `month`, and `month_label` as separate dim fields, the frontend may fail to sort or display correctly.

**Why it happens:** Polars naturally stores numeric columns as int/float in `to_dicts()`.

**How to avoid:** Convert all dim values to strings when building aggregated rows. Add explicit `year` (int), `month` (int), and `month_label` (str) columns to dims when processing date data.

**Warning signs:** Charts fail to sort months correctly; filter checkboxes show raw numbers instead of labels.

### Pitfall 3: Not Repopulating Filter Values After Upload

**What goes wrong:** After a new CSV upload recalculates all aggregates, the `dashboard_filter_values` table still has old stale values. Filter checkboxes show values from the previous dataset.

**Why it happens:** Filter values are extracted from data but not refreshed on every upload.

**How to avoid:** In the worker's `_process_csv_file_async()`, after storing aggregates, extract distinct dimension values for each dashboard filter and upsert them into `dashboard_filter_values`.

**Warning signs:** Filter checkboxes show stale values after upload; new values from the uploaded CSV don't appear.

### Pitfall 4: Date Parsing with DD/MM/YYYY Format

**What goes wrong:** The test CSV uses dates like `04/01/2024` (DD/MM/YYYY) with comma decimal separators (e.g., `0,187805177`). The Polars CSV reader defaults to US date format (MM/DD/YYYY) and period decimal separator.

**Why it happens:** Polars `read_csv()` defaults differ from the RFC 3999 BOM CSV format specified.

**How to avoid:** The existing `CSVLoader._read_csv()` uses `csv.gz` reading with `pl.read_csv()`. Must pass `separator=";"`, enable date parsing, and handle the comma decimal separator. The `processing_configs.json` settings should drive these parameters declaratively.

**Warning signs:** `TVR` values like `0,187805177` parsed as strings; date parsing fails silently or swaps day/month.

### Pitfall 5: Frontend Filter-Dashboard Data Mismatch

**What goes wrong:** `DashboardFilters.tsx` currently derives filter details from `dashboard.config.filters` (hardcoded in Dashboard JSONB config). For Phase 02, filter values must come from the `filter-values` API endpoint, which reads actual aggregated data. If the frontend uses only `dashboard.config`, the filter checkboxes won't reflect actual data.

**Why it happens:** The existing `DashboardFilters.tsx` reads `filter.config.options` from the dashboard config JSONB. This is a static list, not populated from data.

**How to avoid:** Add a new `filter-values` API endpoint and a `useFilterValues` TanStack Query hook. Modify `DashboardFilters` to use the dynamic values from the API when `config.source === 'data'`.

**Warning signs:** Filter checkboxes show hardcoded values from config instead of actual values from the uploaded data.

---

## Code Examples

### Test CSV Structure (Verified)

The test data file `data/test/test_data.csv.gz` has the following structure:

```
Separator: semicolon (;)
Encoding: UTF-8 BOM (utf-8-sig)
Date format: DD/MM/YYYY (e.g., 04/01/2024)
Decimal separator: comma (e.g., 0,187805177)

Columns: date; targetaudience; category; advertiser; brand; adduration;
         addistribution; adtype; adPosition; adPrimeTime; tvCompany; TVR; StandTVR

Sample row:
  04/01/2024;all 18+;УСЛУГИ БАНКОВ;СОВКОМБАНК;СОВКОМБАНК;20;
  Сетевой;Ролик;Средний;Вне прайм-тайм;ЧЕ;0,187805177;0,187805177
```

### Processing Config for test_media_dash

The `processing_configs` table row for `test_media_dash` needs settings that drive the CSV parsing and transformation:

```json
{
  "separator": ";",
  "encoding": "utf-8-sig",
  "date_format": "%d/%m/%Y",
  "decimal_separator": ",",
  "column_types": {
    "date": "date",
    "TVR": "float",
    "StandTVR": "float",
    "advertiser": "str",
    "brand": "str",
    "targetaudience": "str",
    "category": "str"
  },
  "date_column": "date",
  "computed_fields": [
    {
      "name": "year",
      "expr": "date.year()"
    },
    {
      "name": "month",
      "expr": "date.month()"
    },
    {
      "name": "month_label",
      "expr": "date.strftime('%b %Y')"
    }
  ],
  "renames": {
    "TVR": "tvr"
  }
}
```

### Per-Chart Aggregation (Polars Pattern)

```python
# Source: Based on data/processing/aggregate_transforms.py:_apply_groupby_aggregations()
import polars as pl

def aggregate_chart_data(
    df: pl.DataFrame,
    graph_dimensions: list[str],
    filter_dimensions: list[str],
    metric_column: str,
) -> pl.DataFrame:
    """
    Aggregate data for a single chart.
    
    GROUP BY = graph dimensions + all dashboard filter dimensions.
    Metric = SUM of the metric column.
    
    Example for 'Monthly TVR by Brand':
      graph_dimensions = ['year', 'month', 'month_label', 'brand']
      filter_dimensions = ['targetaudience', 'category']
      metric_column = 'TVR'
      
    GROUP BY: year, month, month_label, brand, targetaudience, category
    """
    all_groupby = [d for d in graph_dimensions + filter_dimensions if d in df.columns]
    
    if not all_groupby:
        raise ValueError("No valid groupby columns found in DataFrame")
    
    if metric_column not in df.columns:
        raise ValueError(f"Metric column '{metric_column}' not found in DataFrame")
    
    return df.group_by(all_groupby).agg([
        pl.col(metric_column).sum().alias(f"{metric_column}_sum"),
    ])


def build_aggregated_records(
    agg_df: pl.DataFrame,
    graph_id: str,
    dashboard_id: str,
    filter_dimensions: list[str],
    graph_dimensions: list[str],
) -> list[dict]:
    """
    Convert aggregated Polars DataFrame to list of records for JSONB storage.
    
    Each record: {dashboard_id, graph_id, dims: {all str}, metrics: {values}}
    """
    records = []
    graph_dim_set = set(graph_dimensions)
    filter_dim_set = set(filter_dimensions)
    all_dim_set = graph_dim_set | filter_dim_set
    
    for row in agg_df.to_dicts():
        # All dim values stored as strings (locked decision)
        dims = {}
        for col in graph_dimensions:
            if col in row:
                dims[col] = str(row[col])
        for col in filter_dimensions:
            if col in row:
                dims[col] = str(row[col])
        
        # Metrics = non-dim columns
        metrics = {k: v for k, v in row.items() if k not in all_dim_set}
        
        records.append({
            "dashboard_id": dashboard_id,
            "graph_id": graph_id,
            "dims": dims,
            "metrics": metrics,
        })
    
    return records
```

### Date Parsing for Test CSV

```python
# The test CSV has dates like "04/01/2024" with UTF-8 BOM and semicolon separator.
# Polars read_csv needs explicit parameters:
df = pl.read_csv(
    file_path,
    separator=";",
    encoding="utf-8-sig",
    try_parse_dates=False,  # Parse manually to control format
)

# Then parse dates with the correct DD/MM/YYYY format:
df = df.with_columns(
    pl.col("date").str.strptime(pl.Date, "%d/%m/%Y").alias("date"),
)

# Handle comma decimal separator for TVR:
df = df.with_columns(
    pl.col("TVR").str.replace(",", ".").cast(pl.Float64).alias("TVR"),
)
```

### GraphQL-style Filter Values Endpoint

```python
# Source: Following patterns from api/routes/dashboards_filters.py
# New file: api/routes/filter_values.py

router = APIRouter(tags=["dashboards"])

@router.get(
    "/{dashboard_id}/filter-values",
    response_model=dict,
    status_code=200,
    summary="Get filter values for dashboard",
    description="Returns distinct values for a dashboard filter from aggregated data.",
)
async def get_filter_values_endpoint(
    dashboard_id: UUID,
    filter_name: str = Query(..., description="Filter/dimension name"),
    current_user: UserRead = Depends(require_dashboard_read_access),
    db: AsyncSession = Depends(get_db_dependency),
    filter_values_repo: Any = Depends(get_filter_values_repository),
) -> dict[str, Any]:
    """Get distinct values for a dashboard filter."""
    try:
        values = await filter_values_repo.get_filter_values(
            dashboard_id=dashboard_id, filter_name=filter_name, db=db
        )
        return {"filter_name": filter_name, "values": values}
    except Exception as e:
        logger.error("Error getting filter values for dashboard %s: %s", dashboard_id, e)
        raise HTTPException(status_code=500, detail="Error getting filter values")
```

### Frontend ChartRenderer (reads graphs.definition JSONB)

```typescript
// New file: frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx
// Source: Based on existing BarChart.tsx + PlotlyChart.tsx patterns
// Locked decision: Separate API calls per graph via TanStack Query

import { BarChart } from './BarChart'
import { LineChart } from './LineChart'
import { PieChart } from './PieChart'
import type { GraphDataWithConfig } from '../../../../shared/types/api.types'

interface ChartRendererProps {
  graph: GraphDataWithConfig
}

export function ChartRenderer({ graph }: ChartRendererProps) {
  // Extract x/y from graph layout or first data point keys
  const data = graph.data || []
  
  switch (graph.type) {
    case 'bar':
      return (
        <BarChart
          data={{
            x: data.map((d) => d[Object.keys(d)[0]]),
            y: data.map((d) => d[Object.keys(d)[1]] || 0),
          }}
          title={graph.name}
        />
      )
    case 'line':
      return <LineChart data={{ x: [], y: [] }} title={graph.name} />
    case 'pie':
      return <PieChart data={{ labels: [], values: [] }} title={graph.name} />
    default:
      return <BarChart data={{ x: [], y: [] }} title={graph.name} />
  }
}
```

### Frontend DashboardView Integration

```typescript
// Source: Based on existing features/dashboards/ui/DashboardView.tsx
// The existing DashboardView already uses TanStack Query for:
//   useDashboard(id) → dashboard metadata + config
//   useAggregatedData(id, filters) → chart data
// 
// For Phase 02, the frontend already works. The filter UI in DashboardFilters.tsx 
// needs to fetch values from the new filter-values endpoint:
//
// New hook to add:
export function useFilterValues(dashboardId: string, filterName: string) {
  const accessToken = getToken()
  return useQuery({
    queryKey: ['filterValues', dashboardId, filterName],
    queryFn: () => dashboardApi.getFilterValues(dashboardId, filterName),
    enabled: !!dashboardId && !!filterName && !!accessToken,
  })
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|-------------|-----------------|-------------|--------|
| Row-by-row iteration in `_store_aggregates` | Per-chart `groupby().agg()` (Phase 02) | This phase | Enables filterable aggregated data |
| Static filter options in dashboard config | Dynamic filter values from `dashboard_filter_values` table | This phase | Filters reflect actual data |
| Manual Plotly trace construction | ChartRenderer reads `graphs.definition` JSONB | This phase | Flexible chart type rendering |
| Single all-dashboard aggregation | Per-chart aggregation with filter dims | This phase | Each chart optimized independently |
| `processing_configs` settings as opaque JSON | Declarative column mapping with typed conversions | Already implemented | Config-driven pipeline |

**Deprecated/outdated:**

- The current `_store_aggregates()` row-by-row iteration in `data_worker.py` (lines 278-411) needs to be replaced with the per-chart GROUP BY approach. Keep `StorageManager` as-is for persistence.
- `DashboardFilters.tsx` deriving filter values from `dashboard.config.filters[].options` should be augmented with dynamic values from the `filter-values` API for filters with `source: "data"`.

---

## Open Questions

1. **CSV parsing config source:** The processing config for test_media_dash must specify `separator=";"`, `encoding="utf-8-sig"`, and handle comma decimal separator. Currently, `CSVLoader._read_csv()` accepts a `config` dict but the worker's `_process_csv_file_async()` doesn't pass CSV parsing config from `processing_config_dict` to `CSVLoader`. This needs to be wired.

   What we know: `ProcessingConfig` model has a dict-based `settings` field. The worker passes `processing_config_dict` to `_process_csv_file_async()`. The code path is:
   ```
   _process_csv_file_async() 
     → loader = CSVLoader()  # No config passed!
     → df = loader.load_csv(file_path)  # Uses default config
     → apply_transformations(df, filters=..., groupby=...)  # Config partially used
   ```
   What's unclear: How the CSV separator/encoding/decimal settings flow from `processing_config_dict` to `CSVLoader`. This gap must be filled.

   **Recommendation:** Pass CSV parsing options (separator, encoding) from settings to `CSVLoader` via its `config` parameter, similar to how `LoaderConfig` already supports `required_columns`, `column_types`, etc.

2. **Filter value extraction timing:** Should `dashboard_filter_values` be populated during the worker's aggregation step (inside `_process_csv_file_async`) or by a separate post-aggregation step?

   What we know: The worker processes CSV and stores aggregates in a single async function.
   **Recommendation:** Add a step in `_process_csv_file_async()` after `_store_aggregates()` to extract and store filter values. This keeps the worker as a single atomic operation: parse → transform → aggregate → store aggregates + filter values → cleanup.

3. **Date dimension generation in aggregation:** The test CSV has a `date` column, but the charts need `year`, `month`, and `month_label` as separate dims. Should these be computed before or during aggregation?

   What we know: `computed_fields` in `apply_transformations()` can add computed columns.
   **Recommendation:** Add `year`, `month`, `month_label` as computed fields via `processing_config` before aggregation. The `computed_fields` feature already exists in `apply_transformations()` → `_add_computed_fields()`.

4. **Whether frontend ChartRenderer is needed or DashboardView suffices:**
   What we know: `DashboardView.tsx` already iterates `aggregatedData.graphs` and renders `<PlotlyChart>` for each. `BarChart.tsx` wraps PlotlyChart with bar type.
   **Recommendation:** The existing `DashboardView` already renders charts. `ChartRenderer` is a thin adapter if more complex chart-type switching is needed. For 2 bar charts, `BarChart.tsx` used directly is sufficient. If `graphs.definition` JSONB is meant to drive trace construction, build ChartRenderer to parse the definition and construct Plotly data arrays.

---

## Sources

### Primary (HIGH confidence)

- `src/mkobi/db/models/aggregated_data.py` — Existing AggregatedData model with JSONB dims + metrics, unique index on `(dashboard_id, graph_id, dims::text)`
- `src/mkobi/db/models/graphs.py` — Existing Graph model with `type`, `dimensions[]`, `metrics[]`, `config` JSONB
- `src/mkobi/db/models/filters.py` — Existing Filter model with `name`, `type`, `config` JSONB, many-to-many via `dashboard_filters` table
- `src/mkobi/db/models/dashboard.py` — Existing Dashboard model with relationships to graphs, filters, aggregated_data
- `src/mkobi/db/models/processing_configs.py` — Existing ProcessingConfig dashboard_id PK + settings JSONB
- `src/mkobi/services/file_processing.py` — Existing upload pipeline with validation, log creation, job enqueue
- `src/mkobi/workers/data_worker.py` — Existing background worker: CSV load → transform → aggregate → store
- `src/mkobi/data/loaders/loader.py` — Existing CSVLoader with gzip support, type transforms, lazy loading
- `src/mkobi/data/processing/aggregate_transforms.py` — Existing Polars GROUP BY with AGG_FUNC_MAP dispatch
- `src/mkobi/data/processing/filter_transforms.py` — Existing row filtering, computed fields, dtype casting
- `src/mkobi/data/storage/manager.py` — Existing StorageManager with bulk upsert, JSONB key normalization
- `src/mkobi/services/data_service.py` — Existing DataService with `process_upload()`, `get_aggregated_data()`
- `src/mkobi/api/routes/upload.py` — Existing `POST /upload/{dashboard_id}`, streaming file upload
- `src/mkobi/api/routes/data.py` — Existing `GET /data/aggregated` with dashboard_id, graph_id, filters
- `src/mkobi/api/routes/graphs.py` — Existing graph CRUD with dashboard access control
- `src/mkobi/api/routes/dashboards_graphs.py` — Existing `POST/GET /{dashboard_id}/graphs`
- `src/mkobi/api/routes/dashboards_filters.py` — Existing `POST/DELETE/GET /{dashboard_id}/filters` (bind/unbind/list)
- `src/mkobi/services/dashboard_service.py` — Existing DashboardService with create, get, CRUD
- `src/mkobi/services/graph_service.py` — Existing GraphService with repository pattern
- `src/mkobi/interfaces/repository_interfaces.py` — All repository interface contracts
- `src/mkobi/models/data.py` — Pydantic models: UploadResponse, AggregatedDataResponse, GraphDataResponse, ProcessingConfig
- `src/mkobi/models/enums.py` — All StrEnum classes: GraphType, FilterType, AggregationFunctionEnum, etc.
- `src/mkobi/models/graph.py` — GraphCreate, GraphRead, GraphUpdate Pydantic models
- `data/test/test_data.csv.gz` — Test data: semicolon-separated, UTF-8 BOM, DD/MM/YYYY dates, comma decimals, columns: date/targetaudience/category/advertiser/brand/TVR/StandTVR

### Frontend Sources (HIGH confidence)

- `frontend/src/features/dashboards/ui/DashboardView.tsx` — Main dashboard page with charts + filters
- `frontend/src/features/dashboards/ui/DashboardFilters.tsx` — MUI filter component (select/multiselect/range/date)
- `frontend/src/features/dashboards/ui/charts/PlotlyChart.tsx` — Generic Plotly.js wrapper
- `frontend/src/features/dashboards/ui/charts/BarChart.tsx` — Bar chart wrapper
- `frontend/src/features/dashboards/ui/charts/LineChart.tsx` — Line chart wrapper
- `frontend/src/features/dashboards/ui/charts/PieChart.tsx` — Pie chart wrapper
- `frontend/src/features/dashboards/api/dashboardApi.ts` — TanStack Query hooks: useDashboard, useAggregatedData
- `frontend/src/shared/types/api.types.ts` — TypeScript interfaces for API types
- `frontend/src/shared/types/enums.ts` — Frontend enum constants matching backend StrEnum
- `frontend/src/app/routes.tsx` — Route definitions including `/dashboard/:id`

### Migration Sources (HIGH confidence)

- `alembic/versions/a1b2c3d4e5f6_add_force_password_change_to_user.py` — Recent migration pattern: `op.add_column()` with `server_default`
- `alembic/versions/64730d3d3446_merge_branches_for_force_password_.py` — Merge migration pattern

### Secondary (MEDIUM confidence)

- `docs/SPEC.md` — System specification v3.2 with all design decisions documented
- `src/mkobi/services/processing_config_service.py` — ProcessingConfigService for config CRUD
- `src/mkobi/db/repositories/aggregated_data_repo.py` — AggregatedDataRepository with JSONB filter queries
- `src/mkobi/db/repositories/graph_repo.py` — GraphRepository with get_by_dashboard_id
- `src/mkobi/db/repositories/filter_repo.py` — FilterRepository with get_by_name
- `src/mkobi/db/repositories/dashboard_filter_repo.py` — DashboardFilterRepository for binding

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Standard stack | HIGH | All libraries already in use, verified by reading imports |
| Backend architecture | HIGH | Existing pipeline fully mapped by reading all source files |
| Data processing | HIGH | Polars aggregation patterns exist in codebase; GROUP BY is well-understood |
| Frontend architecture | HIGH | All components exist; ChartRenderer is a thin adapter |
| DB models | HIGH | All existing models read; new table follows same patterns |
| Migration strategy | HIGH | Existing migration pattern is clear and simple |
| CSV parsing config | MEDIUM | Gap identified: how CSV settings flow from processing_config to CSVLoader |
| Filter values API | MEDIUM | New endpoint needed; pattern follows existing filter endpoints |

**Research date:** 2026-06-01
**Valid until:** 2026-07-01 (30 days — stable codebase, no fast-moving dependencies)
