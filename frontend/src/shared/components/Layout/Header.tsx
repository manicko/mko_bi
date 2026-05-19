import { AppBar, Box, Button, Toolbar, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/model/useAuth'

export function Header() {
  const { user } = useAuth()
  const navigate = useNavigate()

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          MKOBI Dashboard
        </Typography>
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {user.role === 'admin' && (
              <Button color="inherit" onClick={() => navigate('/admin')}>
                Admin
              </Button>
            )}
            <Button color="inherit" onClick={() => navigate('/profile')}>
              Profile
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  )
}
