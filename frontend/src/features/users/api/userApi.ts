import { axiosInstance } from '../../../shared/api/axiosInstance'
import type { UserProfile } from '../../../shared/types/api.types'

export async function getProfile(): Promise<UserProfile> {
  const response = await axiosInstance.get<UserProfile>('/auth/me')
  return response.data
}

export async function deleteAccount(): Promise<void> {
  await axiosInstance.delete('/users/me')
}
