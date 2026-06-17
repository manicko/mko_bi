import { useState, useMemo, useCallback } from 'react'
import { DataGrid, GridActionsCellItem, type GridRowId, type GridRenderCellParams } from '@mui/x-data-grid'
import type { GridColDef, GridRowClassNameParams } from '@mui/x-data-grid'
import { Box, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from '@mui/material'
import { Delete as DeleteIcon, Key as ResetPasswordIcon } from '@mui/icons-material'
import { getUsers, changeUserRole, deleteUser, resetUserPassword, retrieveTempPassword } from '../api/adminApi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog'
import { ConfirmDialog } from '../../../shared/components/ConfirmDialog'
import { ResetPasswordResultDialog } from './ResetPasswordResultDialog'
import { shortUuid } from '../../../shared/utils/shortUuid'
import { formatDate } from '../../../shared/utils/formatDate'
import { toast } from 'react-hot-toast'
import type { AdminUser } from '../../../shared/types/api.types'
import { UserRole } from '../../../shared/types/enums'

const ROLE_OPTIONS = [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER]

// Row type for DataGrid - same as AdminUser since is_active was removed
type UserRow = AdminUser

interface RetrievePasswordDialogProps {
  open: boolean
  retrievalToken: string
  userEmail: string
  onClose: () => void
  onPasswordRetrieved: (tempPassword: string, userEmail: string) => void
}

function RetrievePasswordDialog({
  open,
  retrievalToken,
  userEmail,
  onClose,
  onPasswordRetrieved,
}: RetrievePasswordDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  const handleRetrieve = async () => {
    setLoading(true)
    setError(false)
    try {
      const data = await retrieveTempPassword(retrievalToken)
      onPasswordRetrieved(data.temp_password, userEmail)
    } catch {
      setError(true)
      toast.error('Password expired or already retrieved')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Retrieve Password</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Click "Show Password" to retrieve the temporary password for {userEmail}. This can only be
          done once.
        </DialogContentText>
        {error && (
          <DialogContentText color="error" sx={{ mt: 2 }}>
            Password expired or already retrieved.
          </DialogContentText>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={() => { void handleRetrieve() }} variant="contained" disabled={loading}>
          {loading ? 'Retrieving...' : 'Show Password'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export function UserManagement() {
  const queryClient = useQueryClient()
  const confirmDialog = useConfirmDialog()
  const [savingRows, setSavingRows] = useState<GridRowId[]>([])
  const [resetResult, setResetResult] = useState<{
    tempPassword: string
    userEmail: string
  } | null>(null)

  const [pendingRetrievalToken, setPendingRetrievalToken] = useState<string | null>(null)
  const [pendingUserEmail, setPendingUserEmail] = useState<string | null>(null)
  const [showPasswordMode, setShowPasswordMode] = useState(false)

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

  const resetPasswordMutation = useMutation({
    mutationFn: resetUserPassword,
    onSuccess: (data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      const user = users.find((u) => u.id === variables)
      setPendingRetrievalToken(data.retrieval_token)
      setPendingUserEmail(user?.email ?? '')
      setShowPasswordMode(true)
      toast.success('Password reset successfully')
    },
    onError: () => {
      toast.error('Failed to reset password')
    },
  })

  const handleProcessRowUpdate = useCallback(
    async (newRow: UserRow, oldRow: UserRow) => {
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

  const handleResetPassword = useCallback(
    (user: AdminUser) => {
      confirmDialog.confirm({
        title: 'Reset Password',
        message: `Generate a new temporary password for ${user.email}? The current password will be immediately invalidated.`,
        confirmLabel: 'Confirm',
        onConfirm: () => {
          void resetPasswordMutation.mutateAsync(user.id)
        },
      })
    },
    [confirmDialog, resetPasswordMutation],
  )

  const handlePasswordRetrieved = useCallback(
    (tempPassword: string, userEmail: string) => {
      setResetResult({ tempPassword, userEmail })
    },
    [],
  )

  const columns = useMemo(
    (): GridColDef<UserRow>[] => [
      {
        field: 'id',
        headerName: 'ID',
        width: 100,
        renderCell: ({ value }: GridRenderCellParams<UserRow>) => shortUuid(String(value ?? '')),
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
      { field: 'created_at', headerName: 'Created', width: 180 },
      {
        field: 'actions',
        headerName: 'Actions',
        type: 'actions',
        width: 150,
        renderCell: ({ row }: GridRenderCellParams<UserRow>) => (
          <>
            <GridActionsCellItem icon={<DeleteIcon />} label="Delete" onClick={() => handleDelete(row)} />
            <GridActionsCellItem
              icon={<ResetPasswordIcon />}
              label="Reset Password"
              onClick={() => handleResetPassword(row)}
            />
          </>
        ),
      },
    ],
    [handleDelete, handleResetPassword],
  )

  const rows: UserRow[] = users.map((user) => ({
    id: user.id,
    email: user.email,
    role: user.role,
    created_at: formatDate(user.created_at),
    force_password_change: user.force_password_change,
  }))

  return (
    <Box>
      <DataGrid<UserRow>
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
          const errorMessage = error instanceof Error ? error.message : 'Unknown error'
          toast.error(`Failed to update role: ${errorMessage}`)
        }}
        getRowClassName={getRowClassName}
        sx={{
          '& .row-saving': {
            backgroundColor: '#fef08a',
          },
        }}
      />
      <ConfirmDialog
        open={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmLabel={confirmDialog.confirmLabel}
        onConfirm={confirmDialog.handleConfirm}
        onCancel={confirmDialog.handleCancel}
        loading={deleteMutation.isPending || resetPasswordMutation.isPending}
      />
      <RetrievePasswordDialog
        open={showPasswordMode}
        retrievalToken={pendingRetrievalToken ?? ''}
        userEmail={pendingUserEmail ?? ''}
        onClose={() => {
          setShowPasswordMode(false)
          setPendingRetrievalToken(null)
          setPendingUserEmail(null)
        }}
        onPasswordRetrieved={handlePasswordRetrieved}
      />
      <ResetPasswordResultDialog
        open={resetResult !== null}
        tempPassword={resetResult?.tempPassword ?? ''}
        userEmail={resetResult?.userEmail ?? ''}
        onClose={() => {
          setResetResult(null)
          setShowPasswordMode(false)
        }}
      />
    </Box>
  )
}