import axios, { AxiosError } from 'axios'
import { toast } from 'react-hot-toast'

export const axiosInstance = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add JWT token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
      sessionStorage.removeItem('access_token')
      toast.error('Session expired. Please login again.')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axiosInstance
