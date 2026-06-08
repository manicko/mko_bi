import { useAuth } from '../../features/auth'
import { AccessDenied } from './AccessDenied'

interface RoleBasedAccessProps {
  roles: string[]
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function RoleBasedAccess({ roles, children, fallback = <AccessDenied /> }: RoleBasedAccessProps) {
  const { user } = useAuth()

  if (!user || !roles.includes(user.role)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
