import type { UserRole, DashboardPermission, GraphType, FilterType, ProcessingStatus, RegistrationStatus } from './enums'
import type { Data, Layout } from 'react-plotly.js'

// Re-export Plotly types for convenience
export type PlotlyData = Data
export type PlotlyLayout = Layout

export interface UserProfile {
  id: string
  email: string
  role: UserRole
  display_name: string
  created_at: string
  force_password_change: boolean
}

export interface DashboardSummary {
  id: string
  name: string
  description: string | null
  permission: DashboardPermission
  created_at: string
}

export interface GraphData {
  graph_id: string
  data: Data[] // Plotly data format
}

export interface LoginRequest {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserProfile
}

export interface Dashboard {
  id: string
  name: string
  description: string | null
  config: DashboardConfig
}

export interface Filter {
  id: string
  name: string
  type: FilterType
  options?: Record<string, unknown>
}

export interface UploadResponse {
  task_id: string
  filename: string
  dashboard_id: string
  status: string
  message: string
  uploaded_at: string
}

export interface DashboardConfig {
  graph_types: GraphType[]
  filters?: DashboardFilterConfig[]
  aggregations?: DashboardAggregationConfig[]
  charts?: DashboardChartConfig[]
  title?: string
  description?: string
}

export interface DashboardFilterConfig {
  field: string
  type: string
  multi?: boolean
  source?: string
  options?: Array<{ label: string; value: string }>
  default?: string | string[] | number
}

export interface DashboardAggregationConfig {
  type: string
  field: string
}

export interface DashboardChartConfig {
  type: GraphType
  x?: string
  y?: string
  title?: string
  config?: Record<string, unknown>
}

export interface FilterDetail {
  id: string
  name: string
  type: FilterType
  config: FilterConfig
}

export interface FilterConfig {
  field: string
  source?: string
  multi?: boolean
  min?: number
  max?: number
  options?: Array<{ label: string; value: string }>
}

export interface RegistrationRequest {
  email: string
}

export interface RegistrationResponse {
  message: string
  request_id: string
}

export interface DashboardDetail {
  id: string
  name: string
  description: string | null
  config: DashboardConfig
  permission: DashboardPermission
}

export interface AggregatedDataRequest {
  dashboard_id: string
  graph_id?: string
  filters?: Record<string, string | string[] | number | number[]>
}

export interface AggregatedDataResponse {
  graphs: GraphDataWithConfig[]
}

export interface GraphDataWithConfig {
  graph_id: string
  type: GraphType
  name: string
  data: Data[]
  layout?: Layout
}

// Upload types
// UploadMode is now imported from './enums'

export interface ProcessingStatusResponse {
  status: ProcessingStatus
  message?: string
  started_at?: string
  finished_at?: string
}

export interface ProcessingResult {
  rows_processed: number
  status: ProcessingStatus
  message?: string
}

// Admin types
export interface AdminUser {
  id: string
  email: string
  role: UserRole
  created_at: string
  force_password_change: boolean
}

export interface UpdateUserRoleRequest {
  role: UserRole
}

export interface CreateUserRequest {
  email: string
  password: string
  role: UserRole
}

export interface RegistrationRequestItem {
  id: string
  email: string
  status: RegistrationStatus
  requested_by_ip?: string
  reviewed_by?: string
  reviewed_at?: string
  created_at: string
}

export interface DashboardAdmin {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface CreateDashboardRequest {
  name: string
  description?: string
  layout?: string
}

export interface UpdateDashboardRequest {
  name?: string
  description?: string
}

export interface DashboardAccess {
  user_id: string
  dashboard_id: string
  permission: DashboardPermission
}

export interface GrantAccessRequest {
  dashboard_id: string
  user_id: string
  permission: DashboardPermission
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface ProcessingLog {
  id: string
  dashboard_id: string | null
  dashboard_name?: string | null
  status: ProcessingStatus
  message?: string
  started_at: string | null
  finished_at?: string
}

export interface LogFilters {
  dashboard_id?: string
  status_filter?: string
  date_from?: string
  date_to?: string
}
