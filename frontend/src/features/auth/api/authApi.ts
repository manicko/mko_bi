import { axiosInstance } from '../../../shared/api/axiosInstance'
import type { AuthResponse, UserProfile, RegistrationRequest, RegistrationResponse } from '../../../shared/types/api.types'

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await axiosInstance.post<AuthResponse>('/auth/login', { email, password })
  return response.data
}

export async function registerRequest(email: string): Promise<RegistrationResponse> {
  const response = await axiosInstance.post<RegistrationResponse>('/auth/register-request', { email } as RegistrationRequest)
  return response.data
}

export async function getProfile(): Promise<UserProfile> {
  const response = await axiosInstance.get<UserProfile>('/auth/me')
  return response.data
}

export function logoutClient(): void {
  sessionStorage.removeItem('access_token')
}
