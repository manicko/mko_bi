import type { UserRole, DashboardPermission, GraphType, FilterType, ProcessingStatus, RegistrationStatus } from './enums'
import type { Data, Layout } from 'plotly.js'

// Re-export Plotly types for convenience
export type PlotlyData = Data
export type PlotlyLayout = Layout

export interface UserProfile {
  id: string
  email: string
  role: UserRole
}

export interface DashboardSummary {
  id: string
  name: string
  description: string | null
  permission: DashboardPermission
}

export interface GraphData {
  graph_id: string
  data: Data[] // Plotly data format
}

export interface LoginRequest {
  email: string
  password: string
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
  message: string
  filename: string
  status: string
}

export interface RegistrationRequest {
  email: string
}

export interface RegistrationResponse {
  message: string
  request_id: string
}

// Dashboard types
export interface DashboardDetail {
  id: string
  name: string
  description: string | null
  config: DashboardConfig
  permission: DashboardPermission
}

export interface DashboardConfig {
  layout: LayoutConfig
  graphs: GraphConfig[]
  filters: string[] // filter IDs
  bindings: FilterBinding[]
}

export interface LayoutConfig {
  grid: GridItem[]
  charts: ChartConfig[]
}

export interface GridItem {
  graph_id: string
  x: number
  y: number
  w: number
  h: number
}

export interface ChartConfig {
  id: string
  type: GraphType
  title: string
  config: Record<string, unknown>
}

export interface GraphConfig {
  id: string
  name: string
  type: GraphType
  config: Record<string, unknown>
  dimensions: string[]
  metrics: string[]
}

export interface FilterBinding {
  filter: string
  graphs: string[]
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

export interface AggregatedDataRequest {
  dashboard_id: string
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

export interface UploadResponse {
  message: string
  processing_log_id: string
}

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
  is_active: boolean
  created_at: string
}

export interface UpdateUserRoleRequest {
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
  created_by: string
  created_at: string
  updated_at: string
}

export interface CreateDashboardRequest {
  name: string
  description?: string
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
  user_id: string
  permission: DashboardPermission
}

export interface ProcessingLog {
  id: string
  dashboard_id: string | null
  dashboard_name?: string
  status: ProcessingStatus
  message?: string
  started_at: string
  finished_at?: string
}

export interface LogFilters {
  dashboard_id?: string
  status?: string
  date_from?: string
  date_to?: string
}
