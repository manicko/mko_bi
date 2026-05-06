import { useState } from 'react'
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import {
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Snackbar,
} from '@mui/material'
import { Check as ApproveIcon, Close as RejectIcon } from '@mui/icons-material'
import { getRegistrationRequests, approveRequest, rejectRequest } from '../api/adminApi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { RegistrationRequestItem } from '../../../shared/types/api.types'

const columns: GridColDef[] = [
  { field: 'email', headerName: 'Email', width: 250 },
  {
    field: 'status',
    headerName: 'Status',
    width: 130,
    renderCell: (params) => {
      const status = params.value as string
      const color = status === 'approved' ? 'success' : status === 'rejected' ? 'error' : 'warning'
      return <Chip label={status} color={color} size="small" />
    },
  },
  { field: 'created_at', headerName: 'Created', width: 180 },
  { field: 'actions', headerName: 'Actions', type: 'actions', width: 150 },
]

export function RegistrationRequests() {
  const [selectedRequest, setSelectedRequest] = useState<RegistrationRequestItem | null>(null)
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve')
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })

  const queryClient = useQueryClient()

  const { data: requests = [], isLoading } = useQuery({
    queryKey: ['admin', 'registration-requests'],
    queryFn: getRegistrationRequests,
  })

  const approveMutation = useMutation({
    mutationFn: approveRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'registration-requests'] })
      setConfirmDialogOpen(false)
      setSnackbar({ open: true, message: 'Request approved successfully', severity: 'success' })
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to approve request', severity: 'error' })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: rejectRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'registration-requests'] })
      setConfirmDialogOpen(false)
      setSnackbar({ open: true, message: 'Request rejected successfully', severity: 'success' })
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to reject request', severity: 'error' })
    },
  })

  const rows = requests.map((req) => ({
    id: req.id,
    email: req.email,
    status: req.status,
    created_at: new Date(req.created_at).toLocaleString(),
    actions: (
      <>
        {req.status === 'pending' && (
          <>
            <GridActionsCellItem
              icon={<ApproveIcon />}
              label="Approve"
              onClick={() => {
                setSelectedRequest(req)
                setActionType('approve')
                setConfirmDialogOpen(true)
              }}
            />
            <GridActionsCellItem
              icon={<RejectIcon />}
              label="Reject"
              onClick={() => {
                setSelectedRequest(req)
                setActionType('reject')
                setConfirmDialogOpen(true)
              }}
            />
          </>
        )}
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

      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
        <DialogTitle>
          {actionType === 'approve' ? 'Approve' : 'Reject'} Registration Request
        </DialogTitle>
        <DialogContent>
          Are you sure you want to {actionType} the request for {selectedRequest?.email}?
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => {
              if (selectedRequest) {
                if (actionType === 'approve') {
                  approveMutation.mutate(selectedRequest.id)
                } else {
                  rejectMutation.mutate(selectedRequest.id)
                }
              }
            }}
            color={actionType === 'approve' ? 'primary' : 'error'}
            disabled={approveMutation.isPending || rejectMutation.isPending}
          >
            {actionType === 'approve' ? 'Approve' : 'Reject'}
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
