import { useState } from 'react'
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
} from '@mui/material'
import { Edit as EditIcon, Delete as DeleteIcon, Block as BlockIcon } from '@mui/icons-material'
import { getUsers, changeUserRole, deleteUser } from '../api/adminApi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { AdminUser } from '../../../shared/types/api.types'

const columns: GridColDef[] = [
  { field: 'email', headerName: 'Email', width: 250 },
  { field: 'role', headerName: 'Role', width: 130 },
  {
    field: 'is_active',
    headerName: 'Status',
    width: 120,
    valueGetter: (value: boolean) => (value ? 'Active' : 'Blocked'),
  },
  { field: 'created_at', headerName: 'Created', width: 180 },
  { field: 'actions', headerName: 'Actions', type: 'actions', width: 150 },
]

export function UserManagement() {
  const [roleDialogOpen, setRoleDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null)
  const [newRole, setNewRole] = useState<string>('')
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })

  const queryClient = useQueryClient()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: getUsers,
  })

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => changeUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      setRoleDialogOpen(false)
      setSnackbar({ open: true, message: 'Role updated successfully', severity: 'success' })
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to update role', severity: 'error' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      setSnackbar({ open: true, message: 'User deleted successfully', severity: 'success' })
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to delete user', severity: 'error' })
    },
  })

  const rows = users.map((user) => ({
    id: user.id,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    created_at: new Date(user.created_at).toLocaleString(),
    actions: (
      <>
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Change Role"
          onClick={() => {
            setSelectedUser(user)
            setNewRole(user.role)
            setRoleDialogOpen(true)
          }}
        />
        <GridActionsCellItem
          icon={<BlockIcon />}
          label="Block"
          onClick={() => {
            if (confirm(`Block user ${user.email}?`)) {
              roleMutation.mutate({ userId: user.id, role: user.role })
            }
          }}
        />
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => {
            if (confirm(`Delete user ${user.email}?`)) {
              deleteMutation.mutate(user.id)
            }
          }}
        />
      </>
    ),
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
          pagination: { paginationModel: { pageSize: 10 } },
        }}
      />

      <Dialog open={roleDialogOpen} onClose={() => setRoleDialogOpen(false)}>
        <DialogTitle>Change Role for {selectedUser?.email}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Role</InputLabel>
            <Select
              value={newRole}
              label="Role"
              onChange={(e) => setNewRole(e.target.value)}
            >
              <MenuItem value="admin">Admin</MenuItem>
              <MenuItem value="editor">Editor</MenuItem>
              <MenuItem value="viewer">Viewer</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRoleDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => {
              if (selectedUser) {
                roleMutation.mutate({ userId: selectedUser.id, role: newRole })
              }
            }}
            disabled={roleMutation.isPending}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  )
}
