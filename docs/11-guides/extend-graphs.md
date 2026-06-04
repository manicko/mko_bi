---
id: extend-graphs
domain: guides
tags:
  - guide
  - graphs
  - extensibility
  - charts
  - howto
related:
  - dashboards-api
  - processing-api
  - schema-core
  - data-flow
  - extend-filters
  - create-dashboard
---

## Purpose

This guide walks developers through the process of adding new graph types in the mkobi BI Dashboard System. It covers the full extension workflow — from backend StrEnum changes to frontend `ChartRenderer` wiring — for graph types such as scatter, heatmap, or any custom Plotly trace. It assumes you have read the [Dashboards API](../02-dashboards/dashboards-api.md) and [SPEC.md](../SPEC.md) overview.

For filter extension, see the companion guide: [Extend Filters](./extend-filters.md).

## Prerequisites

To follow this guide, you should:

- Be familiar with the codebase structure (FastAPI backend, React + TypeScript frontend, Polars data processing)
- Understand the Clean Architecture layers (API → Service → Repository) and Feature-Sliced Design on the frontend
- Have read the [Dashboards API](../02-dashboards/dashboards-api.md) reference for field-level detail on graph config structures
- Have read the [Core Schema](../09-database/schema-core.md) documentation for the `graphs` table structure

## Quick Reference

The following table maps the current graph types to their backend enum values, frontend components, and Plotly trace types:

| Graph Type | Backend (`GraphType`) | Frontend Component | Plotly Trace Type | Data Shape |
| ---------- | --------------------- | ------------------ | ----------------- | ---------- |
| Bar        | `bar`                 | `BarChart.tsx`     | `bar`             | GROUP BY   |
| Line       | `line`                | `LineChart.tsx`    | `scatter` (mode: lines) | GROUP BY |
| Pie        | `pie`                 | `PieChart.tsx`     | `pie`             | GROUP BY   |
| Table      | `table`               | `TableChart.tsx`   | *(none, HTML table)* | Flat rows |

## Conceptual Overview

The graph extension system follows this end-to-end pipeline:

```
Backend StrEnum (Python)
    │
    ▼
PostgreSQL ENUM type (DB-level validation)
    │
    ▼
JSONB config stored in `graphs` table
    │
    ▼
API response serialized to frontend
    │
    ▼
Frontend TypeScript const object (mirrors backend enum)
    │
    ▼
ChartRenderer converts flat {dims, metrics} records → Plotly traces
```

**Key design principle:** `GraphType` uses Python `StrEnum`, where the enum value is a plain string (e.g., `"bar"`). These strings are stored in PostgreSQL `ENUM` types, which means adding a new type requires both a code change (the StrEnum) and a database migration (`ALTER TYPE ... ADD VALUE`). On the frontend, a `const` object with `as const` assertion mirrors the backend enum to maintain type safety without runtime overhead.

**How ChartRenderer works:** The backend does NOT construct Plotly trace data. Instead, the `AggregationService` produces flat records with `{dims: {...}, metrics: {...}}` and stores them in the `aggregated_data` table. The frontend `ChartRenderer` component receives these flat records and converts them to Plotly `Data[]` format. It has type-specific logic: for `bar` charts it sets `orientation` from config; for `pie` charts it extracts labels/values from dims/metrics. If data already arrives in Plotly format (has `x` and `y` fields), it passes through as-is.

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

**Critical:** Without this migration, the backend will accept the new enum value but every database `INSERT` or `UPDATE` using it will fail with an invalid enum literal error.

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

### Step 4: Update ChartRenderer for the New Type

The `ChartRenderer` component (`frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx`) converts flat `{dims, metrics}` records into Plotly `Data[]`. If your new graph type requires a different Plotly trace configuration, add a case in `convertToPlotlyData()`:

```typescript
// Inside convertToPlotlyData, handle the new type
if (graph.type === 'scatter') {
  return [{
    x: (graph.data as Record<string, unknown>[]).map(row => Number(row[metricCol] ?? 0)),
    y: (graph.data as Record<string, unknown>[]).map(row => Number(row['y_metric'] ?? 0)),
    type: 'scatter',
    mode: 'markers',
  } as unknown as Data]
}
```

If your new type can reuse the existing flat-to-Plotly conversion logic (e.g., a horizontal bar chart using `orientation: 'h'`), you may only need to set the orientation in the graph's `config` JSON — no `ChartRenderer` changes required.

### Step 5: Create a Standalone Chart Component (Optional)

