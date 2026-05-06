import { useCallback, useEffect, useState } from 'react'
import { axiosInstance } from '../../shared/api/axiosInstance'

interface User {
  id: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      // Verify token and get user profile
      axiosInstance
        .get('/auth/profile')
        .then((response) => {
          setAuthState({
            user: response.data,
            isAuthenticated: true,
            isLoading: false,
          })
        })
        .catch(() => {
          localStorage.removeItem('access_token')
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          })
        })
    } else {
      setAuthState((prev) => ({ ...prev, isLoading: false }))
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    })
  }, [])

  return {
    ...authState,
    logout,
  }
}
