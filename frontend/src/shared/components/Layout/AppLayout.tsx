import { Outlet, Navigate, useLocation } from 'react-router-dom'
import { Header } from './Header'

function TrailingSlashRedirect() {
  const { pathname } = useLocation()
  if (pathname !== '/' && pathname.endsWith('/')) {
    return <Navigate to={pathname.slice(0, -1)} replace />
  }
  return null
}

export function AppLayout() {
  return (
    <>
      <TrailingSlashRedirect />
      <Header />
      <Outlet />
    </>
  )
}
