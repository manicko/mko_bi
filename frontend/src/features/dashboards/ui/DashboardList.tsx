import { useNavigate } from 'react-router-dom'
import {
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Stack,
} from '@mui/material'
import { useMyDashboards } from '../api/dashboardApi'

export function DashboardList() {
  const navigate = useNavigate()
  const { data: dashboards, isLoading, error } = useMyDashboards()

  if (isLoading) {
    return (
      <Stack sx={{ alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Stack>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboards. Please try again.
      </Alert>
    )
  }

  if (!dashboards || dashboards.length === 0) {
    return (
      <Stack sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          My Dashboards
        </Typography>
        <Alert severity="info">
          No dashboards available. Contact an administrator to get access.
        </Alert>
      </Stack>
    )
  }

  return (
    <Stack sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        My Dashboards
      </Typography>
      <Grid container spacing={2}>
        {dashboards.map((dashboard) => (
          <Grid key={dashboard.id} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {dashboard.name}
                </Typography>
                {dashboard.description && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    component="p"
                    sx={{ mb: 2 }}
                  >
                    {dashboard.description}
                  </Typography>
                )}
                <Typography variant="caption" sx={{ display: 'block', mb: 2 }}>
                  Permission: {dashboard.permission}
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => navigate(`/dashboard/${dashboard.id}`)}
                >
                  Open
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  )
}
