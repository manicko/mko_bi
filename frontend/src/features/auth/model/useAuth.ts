import { useCallback, useEffect, useState } from 'react'
import type { UserProfile } from '../../../shared/types/api.types'
import { login as apiLogin, registerRequest as apiRegisterRequest, getProfile as apiGetProfile, logoutClient } from '../api/authApi'
import { getToken, setToken, removeToken } from './authToken'

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

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

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await apiLogin(email, password)
      setToken(response.access_token)
      setUser(response.user)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const registerRequest = useCallback(async (email: string) => {
    await apiRegisterRequest(email)
  }, [])

  const logout = useCallback(() => {
    removeToken()
    logoutClient()
    setUser(null)
  }, [])

  useEffect(() => {
    const token = getToken()
    if (!token) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsLoading(false)
      return
    }

    const fetchProfile = async () => {
      try {
        setIsLoading(true)
        const profile = await apiGetProfile()
        setUser(profile)
      } catch {
        removeToken()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    fetchProfile()
  }, [])

  return {
    user,
    isLoading,
    login,
    logout,
    registerRequest,
    getProfile,
  }
}
