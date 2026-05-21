import { axiosInstance } from '../../../shared/api/axiosInstance'
import type {
  AdminUser,
  CreateUserRequest,
  RegistrationRequestItem,
  DashboardAdmin,
  CreateDashboardRequest,
  UpdateDashboardRequest,
  GrantAccessRequest,
  ProcessingLog,
  LogFilters,
} from '../../../shared/types/api.types'

// User Management API
export async function getUsers(): Promise<AdminUser[]> {
  const response = await axiosInstance.get<AdminUser[]>('/admin/users')
  return response.data
}

export async function createUser(data: CreateUserRequest): Promise<AdminUser> {
  const response = await axiosInstance.post<AdminUser>('/users', data)
  return response.data
}

export async function changeUserRole(userId: string, role: string): Promise<AdminUser> {
  const response = await axiosInstance.patch<AdminUser>(`/admin/users/${userId}/role`, { role })
  return response.data
}

export async function deleteUser(userId: string): Promise<void> {
  await axiosInstance.delete(`/admin/users/${userId}`)
}

// Registration Requests API
export async function getRegistrationRequests(): Promise<RegistrationRequestItem[]> {
  const response = await axiosInstance.get<RegistrationRequestItem[]>('/admin/registration-requests')
  return response.data
}

export async function approveRequest(requestId: string): Promise<void> {
  await axiosInstance.post(`/admin/registration-requests/${requestId}/approve`)
}

export async function rejectRequest(requestId: string): Promise<void> {
  await axiosInstance.post(`/admin/registration-requests/${requestId}/reject`)
}

// Dashboard Management API
export async function getDashboardsAdmin(): Promise<DashboardAdmin[]> {
  const response = await axiosInstance.get<DashboardAdmin[]>('/dashboards')
  return response.data
}

export async function createDashboard(data: CreateDashboardRequest): Promise<DashboardAdmin> {
  const payload: Record<string, unknown> = { name: data.name }
  if (data.description) {
    payload.description = data.description
  }
  if (data.layout) {
    payload.config = { graph_types: ['bar'], layout: data.layout }
  }
  const response = await axiosInstance.post<DashboardAdmin>('/dashboards', payload)
  return response.data
}

export async function updateDashboard(dashboardId: string, data: UpdateDashboardRequest): Promise<DashboardAdmin> {
  const response = await axiosInstance.put<DashboardAdmin>(`/dashboards/${dashboardId}`, data)
  return response.data
}

export async function deleteDashboard(dashboardId: string): Promise<void> {
  await axiosInstance.delete(`/dashboards/${dashboardId}`)
}

export async function grantDashboardAccess(dashboardId: string, data: GrantAccessRequest): Promise<void> {
  await axiosInstance.post(`/dashboards/${dashboardId}/access`, data)
}

// Logs API
export async function getLogs(filters?: LogFilters): Promise<ProcessingLog[]> {
  const response = await axiosInstance.get<ProcessingLog[]>('/admin/logs', { params: filters })
  return response.data
}
