import WarningAmber from '@mui/icons-material/WarningAmber'
import { Box, Container, Typography, Button } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

interface ErrorPageProps {
  variant: '404' | '500'
  error?: Error | null
}

export function ErrorPage({ variant, error }: ErrorPageProps) {
  const isDev = import.meta.env.DEV
  const goToHome = '/login'

  const handleReload = () => {
    window.location.reload()
  }

  if (variant === '404') {
    return (
      <Container maxWidth="md">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            textAlign: 'center',
            py: 4,
          }}
        >
          <WarningAmber sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
          <Typography variant="h3" component="h1" gutterBottom>
            Page not found
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            The page you are looking for does not exist or has been moved.
          </Typography>
          <Button
            component={RouterLink}
            to={goToHome}
            variant="contained"
            size="large"
          >
            Go to Home
          </Button>
        </Box>
      </Container>
    )
  }

  // 500 variant
  const errorMessage = isDev && error ? error.message : null
  const errorStack = isDev && error ? error.stack : null

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
          py: 4,
        }}
      >
        <WarningAmber sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
        <Typography variant="h3" component="h1" gutterBottom>
          Something went wrong
        </Typography>
        {isDev && errorMessage ? (
          <Box sx={{ mb: 2, textAlign: 'left', width: '100%', maxWidth: 500 }}>
            <Typography variant="body2" color="error" sx={{ mb: 1 }}>
              Error: {errorMessage}
            </Typography>
            {errorStack && (
              <Typography
                variant="caption"
                component="pre"
                sx={{
                  display: 'block',
                  bgcolor: 'grey.100',
                  p: 1,
                  borderRadius: 1,
                  overflow: 'auto',
                  fontSize: '0.7rem',
                }}
              >
                {errorStack}
              </Typography>
            )}
          </Box>
        ) : (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            An unexpected error occurred. Please try again later.
          </Typography>
        )}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="outlined" onClick={handleReload}>
            Reload page
          </Button>
          <Button
            component={RouterLink}
            to={goToHome}
            variant="contained"
          >
            Go to Home
          </Button>
        </Box>
      </Box>
    </Container>
  )
}