import { axiosInstance } from '../../../shared/api/axiosInstance'
import type { UserProfile, ChangePasswordRequest } from '../../../shared/types/api.types'

export async function getProfile(): Promise<UserProfile> {
  const response = await axiosInstance.get<UserProfile>('/auth/me')
  return response.data
}

export async function deleteAccount(): Promise<void> {
  await axiosInstance.delete('/users/me')
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await axiosInstance.post('/auth/change-password', data)
}
