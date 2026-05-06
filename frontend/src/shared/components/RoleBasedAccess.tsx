import { useAuth } from '../../../features/auth/useAuth'

interface RoleBasedAccessProps {
  roles: string[]
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function RoleBasedAccess({ roles, children, fallback = null }: RoleBasedAccessProps) {
  const { user } = useAuth()

  if (!user || !roles.includes(user.role)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
