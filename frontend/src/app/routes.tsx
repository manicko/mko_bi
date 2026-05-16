import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../shared/components/ProtectedRoute'
import { RoleBasedAccess } from '../shared/components/RoleBasedAccess'
import { AppLayout } from '../shared/components/Layout'
import { LoginForm } from '../features/auth/ui/LoginForm'
import { RegisterForm } from '../features/auth/ui/RegisterForm'
import { DashboardList } from '../features/dashboards/ui/DashboardList'
import { DashboardView } from '../features/dashboards/ui/DashboardView'
import { UploadPage } from '../features/upload/ui/UploadPage'
import { AdminPanel } from '../features/admin/ui/AdminPanel'
import { UserProfile } from '../features/users/ui/UserProfile'
import { ChangePasswordPage } from '../features/users/ui/ChangePasswordPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/register" element={<RegisterForm />} />
        <Route
          path="/dashboards"
          element={
            <ProtectedRoute>
              <DashboardList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/:id"
          element={
            <ProtectedRoute>
              <DashboardView />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/:id/upload"
          element={
            <ProtectedRoute>
              <RoleBasedAccess roles={['admin', 'editor']}>
                <UploadPage />
              </RoleBasedAccess>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <RoleBasedAccess roles={['admin']}>
                <AdminPanel />
              </RoleBasedAccess>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <UserProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile/change-password"
          element={
            <ProtectedRoute>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboards" replace />} />
      </Route>
    </Routes>
  )
}