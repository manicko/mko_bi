---
id: extend-graphs-filters
domain: guides
tags:
  - guide
  - graphs
  - filters
  - extensibility
  - charts
  - howto
related:
  - dashboards-api
  - processing-api
  - schema-core
  - data-flow
  - create-dashboard
---

## Purpose

This guide walks developers through the process of adding new graph types and extending filter capabilities in the mkobi BI Dashboard System. It covers the full extension workflow — from backend StrEnum changes to frontend component wiring — for both graphs (e.g., scatter, heatmap) and filters (e.g., search, toggle). It assumes you have read the [Dashboards API](../02-dashboards/dashboards-api.md) and [SPEC.md](../SPEC.md) overview.

## Prerequisites

To follow this guide, you should:

- Be familiar with the codebase structure (FastAPI backend, React + TypeScript frontend, Polars data processing)
- Understand the Clean Architecture layers (API → Service → Repository) and Feature-Sliced Design on the frontend
- Have read the [Dashboards API](../02-dashboards/dashboards-api.md) reference for field-level detail on graph and filter config structures
- Have read the [Core Schema](../09-database/schema-core.md) documentation for the `graphs` and `filters` table structure

## Quick Reference

The following table maps the current graph types to their backend enum values, frontend components, and Plotly trace types:

| Graph Type | Backend (`GraphType`) | Frontend Component | Plotly Trace Type | Aggregation |
| ---------- | --------------------- | ------------------ | ----------------- | ----------- |
| Bar        | `bar`                 | `BarChart.tsx`     | `bar`             | GROUP BY    |
| Line       | `line`                | `LineChart.tsx`    | `scatter` (mode: lines) | GROUP BY |
| Pie        | `pie`                 | `PieChart.tsx`     | `pie`             | GROUP BY    |
| Table      | `table`               | `TableChart.tsx`   | *(none, HTML table)* | Raw rows |

And filter types:

| Filter Type | Backend (`FilterType`) | MUI Control | Data Source Options |
| ----------- | ---------------------- | ----------- | ------------------- |
| Select      | `select`               | `Select` dropdown | `options` (static) or `data` (dynamic from aggregated dims) |
| Multiselect | `multiselect`         | `Select` multiple + `Chip` | `options` (static) or `data` (dynamic) |
| Range       | `range`                | `Slider`    | `min`/`max` from config |
| Date        | `date`                 | `TextField` type=date | Single date string |

## Conceptual Overview

The graph/filter extension system follows a single end-to-end pipeline:

```
Backend StrEnum (Python)
    │
    ▼
PostgreSQL ENUM type (DB-level validation)
    │
    ▼
JSONB config stored in `graphs` / `filters` tables
    │
    ▼
API response serialized to frontend
    │
    ▼
Frontend TypeScript const object (mirrors backend enum)
    │
    ├── Graphs → ChartRenderer dispatches to Plotly component
    │
    └── Filters → FilterField switch dispatches to MUI control
```

**Key design principle:** Both `GraphType` and `FilterType` use Python `StrEnum`, where the enum value is a plain string (e.g., `"bar"`, `"select"`). These strings are stored in PostgreSQL `ENUM` types, which means adding a new type requires both a code change (the StrEnum) and a database migration (`ALTER TYPE ... ADD VALUE`). On the frontend, `const` objects with `as const` assertions mirror the backend enums to maintain type safety without runtime overhead.

The `ChartRenderer` component is a pass-through dispatcher: the backend constructs Plotly data (traces + layout) as JSON in the `aggregated_data` table, and the frontend renders it without type-specific dispatch logic. Individual chart components (e.g., `BarChart.tsx`, `LineChart.tsx`) are used when the frontend needs to set Plotly trace defaults, but the primary rendering path is backend-constructed data flowing through `PlotlyChart`.

The `DashboardFilters` component uses an explicit `switch (filter.type)` statement in the `FilterField` subcomponent. Each filter type maps to a specific MUI control. Unhandled types silently render `null` — this is the default case.

## Extending Graph Types

### Step 1: Add the Value to `GraphType` StrEnum

Edit `src/mkobi/models/enums.py` and add the new value to the `GraphType` class:

```python
class GraphType(StrEnum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"
    SCATTER = "scatter"   # <-- new value
```

