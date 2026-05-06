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
  data: any // Plotly data format
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
  config: any
}

export interface Filter {
  id: string
  name: string
  type: 'select' | 'multiselect' | 'range' | 'date'
  options?: any
}

export interface UploadResponse {
  message: string
  filename: string
  status: string
}
