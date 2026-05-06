import { Drawer, List, ListItem, ListItemButton, ListItemText } from '@mui/material'
import { useNavigate } from 'react-router-dom'

const DRAWER_WIDTH = 240

export function Sidebar() {
  const navigate = useNavigate()

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
        },
      }}
    >
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/dashboards')}>
            <ListItemText primary="Dashboards" />
          </ListItemButton>
        </ListItem>
      </List>
    </Drawer>
  )
}