The string value (`"scatter"`) must exactly match the value used in the frontend TypeScript enum and the PostgreSQL ENUM type. Use lowercase kebab-case consistently.

### Step 2: Add a Database Migration

Since graph types are enforced at the database level via a PostgreSQL `ENUM` type named `graph_type`, you must add the new value with an `ALTER TYPE` statement in an Alembic migration:

```python
# alembic/versions/XXXX_add_scatter_graph_type.py
def upgrade():
    op.execute("ALTER TYPE graph_type ADD VALUE 'scatter'")

def downgrade():
    # PostgreSQL does not support removing ENUM values directly.
    # A downgrade requires recreating the type or leaving the value in place.
    pass
```

**Critical:** Without this migration, the backend will accept the new enum value but every database `INSERT` or `UPDATE` using it will fail with an invalid enum literal error. See [Processing API](../03-processing/processing-api.md) for details on the processing pipeline that writes to the `graphs` table.

### Step 3: Add the Frontend Enum Value

Edit `frontend/src/shared/types/enums.ts` and add the new value to the `GraphType` const object:

```typescript
export const GraphType = {
  BAR: 'bar',
  LINE: 'line',
  PIE: 'pie',
  TABLE: 'table',
  SCATTER: 'scatter',
} as const

export type GraphType = (typeof GraphType)[keyof typeof GraphType]
```

Ensure the string value matches the backend exactly. Any casing mismatch will cause the admin UI form to silently fail on validation.

### Step 4: Create the Frontend Chart Component

Create a new component file under `frontend/src/features/dashboards/ui/charts/`, for example `ScatterChart.tsx`. The component should wrap `PlotlyChart` and set Plotly trace defaults appropriate for the new type:

```typescript
// frontend/src/features/dashboards/ui/charts/ScatterChart.tsx
import { PlotlyChart } from './PlotlyChart'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface ScatterChartProps {
  data: PlotlyData
  layout?: PlotlyLayout
  title?: string
}

export function ScatterChart({ data, layout, title }: ScatterChartProps) {
  const chartLayout: Partial<PlotlyLayout> = {
    title: { text: title || '' },
    ...layout,
  }

  return <PlotlyChart data={{ ...data, type: 'scatter', mode: 'markers' } as PlotlyData} layout={chartLayout as PlotlyLayout} />
}
```

**Note on ChartRenderer:** The `ChartRenderer` component currently passes data through to `PlotlyChart` without type-specific dispatch. If your new chart type requires frontend-side trace configuration (beyond what the backend provides), you should add a dispatch case in `ChartRenderer`. For most Plotly trace types, the backend-constructed data is sufficient and no `ChartRenderer` changes are needed.

### Step 5: Update Admin UI Forms

In the Admin UI dashboard editor, update the graph type selector to include the new value. This ensures administrators can select the new type when creating or editing graphs. The form field should reference the `GraphType` const object to stay in sync.

### Step 6: Update Backend Data Construction (if needed)

