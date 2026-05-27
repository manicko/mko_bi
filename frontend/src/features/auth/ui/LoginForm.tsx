import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { Box, Button, TextField, Typography, Alert } from '@mui/material'
import { useState, useEffect } from 'react'
import { loginSchema, type LoginFormData } from '../../../shared/types/formSchemas'
import { useAuth } from '../model/useAuth'

export function LoginForm() {
  const navigate = useNavigate()
  const { login, accessToken } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  // Clear error when user modifies form fields
  const watchedFields = useWatch({ control })
  useEffect(() => {
    if (error) {
      // Use setTimeout to defer state update outside of effect
      setTimeout(() => setError(null), 0)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchedFields.email, watchedFields.password])

  const onSubmit = async (data: LoginFormData) => {
    try {
      setError(null)
      setIsSubmitting(true)
      await login(data.email, data.password)
      void navigate('/dashboards')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Redirect authenticated users away from login page
  // Check after hooks to comply with React rules of hooks
  // If accessToken exists, user is authenticated
  if (accessToken) {
    return <Navigate to="/dashboards" replace />
  }

  return (
    <Box component="form" onSubmit={(e) => void handleSubmit(onSubmit)(e)} sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Login
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

      <TextField
        label="Password"
        type="password"
        fullWidth
        margin="normal"
        {...register('password')}
        error={!!errors.password}
        helperText={errors.password?.message}
      />

      <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={isSubmitting}>
        {isSubmitting ? 'Loading...' : 'Login'}
      </Button>

      <Typography sx={{ mt: 2, textAlign: 'center' }}>
        {"Don't have an account? "}
        <Link to="/register">
          Create an account
        </Link>
      </Typography>
    </Box>
  )
}