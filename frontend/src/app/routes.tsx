import { lazy, Suspense } from 'react'
import type { ComponentType } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../shared/components/ProtectedRoute'
import { RoleBasedAccess } from '../shared/components/RoleBasedAccess'
import { AppLayout } from '../shared/components/Layout'
import { NotFound } from '../shared/components/NotFound'
import { ErrorBoundary } from '../shared/components/ErrorBoundary'
import { CircularProgress, Box } from '@mui/material'
import { useAuth } from '../features/auth/model/useAuth'

// Lazy-loaded route components
const LoginForm = lazy(() =>
  import('../features/auth/ui/LoginForm').then((module) => ({ default: module.LoginForm as ComponentType })),
)
const RegisterForm = lazy(() =>
  import('../features/auth/ui/RegisterForm').then((module) => ({ default: module.RegisterForm as ComponentType })),
)
const DashboardList = lazy(() =>
  import('../features/dashboards/ui/DashboardList').then((module) => ({ default: module.DashboardList as ComponentType })),
)
const DashboardView = lazy(() =>
  import('../features/dashboards/ui/DashboardView').then((module) => ({ default: module.DashboardView as ComponentType })),
)
const AdminPanel = lazy(() =>
  import('../features/admin/ui/AdminPanel').then((module) => ({ default: module.AdminPanel as ComponentType })),
)
const UserProfile = lazy(() =>
  import('../features/users/ui/UserProfile').then((module) => ({ default: module.UserProfile as ComponentType })),
)
const ChangePasswordPage = lazy(() =>
  import('../features/users/ui/ChangePasswordPage').then((module) => ({
    default: module.ChangePasswordPage as ComponentType,
  })),
)

function LoadingFallback() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
      <CircularProgress />
    </Box>
  )
}

function RootRedirect() {
  const { accessToken, isLoading } = useAuth()

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  return <Navigate to={accessToken ? '/dashboards' : '/login'} replace />
}

export function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <Suspense fallback={<LoadingFallback />}>
            <LoginForm />
          </Suspense>
        }
      />
      <Route
        path="/register"
        element={
          <Suspense fallback={<LoadingFallback />}>
            <RegisterForm />
          </Suspense>
        }
      />
      <Route element={<AppLayout />}>
        <Route element={<ErrorBoundary />}>
          <Route
            path="/dashboards"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ProtectedRoute>
                  <DashboardList />
                </ProtectedRoute>
              </Suspense>
            }
          />
          <Route
            path="/dashboard/:id"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ProtectedRoute>
                  <DashboardView />
                </ProtectedRoute>
              </Suspense>
            }
          />
          <Route
            path="/admin"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ProtectedRoute>
                  <RoleBasedAccess roles={['admin']}>
                    <AdminPanel />
                  </RoleBasedAccess>
                </ProtectedRoute>
              </Suspense>
            }
          />
          <Route
            path="/profile"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ProtectedRoute>
                  <UserProfile />
                </ProtectedRoute>
              </Suspense>
            }
          />
          <Route
            path="/profile/change-password"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ProtectedRoute>
                  <ChangePasswordPage />
                </ProtectedRoute>
              </Suspense>
            }
          />
          <Route path="/" element={<RootRedirect />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}