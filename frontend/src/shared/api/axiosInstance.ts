import axios, { AxiosError } from 'axios'
import { toast } from 'react-hot-toast'
import { getTokenWithExpirationCheck, removeToken, setToken } from '../../features/auth/model/authToken'
import { getRefreshHandler } from './refreshHandler'

export const axiosInstance = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  maxRedirects: 5,
})

// Request interceptor - add JWT token with expiration check
axiosInstance.interceptors.request.use(
  (config) => {
    const token = getTokenWithExpirationCheck()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      // Token was expired and removed
      removeToken()
    }
    return config
  },
  (error) => Promise.reject(error instanceof Error ? error : new Error(String(error)))
)

// Request queuing for concurrent 401 handling
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: Error) => void
}> = []

const processQueue = (error: Error | null, token: string | null = null): void => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token!)
    }
  })
  failedQueue = []
}

// Response interceptor - handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Skip redirect/toast for login endpoint - let inline form error handle it
      if (error.config?.url?.includes('/auth/login')) {
        return Promise.reject(error)
      }

      const originalConfig = error.config

      // If config is missing, reject immediately
      if (!originalConfig) {
        removeToken()
        toast.error('Session expired. Please login again.')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // If already refreshing, queue the request
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalConfig.headers.Authorization = `Bearer ${token}`
            return axiosInstance(originalConfig)
          })
          .catch((err) => Promise.reject(err instanceof Error ? err : new Error(String(err))))
      }

      // Mark as refreshing and attempt token refresh
      isRefreshing = true

      try {
        // Use registered refresh handler instead of direct import
        const handler = getRefreshHandler()
        if (!handler) {
          throw new Error('Refresh handler not registered')
        }
        const newToken = await handler()
        setToken(newToken.access_token)
        processQueue(null, newToken.access_token)
        originalConfig.headers.Authorization = `Bearer ${newToken.access_token}`
        return axiosInstance(originalConfig)
      } catch (err) {
        const errorToReject = err instanceof Error ? err : new Error(String(err))
        processQueue(errorToReject, null)
        removeToken()
        toast.error('Session expired. Please login again.')
        window.location.href = '/login'
        return Promise.reject(errorToReject)
      } finally {
        isRefreshing = false
      }
    }

    if (error.response?.status === 403) {
      toast.error('Access denied')
    }
    return Promise.reject(error)
  }
)

export default axiosInstance