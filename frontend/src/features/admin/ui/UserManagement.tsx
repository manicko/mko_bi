import { useState, useMemo, useCallback } from 'react'
import { DataGrid, GridActionsCellItem, type GridRowId, type GridRenderCellParams } from '@mui/x-data-grid'
import type { GridColDef, GridRowClassNameParams } from '@mui/x-data-grid'
import { Box } from '@mui/material'
import { Delete as DeleteIcon, Block as BlockIcon } from '@mui/icons-material'
import { getUsers, changeUserRole, deleteUser } from '../api/adminApi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog'
import { ConfirmDialog } from '../../../shared/components/ConfirmDialog'
import { shortUuid } from '../../../shared/utils/shortUuid'
import { toast } from 'react-hot-toast'
import type { AdminUser } from '../../../shared/types/api.types'
import { UserRole } from '../../../shared/types/enums'

const ROLE_OPTIONS = [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER]

export function UserManagement() {
  const queryClient = useQueryClient()
  const confirmDialog = useConfirmDialog()
  const [savingRows, setSavingRows] = useState<GridRowId[]>([])

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: getUsers,
  })

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => changeUserRole(userId, role),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      setSavingRows((prev) => prev.filter((id) => id !== variables.userId))
      toast.success('Role updated successfully')
    },
    onError: (_, variables) => {
      setSavingRows((prev) => prev.filter((id) => id !== variables.userId))
      toast.error('Failed to update role')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      toast.success('User deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete user')
    },
  })

  const handleProcessRowUpdate = useCallback(
    async (newRow: AdminUser, oldRow: AdminUser) => {
      if (newRow.role === oldRow.role) {
        return newRow
      }

      setSavingRows((prev) => [...prev, newRow.id])

      try {
        await roleMutation.mutateAsync({ userId: newRow.id, role: newRow.role })
      } catch {
        setSavingRows((prev) => prev.filter((id) => id !== newRow.id))
        throw new Error('Update failed')
      }
      return newRow
    },
    [roleMutation],
  )

  const getRowClassName = useCallback(
    ({ id }: GridRowClassNameParams) => {
      return savingRows.includes(id) ? 'row-saving' : ''
    },
    [savingRows],
  )

  const handleDelete = useCallback(
    (user: AdminUser) => {
      confirmDialog.confirm({
        title: 'Delete User',
        message: `Are you sure you want to delete ${user.email}?`,
        confirmLabel: 'Delete',
        onConfirm: () => {
          void deleteMutation.mutateAsync(user.id)
        },
      })
    },
    [confirmDialog, deleteMutation],
  )

  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: 'id',
        headerName: 'ID',
        width: 100,
        renderCell: ({ value }: GridRenderCellParams) => shortUuid(String(value ?? '')),
      },
      { field: 'email', headerName: 'Email', width: 250 },
      {
        field: 'role',
        headerName: 'Role',
        width: 130,
        type: 'singleSelect',
        valueOptions: ROLE_OPTIONS,
        editable: true,
      },
      {
        field: 'is_active',
        headerName: 'Status',
        width: 120,
        valueGetter: (value: boolean) => (value ? 'Active' : 'Blocked'),
      },
      { field: 'created_at', headerName: 'Created', width: 180 },
      {
        field: 'actions',
        headerName: 'Actions',
        type: 'actions',
        width: 150,
        renderCell: ({ row }: GridRenderCellParams<AdminUser>) => (
          <>
            <GridActionsCellItem
              icon={<BlockIcon />}
              label="Block"
              onClick={() => {
                confirmDialog.confirm({
                  title: 'Block User',
                  message: `Are you sure you want to block ${row.email}?`,
                  confirmLabel: 'Block',
                  onConfirm: () => {
                    toast('Block functionality coming soon')
                  },
                })
              }}
            />
            <GridActionsCellItem icon={<DeleteIcon />} label="Delete" onClick={() => handleDelete(row)} />
          </>
        ),
      },
    ],
    [confirmDialog, handleDelete],
  )

  const rows = users.map((user) => ({
    id: user.id,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    created_at: new Date(user.created_at).toLocaleString(),
  }))

  return (
    <Box>
      <DataGrid
        rows={rows}
        columns={columns}
        loading={isLoading}
        autoHeight
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        processRowUpdate={handleProcessRowUpdate}
        onProcessRowUpdateError={(error) => {
          console.error('Row update error:', error)
        }}
        getRowClassName={getRowClassName}
      />
      <ConfirmDialog
        open={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmLabel={confirmDialog.confirmLabel}
        onConfirm={confirmDialog.handleConfirm}
        onCancel={confirmDialog.handleCancel}
      />
      <style>
        {`
          .row-saving {
            background-color: #fef08a !important;
          }
        `}
      </style>
    </Box>
  )
}