import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { Box, Button, TextField, Typography, Alert } from '@mui/material'
import { useState } from 'react'
import { changePasswordSchema, type ChangePasswordFormData } from '../../../shared/types/formSchemas'
import { changePassword } from '../api/userApi'
import { toast } from 'react-hot-toast'

export function ChangePasswordPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  })

  const onFormSubmit = async (data: ChangePasswordFormData) => {
    try {
      setError(null)
      setIsSubmitting(true)
      await changePassword(data)
      toast.success('Password changed successfully')
      void navigate('/profile')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to change password'
      setError(message)
      toast.error(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = () => {
    void navigate('/profile')
  }

  return (
    <Box sx={{ p: 3, maxWidth: 400, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Change Password
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={(e) => void handleSubmit(onFormSubmit)(e)}>
        <TextField
          label="Current Password"
          type="password"
          fullWidth
          margin="normal"
          {...register('current_password')}
          error={!!errors.current_password}
          helperText={errors.current_password?.message}
        />

        <TextField
          label="New Password"
          type="password"
          fullWidth
          margin="normal"
          {...register('new_password')}
          error={!!errors.new_password}
          helperText={errors.new_password?.message}
        />

        <TextField
          label="Confirm New Password"
          type="password"
          fullWidth
          margin="normal"
          {...register('confirm_password')}
          error={!!errors.confirm_password}
          helperText={errors.confirm_password?.message}
        />

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button
            variant="contained"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Changing...' : 'Change Password'}
          </Button>
          <Button
            variant="outlined"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
        </Box>
      </Box>
    </Box>
  )
}