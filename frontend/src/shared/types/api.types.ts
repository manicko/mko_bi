export interface UserProfile {
  id: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
}

export interface DashboardSummary {
  id: string
  name: string
  description: string | null
  permission: 'view' | 'edit' | 'admin'
}

export interface GraphData {
  graph_id: string
  data: unknown // Plotly data format
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
  config: unknown
}

export interface Filter {
  id: string
  name: string
  type: 'select' | 'multiselect' | 'range' | 'date'
  options?: unknown
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
  permission: 'view' | 'edit' | 'admin'
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
  type: 'bar' | 'line' | 'pie' | 'table'
  title: string
  config: Record<string, unknown>
}

export interface GraphConfig {
  id: string
  name: string
  type: 'bar' | 'line' | 'pie' | 'table'
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
  type: 'select' | 'multiselect' | 'range' | 'date'
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
  type: 'bar' | 'line' | 'pie' | 'table'
  name: string
  data: PlotlyData
  layout?: PlotlyLayout
}

export interface PlotlyData {
  x?: unknown[]
  y?: unknown[]
  z?: unknown[]
  labels?: unknown[]
  values?: unknown[]
  type?: string
  marker?: Record<string, unknown>
  line?: Record<string, unknown>
  [key: string]: unknown
}

export interface PlotlyLayout {
  title?: string
  xaxis?: Record<string, unknown>
  yaxis?: Record<string, unknown>
  [key: string]: unknown
}

// Upload types
export type UploadMode = 'overwrite' | 'append'

export interface UploadResponse {
  message: string
  processing_log_id: string
}

export interface ProcessingStatusResponse {
  status: 'started' | 'uploaded' | 'processing' | 'success' | 'failed' | 'completed'
  message?: string
  started_at?: string
  finished_at?: string
}

export interface ProcessingResult {
  rows_processed: number
  status: string
  message?: string
}

// Admin types
export interface AdminUser {
  id: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
  is_active: boolean
  created_at: string
}

export interface UpdateUserRoleRequest {
  role: 'admin' | 'editor' | 'viewer'
}

export interface RegistrationRequestItem {
  id: string
  email: string
  status: 'pending' | 'approved' | 'rejected'
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
  permission: 'view' | 'edit' | 'admin'
}

export interface GrantAccessRequest {
  user_id: string
  permission: 'view' | 'edit' | 'admin'
}

export interface ProcessingLog {
  id: string
  dashboard_id: string | null
  dashboard_name?: string
  status: 'started' | 'uploaded' | 'processing' | 'success' | 'failed' | 'completed'
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
