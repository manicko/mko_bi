import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../shared/components/ProtectedRoute'
import { RoleBasedAccess } from '../shared/components/RoleBasedAccess'

// Placeholder imports - will be implemented in future tasks
// import { LoginPage } from '../features/auth/LoginPage'
// import { RegisterPage } from '../features/auth/RegisterPage'
// import { DashboardListPage } from '../features/dashboards/DashboardListPage'
// import { DashboardViewPage } from '../features/dashboards/DashboardViewPage'
// import { UploadPage } from '../features/upload/UploadPage'
// import { AdminPanel } from '../features/admin/AdminPanel'
// import { ProfilePage } from '../features/users/ProfilePage'

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ padding: '20px' }}>
      <h1>{title}</h1>
      <p>This page will be implemented in a future task.</p>
    </div>
  )
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PlaceholderPage title="Login" />} />
      <Route path="/register" element={<PlaceholderPage title="Register" />} />
      <Route
        path="/dashboards"
        element={
          <ProtectedRoute>
            <PlaceholderPage title="Dashboards" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/:id"
        element={
          <ProtectedRoute>
            <PlaceholderPage title="Dashboard View" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/:id/upload"
        element={
          <ProtectedRoute>
            <RoleBasedAccess roles={['admin', 'editor']}>
              <PlaceholderPage title="Upload Data" />
            </RoleBasedAccess>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <RoleBasedAccess roles={['admin']}>
              <PlaceholderPage title="Admin Panel" />
            </RoleBasedAccess>
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <PlaceholderPage title="Profile" />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboards" replace />} />
    </Routes>
  )
}
