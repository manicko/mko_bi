import { useNavigate } from 'react-router-dom'
import { DataGrid, GridToolbar } from '@mui/x-data-grid'
import type { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import { Stack, Typography, CircularProgress, Alert } from '@mui/material'
import { useMyDashboards } from '../api/dashboardApi'
import { shortUuid } from '../../../shared/utils/shortUuid'
import { formatDateForGrid } from '../../../shared/utils/formatDate'
import type { DashboardSummary } from '../../../shared/types/api.types'

export function DashboardList() {
  const navigate = useNavigate()
  const { data: dashboards, isLoading, error } = useMyDashboards()

  if (isLoading) {
    return (
      <Stack sx={{ alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Stack>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboards. Please try again.
      </Alert>
    )
  }

  const columns: GridColDef<DashboardSummary>[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 120,
      sortable: true,
      renderCell: (params: GridRenderCellParams<DashboardSummary>) =>
        shortUuid(params.row.id),
    },
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 200,
      sortable: true,
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 180,
      sortable: true,
      renderCell: (params: GridRenderCellParams<DashboardSummary>) =>
        formatDateForGrid(params.row.created_at),
    },
  ]

  if (!dashboards || dashboards.length === 0) {
    return (
      <Stack sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          My Dashboards
        </Typography>
        <DataGrid
          rows={[]}
          columns={columns}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
          slots={{ toolbar: GridToolbar }}
          slotProps={{
            toolbar: { showQuickFilter: true },
          }}
          sx={{ mt: 2 }}
        />
        <Alert severity="info" sx={{ mt: 2 }}>
          No dashboards available. Contact an administrator to get access.
        </Alert>
      </Stack>
    )
  }

  return (
    <Stack sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        My Dashboards
      </Typography>
      <DataGrid
        rows={dashboards}
        columns={columns}
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        onRowClick={(params: { row: DashboardSummary }) =>
          void navigate(`/dashboard/${params.row.id}`)
        }
        slots={{ toolbar: GridToolbar }}
        slotProps={{
          toolbar: { showQuickFilter: true },
        }}
        sx={{ mt: 2, cursor: 'pointer' }}
      />
    </Stack>
  )
}