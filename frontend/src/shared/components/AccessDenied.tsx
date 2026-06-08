import { Box, Typography } from '@mui/material'

/**
 * Access denied page displayed when a user lacks required permissions.
 *
 * Intended usage:
 * - As the fallback for RoleBasedAccess when user lacks required roles
 * - As a dedicated route for 403 Forbidden responses
 * - As an inline component when dashboard access is denied
 *
 * @example
 * // In RoleBasedAccess:
 * <RoleBasedAccess roles={['admin']} fallback={<AccessDenied />}>
 *   <AdminPanel />
 * </RoleBasedAccess>
 *
 * // In routes for 403 handling:
 * <Route path="/403" element={<AccessDenied />} />
 */
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