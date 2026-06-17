import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Typography, Button, Alert, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { getProfile, deleteAccount } from '../api/userApi'
import { useAuth } from '../../auth/model/useAuth'
import { toast } from 'react-hot-toast'

// getProfile is re-exported from authApi.ts to maintain backwards compatibility

export function UserProfile() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
  })

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true)
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setDeleteError(null)
  }

  const handleDeleteConfirm = async () => {
    try {
      setDeleteError(null)
      await deleteAccount()
      toast.success('Account deleted successfully')
      await logout()
      void navigate('/login')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete account'
      setDeleteError(message)
      toast.error(message)
    } finally {
      setDeleteDialogOpen(false)
    }
  }

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading...</Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Failed to load profile</Alert>
      </Box>
    )
  }

  const isAdmin = profile?.role === 'admin'

  return (
    <Box sx={{ p: 3, maxWidth: 600 }}>
      <Typography variant="h4" gutterBottom>
        User Profile
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Email
        </Typography>
        <Typography variant="body1" sx={{ p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
          {profile?.email}
        </Typography>
      </Box>

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Display Name
        </Typography>
        <Typography variant="body1" sx={{ p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
          {profile?.display_name}
        </Typography>
      </Box>

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Global Role
        </Typography>
        <Typography variant="body1" sx={{ p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
          {profile?.role}
        </Typography>
      </Box>

      <Box sx={{ mt: 4 }}>
        <Button
          variant="outlined"
          onClick={() => void navigate('/profile/change-password')}
        >
          Change Password
        </Button>
      </Box>

      {!isAdmin && (
        <Box sx={{ mt: 4 }}>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteClick}
          >
            Delete Account
          </Button>
        </Box>
      )}

      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Confirm Account Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete your account? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={() => void handleDeleteConfirm()} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}