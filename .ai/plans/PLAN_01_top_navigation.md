---
wave: 3
depends_on: []
files_modified:
  - frontend/src/shared/components/Layout/Header.tsx
  - frontend/src/shared/components/Layout/Sidebar.tsx
  - frontend/src/shared/components/Layout/AppLayout.tsx
autonomous: true
---

# Plan 01.11: Top Navigation with Role-Based Items

## Goal
Replace the sidebar navigation with a top navigation bar in `Header.tsx` with role-based items. Order (right to left): Profile, Dashboards, Admin (admin only). Active menu item highlighted. Remove the sidebar.

## must_haves
- [ ] Top nav items: Profile, Dashboards, Admin (admin only) — right to left order
- [ ] Active menu item highlighted (using `useLocation` to detect current route)
- [ ] Admin link only visible to users with `role === 'admin'`
- [ ] Sidebar removed from layout (no longer rendered in `AppLayout`)
- [ ] Clean, minimal, light theme styling
- [ ] Icons for key actions where appropriate

## Tasks

### Task 1: Update Header with top navigation
In `frontend/src/shared/components/Layout/Header.tsx`:
- **Remove** the existing Profile button (`<Button color="inherit" onClick={() => navigate('/profile')}>Profile</Button>`)
- **Remove** the existing Admin button (`{user.role === 'admin' && <Button color="inherit" onClick={() => navigate('/admin')}>Admin</Button>}`)
- **Remove** the `useNavigate` import and hook if no longer needed elsewhere in the file
- Add navigation buttons in the toolbar using the unified nav items pattern below
- Use `useLocation()` to detect current route and highlight active item
- Style active button differently (e.g., `variant="outlined"` or custom sx with border-bottom)
- Keep the app title "MKOBI Dashboard" on the left
- Keep the user email and logout button on the right

Implementation approach:
```tsx
const location = useLocation()

// Order: Admin first, then Dashboards, then Profile — rendered left-to-right in flex.
// This places Profile rightmost (near user email), giving right-to-left reading order:
// Profile, Dashboards, Admin (locked decision).
const navItems = []

// Admin only — leftmost among nav items
if (user?.role === 'admin') {
  navItems.push({ label: 'Admin', path: '/admin' })
}

navItems.push({ label: 'Dashboards', path: '/dashboards' })
navItems.push({ label: 'Profile', path: '/profile' })

// In Toolbar, before user email:
{navItems.map((item) => (
  <Button
    key={item.path}
    color="inherit"
    onClick={() => navigate(item.path)}
    sx={{
      fontWeight: location.pathname === item.path ? 700 : 400,
      borderBottom: location.pathname === item.path ? '2px solid' : 'none',
      borderRadius: 0,
    }}
  >
    {item.label}
  </Button>
))}
```

### Task 2: Remove Sidebar from AppLayout
In `frontend/src/shared/components/Layout/AppLayout.tsx`:
- Remove the `<Sidebar />` component rendering
- Remove the `Sidebar` import
- Remove the wrapping `<Box sx={{ display: 'flex', flex: 1 }}>` — `<Outlet />` should be direct child
- Keep the main content area full-width

### Task 3: Remove Sidebar component file
The `frontend/src/shared/components/Layout/Sidebar.tsx` file is no longer needed. It can be left in place (unused) to avoid breaking any potential imports, but it should not be imported anywhere.

## Validation
- Verify top nav shows Profile, Dashboards, Admin (for admin users)
- Verify Admin link is hidden for non-admin users
- Verify active route is highlighted
- Verify sidebar is no longer visible
- Verify navigation works correctly for all routes

## Acceptance Criteria
- [ ] Top nav with role-based items
- [ ] Active item highlighted
- [ ] Admin link only for admins
- [ ] Sidebar removed from layout
