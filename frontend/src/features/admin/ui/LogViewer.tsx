import { useState } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import {
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  Stack,
  Alert,
} from '@mui/material'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { getLogs } from '../api/adminApi'
import { useQuery } from '@tanstack/react-query'
import type { LogFilters } from '../../../shared/types/api.types'

const statusOptions = ['started', 'uploaded', 'processing', 'success', 'failed', 'completed']

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 100 },
  { field: 'dashboard_name', headerName: 'Dashboard', width: 200 },
  {
    field: 'status',
    headerName: 'Status',
    width: 130,
    renderCell: (params) => {
      const status = params.value as string
      const color = status === 'success' || status === 'completed' ? 'success'
        : status === 'failed' ? 'error'
        : 'warning'
      return <Chip label={status} color={color} size="small" />
    },
  },
  { field: 'message', headerName: 'Message', width: 300 },
  { field: 'started_at', headerName: 'Started', width: 180 },
  { field: 'finished_at', headerName: 'Finished', width: 180 },
]

export function LogViewer() {
  const [filters, setFilters] = useState<LogFilters>({})
  const [appliedFilters, setAppliedFilters] = useState<LogFilters>({})

  const { data: logs = [], isLoading, error, isError } = useQuery({
    queryKey: ['admin', 'logs', appliedFilters],
    queryFn: () => getLogs(appliedFilters),
  })

  const handleApplyFilters = () => {
    setAppliedFilters(filters)
  }

  const handleClearFilters = () => {
    setFilters({})
    setAppliedFilters({})
  }

  const rows = logs.map((log) => ({
    id: log.id.slice(0, 8),
    dashboard_name: log.dashboard_name || 'N/A',
    status: log.status,
    message: log.message || '',
    started_at: log.started_at ? new Date(log.started_at).toLocaleString() : '',
    finished_at: log.finished_at ? new Date(log.finished_at).toLocaleString() : '',
  }))

  return (
    <Box>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <Stack direction="row" spacing={2} sx={{ mb: 3, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Dashboard</InputLabel>
            <Select
              value={filters.dashboard_id || ''}
              label="Dashboard"
              onChange={(e) => setFilters({ ...filters, dashboard_id: e.target.value || undefined })}
            >
              <MenuItem value="">All</MenuItem>
              {/* TODO: Load dashboards for filter */}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status Filter</InputLabel>
            <Select
              value={filters.status_filter || ''}
              label="Status Filter"
              onChange={(e) => setFilters({ ...filters, status_filter: e.target.value || undefined })}
            >
              <MenuItem value="">All</MenuItem>
              {statusOptions.map((status) => (
                <MenuItem key={status} value={status}>{status}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <DatePicker
            label="Date From"
            value={filters.date_from ? new Date(filters.date_from) : null}
            onChange={(date) => setFilters({ ...filters, date_from: date ? date.toISOString().split('T')[0] : undefined })}
            slotProps={{ textField: { size: 'small' } }}
          />

          <DatePicker
            label="Date To"
            value={filters.date_to ? new Date(filters.date_to) : null}
            onChange={(date) => setFilters({ ...filters, date_to: date ? date.toISOString().split('T')[0] : undefined })}
            slotProps={{ textField: { size: 'small' } }}
          />

          <Button variant="contained" onClick={handleApplyFilters}>
            Apply
          </Button>
          <Button onClick={handleClearFilters}>Clear</Button>
        </Stack>
      </LocalizationProvider>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load logs: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      )}

      <DataGrid
        rows={rows}
        columns={columns}
        loading={isLoading}
        autoHeight
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 10 } },
        }}
      />
    </Box>
  )
}
