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
    } else if (getTokenWithExpirationCheck() === null) {
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
      removeToken()
      toast.error('Session expired. Please login again.')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axiosInstance
