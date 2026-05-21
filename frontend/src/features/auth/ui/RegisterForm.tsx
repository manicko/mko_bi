import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import { useAuth } from '../'
import { Box, Button, TextField, Typography, Alert } from '@mui/material'
import { useState } from 'react'
import { registerSchema, type RegisterFormData } from '../../../shared/types/formSchemas'

export function RegisterForm() {
  const { registerRequest } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setError(null)
      setIsSubmitting(true)
      await registerRequest(data.email)
      setSuccess(true)
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      const errorMessage = axiosError.response?.data?.detail || 'Failed to submit registration request. Please try again.'
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (success) {
    return (
      <Box sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
        <Alert severity="success" sx={{ mb: 2 }}>
          Your request has been submitted. An administrator will review it.
        </Alert>
        <Typography sx={{ textAlign: 'center' }}>
          <Link to="/login">
            Back to login
          </Link>
        </Typography>
      </Box>
    )
  }

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Register
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TextField
        label="Email"
        fullWidth
        margin="normal"
        {...register('email')}
        error={!!errors.email}
        helperText={errors.email?.message}
      />

      <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }}
        loading={isSubmitting} loadingPosition="start">
        {isSubmitting ? 'Sending...' : 'Submit Request'}
      </Button>

      <Typography sx={{ mt: 2, textAlign: 'center' }}>
        {"Already have an account? "}
        <Link to="/login">
          Login
        </Link>
      </Typography>
    </Box>
  )
}
