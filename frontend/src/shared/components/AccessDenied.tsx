import { Box, Typography } from '@mui/material'

export function AccessDenied() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
        textAlign: 'center',
      }}
    >
      <Typography variant="h5" color="text.secondary">
        No access — contact your administrator
      </Typography>
    </Box>
  )
}