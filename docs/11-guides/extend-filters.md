---
id: extend-filters
domain: guides
tags:
  - guide
  - filters
  - extensibility
  - howto
related:
  - dashboards-api
  - processing-api
  - schema-core
  - data-flow
  - extend-graphs
  - create-dashboard
---

## Purpose

This guide walks developers through the process of extending filter capabilities in the mkobi BI Dashboard System. It covers the full extension workflow — from backend StrEnum changes to frontend `FilterField` wiring — for filter types such as search, toggle, or any custom MUI control. It assumes you have read the [Dashboards API](../02-dashboards/dashboards-api.md) and [SPEC.md](../SPEC.md) overview.

For graph extension, see the companion guide: [Extend Graphs](./extend-graphs.md).

## Prerequisites

To follow this guide, you should:

- Be familiar with the codebase structure (FastAPI backend, React + TypeScript frontend, Polars data processing)
- Understand the Clean Architecture layers (API → Service → Repository) and Feature-Sliced Design on the frontend
- Have read the [Dashboards API](../02-dashboards/dashboards-api.md) reference for field-level detail on filter config structures
- Have read the [Core Schema](../09-database/schema-core.md) documentation for the `filters` table structure

## Quick Reference

The following table maps the current filter types to their backend enum values, MUI controls, and value sources:

| Filter Type | Backend (`FilterType`) | MUI Control | Value Source |
| ----------- | ---------------------- | ----------- | ------------ |
| Select      | `select`               | `Select` dropdown | `config.options` (static) or `source: "data"` (dynamic from `dashboard_filter_values` table) |
| Multiselect | `multiselect`         | `Select` multiple + `Chip` | Same as select |
| Range       | `range`                | `Slider`    | `config.min`/`config.max` |
| Date        | `date`                 | `TextField` type=date | Single date string |

## Conceptual Overview

The filter extension system follows this end-to-end pipeline:

```
Backend StrEnum (Python)
    │
    ▼
PostgreSQL ENUM type (DB-level validation)
    │
    ▼
JSONB config stored in `filters` table
    │
    ▼
API response serialized to frontend
    │
    ▼
Frontend TypeScript const object (mirrors backend enum)
    │
    ▼
FilterField switch dispatches to MUI control
```

**Key design principle:** `FilterType` uses Python `StrEnum`, where the enum value is a plain string (e.g., `"select"`). These strings are stored in PostgreSQL `ENUM` types, which means adding a new type requires both a code change (the StrEnum) and a database migration (`ALTER TYPE ... ADD VALUE`). On the frontend, a `const` object with `as const` assertion mirrors the backend enum to maintain type safety without runtime overhead.

**How DashboardFilters works:** The `DashboardFilters` component uses an explicit `switch (filter.type)` statement in the `FilterField` subcomponent. Each filter type maps to a specific MUI control. Unhandled types silently render `null` — this is the `default` case. Filter values are fetched dynamically from `GET /api/v1/dashboards/{id}/filter-values` when `config.source === "data"`, or from static `config.options` when `config.source === "dims"`.

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

Add an Alembic migration for the `filter_type` PostgreSQL ENUM:

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

Edit `frontend/src/features/dashboards/ui/DashboardFilters.tsx` and add a new `case` in the `FilterField` switch statement:

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

### Step 5: Update Backend Filter Application (if needed)

If the new filter type requires backend-side filtering logic (e.g., substring search), update the filter/processing service. The backend applies filters through parameterized SQL queries against the `aggregated_data.dims` JSONB column using PostgreSQL JSONB containment operators (`@>`). For a search filter, you would add a case that uses `ILIKE` on the dimension value.

### Step 6: Update Admin UI Forms

Update the filter type selector in the Admin UI to include the new value, referencing the `FilterType` const object.

## Data Pipeline Implications

Filter types do not affect the aggregation pipeline. They affect how users select dimension values to filter by. The key consideration is the `config.source` field:

- **`source: "dims"` (static):** Filter options are defined in the filter's `config.options` JSON array. No data pipeline changes needed.
- **`source: "data"` (dynamic):** Filter options are extracted from the `dashboard_filter_values` table after each upload. No code changes needed for new filter types — as long as the filter's `config.field` matches a dimension name in your data, dynamic values are populated automatically during CSV processing.

The only code change for new filter types is the frontend `FilterField` case (Step 4 above). The backend handles all filter types uniformly through the `FilterType` StrEnum and Pydantic validation.

## Appendix

### Example: Adding a Search Filter Type

This example adds a `"search"` filter type that provides a text input for free-text filtering of dimension values.

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

Add the search case to the `FilterField` switch statement:

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

**5. Backend handling** — The backend filter application logic needs to handle search filters differently from exact-match filters. In the data retrieval step, add a case for search that uses SQL `ILIKE` on the dimension value in the `aggregated_data.dims` JSONB column:

```python
# Pseudocode in data service filter application
if filter.type == FilterType.SEARCH:
    search_term = filter_values.get(filter.name, "")
    if search_term:
        # Filter aggregated_data where dims->>'field_name' ILIKE '%search_term%'
        ...
```

No changes to the aggregation pipeline are needed. The search filter operates on the already-aggregated data, filtering rows where a dimension value contains the search term.

## Cross-Links

- [Dashboards API](../02-dashboards/dashboards-api.md) — CRUD for dashboards, graphs, filters, and access management; field-level detail on filter config JSONB structures
- [Processing API](../03-processing/processing-api.md) — Upload, processing pipeline, and aggregated data endpoints; full data flow documentation
- [Core Schema](../09-database/schema-core.md) — Table definitions for `filters` table, including PostgreSQL ENUM types and JSONB columns
- [Processing Schema](../09-database/schema-processing.md) — Table definitions for `aggregated_data`, `dashboard_filter_values`, `processing_configs`, and `processing_logs`
- [Data Flow](../00-overview/data-flow.md) — End-to-end upload-to-display pipeline
- [Extend Graphs](./extend-graphs.md) — How to add new graph types (companion guide)
- [Create Dashboard](./create-dashboard.md) — Step-by-step guide for creating a new dashboard from scratch
