import { axiosInstance } from '../../../shared/api/axiosInstance'
import type { ChangePasswordRequest } from '../../../shared/types/api.types'
export { getProfile } from '../../auth/api/authApi'

export async function deleteAccount(): Promise<void> {
  await axiosInstance.delete('/users/me')
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await axiosInstance.post('/auth/change-password', data)
}
