import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { useAuth } from '../'
import { Box, Button, TextField, Typography, Alert } from '@mui/material'
import { useState } from 'react'

const BLOCKED_DOMAINS = ['tempmail.com', 'throwawaymail.com']

const registerSchema = z.object({
  email: z
    .string()
    .email('Invalid email format')
    .refine((email) => {
      const domain = email.split('@')[1]
      return domain && !BLOCKED_DOMAINS.includes(domain)
    }, 'This email domain is not allowed'),
})

type RegisterFormData = z.infer<typeof registerSchema>

export function RegisterForm() {
  const { registerRequest, isLoading } = useAuth()
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
      await registerRequest(data.email)
      setSuccess(true)
    } catch {
      setError('Failed to submit registration request. Please try again.')
    }
  }

  if (success) {
    return (
      <Box sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
        <Alert severity="success" sx={{ mb: 2 }}>
          Registration request sent to administrator
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
    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
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

      <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={isLoading}>
        {isLoading ? 'Submitting...' : 'Submit Request'}
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
