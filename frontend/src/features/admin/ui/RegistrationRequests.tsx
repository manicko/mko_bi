import { useState } from 'react'
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import { Box, Chip, Typography } from '@mui/material'
import { Check as ApproveIcon, Close as RejectIcon } from '@mui/icons-material'
import { getRegistrationRequests, approveRequest, rejectRequest } from '../api/adminApi'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ConfirmDialog } from '../../../shared/components/ConfirmDialog'
import { toast } from 'react-hot-toast'
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

  const queryClient = useQueryClient()

  const { data: requests = [], isLoading } = useQuery({
    queryKey: ['admin', 'registration-requests'],
    queryFn: getRegistrationRequests,
    refetchOnMount: 'always',
  })

  const approveMutation = useMutation({
    mutationFn: approveRequest,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'registration-requests'] })
      setConfirmDialogOpen(false)
      toast.success('Request approved successfully')
    },
    onError: () => {
      toast.error('Failed to approve request')
    },
  })

  const rejectMutation = useMutation({
    mutationFn: rejectRequest,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'registration-requests'] })
      setConfirmDialogOpen(false)
      toast.success('Request rejected successfully')
    },
    onError: () => {
      toast.error('Failed to reject request')
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

  function NoRegistrationRequestsOverlay() {
    return (
      <Typography sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
        No pending registration requests
      </Typography>
    )
  }

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
        slots={{ noRowsOverlay: NoRegistrationRequestsOverlay }}
      />

      <ConfirmDialog
        open={confirmDialogOpen}
        title={`${actionType === 'approve' ? 'Approve' : 'Reject'} Registration Request`}
        message={`Are you sure you want to ${actionType} the request for ${selectedRequest?.email}?`}
        onConfirm={() => {
          if (selectedRequest) {
            if (actionType === 'approve') {
              approveMutation.mutate(selectedRequest.id)
            } else {
              rejectMutation.mutate(selectedRequest.id)
            }
          }
        }}
        onCancel={() => setConfirmDialogOpen(false)}
        loading={approveMutation.isPending || rejectMutation.isPending}
        confirmLabel={actionType === 'approve' ? 'Approve' : 'Reject'}
      />
    </Box>
  )
}
