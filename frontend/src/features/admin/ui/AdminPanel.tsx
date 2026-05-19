import { Tabs, Tab, Box } from '@mui/material'
import { useState } from 'react'
import { UserManagement } from './UserManagement'
import { RegistrationRequests } from './RegistrationRequests'
import { DashboardManagement } from './DashboardManagement'
import { LogViewer } from './LogViewer'

export function AdminPanel() {
  const [currentTab, setCurrentTab] = useState(0)

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue)
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Tabs value={currentTab} onChange={handleTabChange} aria-label="Admin panel tabs">
        <Tab label="User Management" />
        <Tab label="Registration Requests" />
        <Tab label="Dashboard Management" />
        <Tab label="Log Viewer" />
      </Tabs>

      <Box sx={{ mt: 3 }}>
        <Box sx={{ display: currentTab === 0 ? 'block' : 'none' }}>
          <UserManagement />
        </Box>
        <Box sx={{ display: currentTab === 1 ? 'block' : 'none' }}>
          <RegistrationRequests />
        </Box>
        <Box sx={{ display: currentTab === 2 ? 'block' : 'none' }}>
          <DashboardManagement />
        </Box>
        <Box sx={{ display: currentTab === 3 ? 'block' : 'none' }}>
          <LogViewer />
        </Box>
      </Box>
    </Box>
  )
}
