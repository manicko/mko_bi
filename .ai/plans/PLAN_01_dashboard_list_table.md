---
wave: 2
depends_on:
  - PLAN_01_short_uuid.md
files_modified:
  - frontend/src/features/dashboards/ui/DashboardList.tsx
autonomous: true
---

# Plan 01.6: Dashboard List Table Conversion

## Goal
Convert the dashboard list from a Card grid to a DataGrid table with ID (short UUID) + Name columns, 25 rows/page default, sorting, and "No data" empty state per the locked decisions.

## must_haves
- [ ] DataGrid table with ID and Name columns
- [ ] ID column displays short UUID (first 8 chars) using `shortUuid`
- [ ] Default page size: 25 rows
- [ ] Page size options: 10, 25, 50
- [ ] Sorting enabled on all columns
- [ ] Empty state: table header + "No data" text when no dashboards
- [ ] Loading spinner shown during data fetch
- [ ] Row click or action to navigate to dashboard
- [ ] Removed Card grid layout completely

## Tasks

### Task 1: Rewrite DashboardList as DataGrid table
Replace the entire content of `frontend/src/features/dashboards/ui/DashboardList.tsx`. The current implementation uses `Card`, `Grid`, `CardContent` — replace with `DataGrid` from `@mui/x-data-grid`.

Key imports needed:
```tsx
import { DataGrid, GridColDef } from '@mui/x-data-grid'
import { Box, Typography, CircularProgress, Alert, Stack } from '@mui/material'
import { shortUuid } from '../../../shared/utils/shortUuid'
```

Columns definition:
```tsx
const columns: GridColDef[] = [
  {
    field: 'id',
    headerName: 'ID',
    width: 120,
    valueGetter: (value: string) => shortUuid(value),
  },
  { field: 'name', headerName: 'Name', flex: 1, minWidth: 200 },
]
```

DataGrid configuration:
```tsx
<DataGrid
  rows={dashboards ?? []}
  columns={columns}
  loading={isLoading}
  autoHeight
  pageSizeOptions={[10, 25, 50]}
  initialState={{
    pagination: { paginationModel: { pageSize: 25 } },
  }}
  slots={{
    noRowsOverlay: () => (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary">No data</Typography>
      </Box>
    ),
  }}
  sx={{
    '& .MuiDataGrid-cell:focus': { outline: 'none' },
  }}
/>
```

Keep the existing loading state (`CircularProgress`) and error state (`Alert`) wrappers. Remove all Card/Grid/CardContent imports and usage.

## Validation
- Verify table renders with ID and Name columns
- Verify ID shows 8-character short UUID
- Verify default page size is 25
- Verify empty state shows "No data" with table header visible
- Verify sorting works on both columns
- Verify loading spinner appears during fetch

## Acceptance Criteria
- [ ] Dashboard list uses DataGrid table (not cards)
- [ ] ID column shows short UUID
- [ ] Default page size is 25
- [ ] Empty state shows header + "No data"
- [ ] No Card/Grid/CardContent imports remain
