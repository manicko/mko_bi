import axios, { AxiosError } from 'axios'
import { toast } from 'react-hot-toast'
import { getTokenWithExpirationCheck, removeToken } from '../../features/auth/model/authToken'

export const axiosInstance = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
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
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Skip redirect/toast for login endpoint - let inline form error handle it
      if (error.config?.url?.includes('/auth/login')) {
        return Promise.reject(error)
      }
      removeToken()
      toast.error('Session expired. Please login again.')
      window.location.href = '/login'
    }
    if (error.response?.status === 403) {
      toast.error('Access denied')
    }
    return Promise.reject(error)
  }
)

export default axiosInstance