If the new graph type needs its own reusable component (e.g., for direct use in admin preview or custom layouts), create one under `frontend/src/features/dashboards/ui/charts/`:

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

### Step 6: Update Admin UI Forms

In the Admin UI dashboard editor, update the graph type selector to include the new value. The form field should reference the `GraphType` const object to stay in sync.

## Data Pipeline Implications

The aggregation pipeline in `AggregationService` produces flat records with `{dims: {dimension_name: value}, metrics: {metric_name: value}}` for each graph. The GROUP BY columns are `graph.dimensions + dashboard.filter.names` (filter names from bound dashboard filters). All dimension values are converted to strings.

**Graph types that work with existing conversion:**
Bar, line, and pie graphs all work with the default `ChartRenderer.convertToPlotlyData()` logic, which extracts x values from the first dimension column and y values from the first metric column. If your new type can use this same data shape (just with different Plotly trace properties), you only need to add a case in `ChartRenderer`.

**Graph types that need raw row access:**
Table charts display flat records directly without Plotly conversion. If your new graph type needs row-level data (e.g., scatter plots where x and y come from different metric columns), add a conversion case in `ChartRenderer` that maps metric columns to Plotly x/y arrays.

**Summary:** The aggregation pipeline's output (flat `{dims, metrics}` records) is the single source of truth. New graph types add *conversion functions* in `ChartRenderer` that transform this output into different Plotly trace shapes. You rarely need to modify the aggregation itself.

## Appendix

### Example 1: Adding a Scatter Graph Type (Simple)

This example adds a `"scatter"` graph type that renders individual data points. The scatter plot uses two metric columns (x_metric, y_metric) from the aggregated data.

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

**4. ChartRenderer conversion** (`frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx`):

Add a case in `convertToPlotlyData` for scatter:

```typescript
if (graph.type === 'scatter') {
  const rows = graph.data as unknown as Record<string, unknown>[]
  const xCol = config.x || 'x'
  const yCol = config.y || 'y'
  return [{
    x: rows.map(row => Number(row[xCol] ?? 0)),
    y: rows.map(row => Number(row[yCol] ?? 0)),
    type: 'scatter',
    mode: 'markers',
  } as unknown as Data]
}
```

**5. Backend data construction** — No changes needed. The `AggregationService` produces flat `{dims, metrics}` records. The graph's `config.x` and `config.y` fields specify which metric columns to use for the scatter plot axes.

### Example 2: Adding a Heatmap Graph Type (Medium Complexity)

Heatmaps require a 2D matrix of values and two dimension axes. The data shape differs from bar/line/pie graphs because it needs cross-tabulated aggregates.

**1–3. StrEnum + migration + frontend enum** — Same pattern as Example 1 (`HEATMAP = "heatmap"`).

**4. ChartRenderer conversion** — Heatmaps need a pivoted data shape. Add a conversion case that produces `z` (2D value matrix), `x` (column dimension values), and `y` (row dimension values):

```typescript
if (graph.type === 'heatmap') {
  // Expects data pre-pivoted by the backend or uses first two dims + first metric
  const rows = graph.data as unknown as Record<string, unknown>[]
  // Pivot logic: group by dim1 (y) and dim2 (x), aggregate metric (z)
  // ... pivot implementation ...
  return [{
    x: xLabels,
    y: yLabels,
    z: zMatrix,
    type: 'heatmap',
  } as unknown as Data]
}
```

**5. Backend data construction** — If the heatmap requires a different aggregation shape, add a construction function in `AggregationService` that produces pre-pivoted records. The default GROUP BY produces flat records; heatmaps need an additional pivot step.

## Cross-Links

- [Dashboards API](../02-dashboards/dashboards-api.md) — CRUD for dashboards, graphs, filters, and access management; field-level detail on graph config JSONB structures
- [Processing API](../03-processing/processing-api.md) — Upload, processing pipeline, and aggregated data endpoints; full data flow documentation
- [Core Schema](../09-database/schema-core.md) — Table definitions for `graphs` table, including PostgreSQL ENUM types and JSONB columns
- [Processing Schema](../09-database/schema-processing.md) — Table definitions for `aggregated_data`, `processing_configs`, and `processing_logs`
- [Data Flow](../00-overview/data-flow.md) — End-to-end upload-to-display pipeline
- [Extend Filters](./extend-filters.md) — How to add new filter types (companion guide)
- [Create Dashboard](./create-dashboard.md) — Step-by-step guide for creating a new dashboard from scratch
