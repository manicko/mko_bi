import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { AuthResponse, UserProfile } from '../../../shared/types/api.types'
import { login as apiLogin, registerRequest as apiRegisterRequest, getProfile as apiGetProfile, logout as apiLogout, logoutClient, refreshToken as apiRefreshToken } from '../api/authApi'
import { getToken, setToken, removeToken } from './authToken'

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const getProfile = useCallback(async () => {
    try {
      setIsLoading(true)
      const profile = await apiGetProfile()
      setUser(profile)
    } catch (error) {
      removeToken()
      setUser(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string): Promise<AuthResponse> => {
    setIsLoading(true)
    try {
      const response = await apiLogin(email, password)
      setToken(response.access_token)
      setUser(response.user)
      // Security: Redirect to password change if flag is set after admin password reset
      if (response.user.force_password_change) {
        void navigate('/profile/change-password?force=true')
      }
      return response
    } catch (error) {
      removeToken()
      setUser(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [navigate])

  const registerRequest = useCallback(async (email: string) => {
    await apiRegisterRequest(email)
  }, [])

  const logout = useCallback(async () => {
    try {
      await apiLogout()
    } catch {
      // Ignore errors - user may already be logged out server-side
    }
    logoutClient()
    setUser(null)
  }, [])

  useEffect(() => {
    const token = getToken()
    if (!token) {
      // No access token - try silent refresh using refresh cookie
      void (async () => {
        try {
          const response = await apiRefreshToken()
          setToken(response.access_token)
          // After refresh, fetch profile
          const profile = await apiGetProfile()
          setUser(profile)
          if (profile.force_password_change) {
            void navigate('/profile/change-password?force=true')
          }
        } catch {
          // Refresh failed or no refresh cookie - user needs to login
          removeToken()
          setUser(null)
        } finally {
          setIsLoading(false)
        }
      })()
      return
    }

    void (async () => {
      try {
        setIsLoading(true)
        const profile = await apiGetProfile()
        setUser(profile)
        if (profile.force_password_change) {
          void navigate('/profile/change-password?force=true')
        }
      } catch {
        removeToken()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    })()
  }, [navigate])

  return {
    user,
    accessToken: getToken(),
    isLoading,
    login,
    logout,
    registerRequest,
    getProfile,
  }
}
