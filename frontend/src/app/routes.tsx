import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../shared/components/ProtectedRoute'
import { RoleBasedAccess } from '../shared/components/RoleBasedAccess'
import { AppLayout } from '../shared/components/Layout'
import { NotFound } from '../shared/components/NotFound'
import { ErrorBoundary } from '../shared/components/ErrorBoundary'
import { LoginForm } from '../features/auth/ui/LoginForm'
import { RegisterForm } from '../features/auth/ui/RegisterForm'
import { DashboardList } from '../features/dashboards/ui/DashboardList'
import { DashboardView } from '../features/dashboards/ui/DashboardView'
import { AdminPanel } from '../features/admin/ui/AdminPanel'
import { UserProfile } from '../features/users/ui/UserProfile'
import { ChangePasswordPage } from '../features/users/ui/ChangePasswordPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route path="/register" element={<RegisterForm />} />
      <Route element={<AppLayout />}>
        <Route element={<ErrorBoundary />}>
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
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}