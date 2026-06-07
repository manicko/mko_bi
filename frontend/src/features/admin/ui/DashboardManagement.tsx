import { useState, useMemo, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { DataGrid, GridActionsCellItem, type GridRenderCellParams } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, ManageAccounts as AccessIcon } from '@mui/icons-material'
import { getDashboardsAdmin, createDashboard, updateDashboard, deleteDashboard } from '../api/adminApi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog'
import { ConfirmDialog } from '../../../shared/components/ConfirmDialog'
import { shortUuid } from '../../../shared/utils/shortUuid'
import { toast } from 'react-hot-toast'
import type { DashboardAdmin } from '../../../shared/types/api.types'
import { extractApiError } from '../../../shared/api/errorHandler'
import { ErrorCode } from '../../../shared/types/enums'
import { getErrorMessage } from '../../../shared/api/errorMessages'
import { adminErrorMessages } from '../model/errorMessages'
import { createDashboardSchema, updateDashboardSchema, type CreateDashboardFormData, type UpdateDashboardFormData } from '../../../shared/types/formSchemas'

export function DashboardManagement() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedDashboard, setSelectedDashboard] = useState<DashboardAdmin | null>(null)
  const [formData, setFormData] = useState<{ name: string; description: string; layout: 'single-column' | 'two-columns' | 'grid' | '' }>({ name: '', description: '', layout: '' })
  const [error, setError] = useState<string | null>(null)

  const queryClient = useQueryClient()
  const confirmDialog = useConfirmDialog()

  const { data: dashboards = [], isLoading } = useQuery({
    queryKey: ['admin', 'dashboards'],
    queryFn: getDashboardsAdmin,
  })

  const createMutation = useMutation({
    mutationFn: createDashboard,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'dashboards'] })
      setCreateDialogOpen(false)
      setFormData({ name: '', description: '', layout: '' })
      setError(null)
    },
    onError: (error: unknown) => {
      const extracted = extractApiError(error)
      const userMessage = getErrorMessage(
        extracted.code === ErrorCode.VALIDATION_ERROR ? ErrorCode.VALIDATION_ERROR : ErrorCode.INTERNAL_ERROR,
        adminErrorMessages,
        extracted.message,
      )
      setError(userMessage)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string } }) =>
      updateDashboard(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'dashboards'] })
      setEditDialogOpen(false)
      toast.success('Dashboard updated successfully')
    },
    onError: (error: unknown) => {
      const extracted = extractApiError(error)
      const userMessage = getErrorMessage(
        extracted.code === ErrorCode.VALIDATION_ERROR ? ErrorCode.VALIDATION_ERROR : ErrorCode.INTERNAL_ERROR,
        adminErrorMessages,
        extracted.message,
      )
      toast.error(userMessage)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDashboard,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'dashboards'] })
      toast.success('Dashboard deleted successfully')
    },
    onError: (error: unknown) => {
      const extracted = extractApiError(error)
      const userMessage = getErrorMessage(extracted.code, adminErrorMessages, extracted.message)
      toast.error(userMessage)
    },
  })

  const handleCreate = () => {
    createMutation.mutate({
      name: formData.name,
      description: formData.description,
      layout: formData.layout || undefined,
    })
  }

  const handleEdit = () => {
    if (selectedDashboard) {
      updateMutation.mutate({
        id: selectedDashboard.id,
        data: formData,
      })
    }
  }

  const handleDelete = useCallback(
    (dashboard: DashboardAdmin) => {
      confirmDialog.confirm({
        title: 'Delete Dashboard',
        message: `Are you sure you want to delete "${dashboard.name}"?`,
        confirmLabel: 'Delete',
        onConfirm: () => {
          void deleteMutation.mutateAsync(dashboard.id)
        },
      })
    },
    [confirmDialog, deleteMutation],
  )

  const openEditDialog = useCallback(
    (dashboard: DashboardAdmin) => {
      setSelectedDashboard(dashboard)
      setFormData({ name: dashboard.name, description: dashboard.description || '', layout: '' })
      setEditDialogOpen(true)
    },
    [],
  )

  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: 'id',
        headerName: 'ID',
        width: 100,
        renderCell: ({ value }: GridRenderCellParams) => shortUuid(String(value ?? '')),
      },
      { field: 'name', headerName: 'Name', width: 250 },
      { field: 'description', headerName: 'Description', width: 300 },
      { field: 'created_at', headerName: 'Created', width: 180 },
      { field: 'updated_at', headerName: 'Updated', width: 180 },
      {
        field: 'actions',
        headerName: 'Actions',
        width: 200,
        sortable: false,
        filterable: false,
        renderCell: ({ row }: GridRenderCellParams<DashboardAdmin>) => (
          <>
            <GridActionsCellItem
              icon={<EditIcon />}
              label="Edit"
              onClick={() => openEditDialog(row)}
            />
            <GridActionsCellItem
              icon={<AccessIcon />}
              label="Access (coming soon)"
              disabled
              title="Access management is not yet implemented"
            />
            <GridActionsCellItem
              icon={<DeleteIcon />}
              label="Delete"
              onClick={() => handleDelete(row)}
            />
          </>
        ),
      },
    ],
    [handleDelete, openEditDialog],
  )

  const rows = dashboards.map((dashboard) => ({
    id: dashboard.id,
    name: dashboard.name,
    description: dashboard.description || '',
    created_at: new Date(dashboard.created_at).toLocaleString(),
    updated_at: new Date(dashboard.updated_at).toLocaleString(),
  }))

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setFormData({ name: '', description: '', layout: '' })
            setError(null)
            setCreateDialogOpen(true)
          }}
        >
          Create Dashboard
        </Button>
      </Box>

      <DataGrid
        rows={rows}
        columns={columns}
        loading={isLoading}
        autoHeight
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
      />

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Dashboard</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value.slice(0, 200) })}
            helperText={`${formData.description.length}/200`}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Layout</InputLabel>
            <Select
              value={formData.layout || ''}
              label="Layout"
              onChange={(e) => setFormData({ ...formData, layout: e.target.value })}
            >
              <MenuItem value="single-column">Single column</MenuItem>
              <MenuItem value="two-columns">Two columns</MenuItem>
              <MenuItem value="grid">Grid</MenuItem>
            </Select>
          </FormControl>
          {error && (<Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>)}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreate} disabled={createMutation.isPending || !formData.name}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Dashboard</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEdit} disabled={updateMutation.isPending || !formData.name}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmLabel={confirmDialog.confirmLabel}
        loading={deleteMutation.isPending}
        onConfirm={confirmDialog.handleConfirm}
        onCancel={confirmDialog.handleCancel}
      />
    </Box>
  )
}