If the new graph type requires different data shapes orPlotly trace properties, update the backend aggregation service that constructs Plotly data. See [Data Pipeline Implications](#data-pipeline-implications) below for guidance on when this is necessary.

## Extending Filter Types

### Step 1: Add the Value to `FilterType` StrEnum

Edit `src/mkobi/models/enums.py` and add the new value to the `FilterType` class:

```python
class FilterType(StrEnum):
    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"
    SEARCH = "search"       # <-- new value
```

### Step 2: Add a Database Migration

Same as for graph types, add an Alembic migration for the `filter_type` PostgreSQL ENUM:

```python
def upgrade():
    op.execute("ALTER TYPE filter_type ADD VALUE 'search'")
```

### Step 3: Add the Frontend Enum Value

Edit `frontend/src/shared/types/enums.ts`:

```typescript
export const FilterType = {
  SELECT: 'select',
  MULTISELECT: 'multiselect',
  RANGE: 'range',
  DATE: 'date',
  SEARCH: 'search',
} as const

export type FilterType = (typeof FilterType)[keyof typeof FilterType]
```

### Step 4: Add the Filter Field Case in `DashboardFilters`

Edit `src/features/dashboards/ui/DashboardFilters.tsx` and add a new `case` in the `FilterField` switch statement (around the `switch (filter.type)` block):

```typescript
case 'search':
  return (
    <TextField
      fullWidth
      size="small"
      label={filter.name}
      value={(value as string) || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={`Search ${filter.name}...`}
    />
  )
```

**Critical:** If you omit the new case, the filter will silently render `null` (the `default` return in the switch). Always verify your new case is correctly matched by the filter type string.

### Step 5: Update Admin UI Forms

Update the filter type selector in the Admin UI to include the new value, referencing the `FilterType` const object.

## Data Pipeline Implications

Adding new types affects the data pipeline differently depending on the type of extension:

### New Graph Types — When Aggregation Changes Are Needed

The aggregation pipeline in `AggregationService` produces Plotly trace data based on `GROUP BY` operations over dimension columns. Whether a new graph type requires pipeline changes depends on its data shape:

**Graph types that need GROUP BY aggregation (same as existing):**
Bar, line, pie graphs all share the same aggregation pattern — the pipeline groups by dimension columns and computes metric aggregates (sum, mean, etc.). Adding a graph type like `"scatter"` where x and y values come from the same row (not grouped) requires a different data shape: an array of `{ x, y }` pairs rather than grouped dimension values.

If your new graph type needs grouped data in a new format, you only need to add a data-construction function that transforms the existing grouped Polars DataFrame into the Plotly trace format. No changes to the aggregation itself are needed.

**Graph types that need raw row access:**
Table charts already use raw row access (no GROUP BY). Heatmaps typically need 2D matrix data. If your new graph type requires row-level data, add a raw data pass-through in the construction step.

**Summary:** The aggregation pipeline's output (grouped Polars DataFrames) is the single source of truth. New graph types add *construction functions* that transform this output into different Plotly trace shapes. You rarely need to modify the aggregation itself.

### New Filter Types — No Aggregation Changes

Filter types do not affect the aggregation pipeline. They affect how users select dimension values to filter by. The key consideration is the `config.source` field:

- **`source: "options"` (static):** Filter options are defined in the filter's `config.options` JSON. No data pipeline changes needed.
- **`source: "data"` (dynamic):** Filter options are extracted from the `aggregated_data.dims` JSONB column after each upload. No code changes needed for new filter types — as long as the filter's `config.field` matches a dimension name in your data, dynamic values are populated automatically.

The only code change for new filter types is the frontend `FilterField` case (Step 4 in the filter extension section above). The backend handles all filter types uniformly through the `FilterType` StrEnum and Pydantic validation.

## Appendix

### Example 1: Adding a Scatter Graph Type (Simple)

This example adds a `"scatter"` graph type that renders individual data points without GROUP BY aggregation.

**1. Backend StrEnum** (`src/mkobi/models/enums.py`):

```python
class GraphType(StrEnum):
    # ... existing values
    SCATTER = "scatter"
```

**2. Database migration** (`alembic/versions/XXXX_add_scatter.py`):

```python
"""Add scatter to graph_type enum."""

revision = "XXXX"
down_revision = "YYYY"

def upgrade():
    op.execute("ALTER TYPE graph_type ADD VALUE 'scatter'")

def downgrade():
    pass  # PostgreSQL does not support removing ENUM values
```

**3. Frontend enum** (`frontend/src/shared/types/enums.ts`):

```typescript
export const GraphType = {
  // ... existing values
  SCATTER: 'scatter',
} as const
```

**4. Frontend component** (`frontend/src/features/dashboards/ui/charts/ScatterChart.tsx`):

```typescript
import { PlotlyChart } from './PlotlyChart'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface ScatterChartProps {
  data: PlotlyData
  layout?: PlotlyLayout
  title?: string
}

export function ScatterChart({ data, layout, title }: ScatterChartProps) {
  const chartLayout: Partial<PlotlyLayout> = {
    title: { text: title || '' },
    ...layout,
  }

  return (
    <PlotlyChart
      data={{ ...data, type: 'scatter', mode: 'markers' } as PlotlyData}
      layout={chartLayout as PlotlyLayout}
    />
  )
}
```

**5. Backend data construction** — In the graph data construction step, pass x/y arrays as raw data rather than grouped aggregates:

```python
# Pseudocode for scatter data construction
df = aggregated_raw_data  # Polars DataFrame with metric columns
trace = {
    "x": df["revenue"].to_list(),
    "y": df["cost"].to_list(),
    "type": "scatter",
    "mode": "markers",
}
```

### Example 2: Adding a Heatmap Graph Type (Medium Complexity)

Heatmaps require a 2D matrix of values and two dimension axes. The data shape differs from bar/line/pie graphs because it needs cross-tabulated aggregates.

**1–3. StrEnum + migration + frontend enum** — Same pattern as Example 1 (`HEATMAP = "heatmap"`).

**4. Frontend component** (`HeatmapChart.tsx`):

The heatmap component sets the Plotly trace type to `"heatmap"` and provides axis labels:

```typescript
import { PlotlyChart } from './PlotlyChart'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface HeatmapChartProps {
  data: PlotlyData
  layout?: PlotlyLayout
  title?: string
}

export function HeatmapChart({ data, layout, title }: HeatmapChartProps) {
  const chartLayout: Partial<PlotlyLayout> = {
    title: { text: title || '' },
    xaxis: { title: { text: data.xLabel || '' } },
    yaxis: { title: { text: data.yLabel || '' } },
    ...layout,
  }

  return <PlotlyChart data={{ ...data, type: 'heatmap' } as PlotlyData} layout={chartLayout as PlotlyLayout} />
}
```

**5. Backend data construction** — Heatmaps need a pivoted/cross-tabulated data shape. In the aggregation service, add a construction step that produces `z` (2D value matrix), `x` (column dimension values), and `y` (row dimension values):

```python
# Pseudocode for heatmap data construction
pivot = df.pivot(
    values="revenue",
    index="region",
    columns="product",
    aggregate_function="sum",
)
trace = {
    "x": pivot.columns[1:],  # column headers (excluding index)
    "y": pivot["region"].to_list(),
    "z": pivot.drop("region").to_numpy().tolist(),
    "type": "heatmap",
}
```

No changes to the aggregation pipeline itself are needed — the pivot operation transforms the existing grouped data into the heatmap shape.

### Example 3: Adding a Search Filter Type (Complex)

This example adds a `"search"` filter type that provides a text input for free-text filtering of dimension values. This is common when dimension value lists are long (e.g., product names).

**1. Backend StrEnum** (`src/mkobi/models/enums.py`):

```python
class FilterType(StrEnum):
    # ... existing values
    SEARCH = "search"
```

**2. Database migration**:

```python
def upgrade():
    op.execute("ALTER TYPE filter_type ADD VALUE 'search'")
```

**3. Frontend enum** (`frontend/src/shared/types/enums.ts`):

```typescript
export const FilterType = {
  // ... existing values
  SEARCH: 'search',
} as const
```

**4. FilterField case** (`frontend/src/features/dashboards/ui/DashboardFilters.tsx`):

Add the search case to the `FilterField` switch statement. Unlike select-based filters, search accepts a single string and filters dimension values using substring matching:

```typescript
case 'search': {
  return (
    <TextField
      fullWidth
      size="small"
      label={filter.name}
      value={(value as string) || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={`Search ${filter.name}...`}
    />
  )
}
```

**5. Backend handling** — The backend filter application logic needs to handle search filters differently from exact-match filters. In the filter application step, add a case for search that uses SQL `LIKE` or `ILIKE` on the dimension value:

```python
# Pseudocode in filter/processing service
if filter.type == FilterType.SEARCH:
    search_term = filter_values.get(filter.name, "")
    if search_term:
        df = df.filter(
            pl.col(filter.config["field"]).str.contains(search_term, literal=True)
        )
```

No changes to the aggregation pipeline are needed. The search filter operates on the already-aggregated data, filtering rows where a dimension value contains the search term.

## Cross-Links

- [Dashboards API](../02-dashboards/dashboards-api.md) — CRUD for dashboards, graphs, filters, and access management; field-level detail on graph and filter config JSONB structures
- [Processing API](../03-processing/processing-api.md) — Upload, processing pipeline, and aggregated data endpoints; full data flow documentation
- [Core Schema](../09-database/schema-core.md) — Table definitions for `graphs` and `filters` tables, including PostgreSQL ENUM types and JSONB columns
- [Processing Schema](../09-database/schema-processing.md) — Table definitions for `aggregated_data`, `processing_configs`, and `processing_logs`
- [Data Flow](../00-overview/data-flow.md) — End-to-end upload-to-display pipeline
- [Create Dashboard](./create-dashboard.md) — Step-by-step guide for creating a new dashboard from scratch (uses the same extension types documented here)
