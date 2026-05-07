/**
 * Shared enum definitions matching backend StrEnum values.
 * These constants ensure type safety and consistency between frontend and backend.
 * Using const objects instead of enums for erasableSyntaxOnly compatibility.
 */

export const UserRole = {
  ADMIN: 'admin',
  EDITOR: 'editor',
  VIEWER: 'viewer',
} as const

export type UserRole = (typeof UserRole)[keyof typeof UserRole]

export const DashboardPermission = {
  VIEW: 'view',
  EDIT: 'edit',
  ADMIN: 'admin',
} as const

export type DashboardPermission = (typeof DashboardPermission)[keyof typeof DashboardPermission]

export const GraphType = {
  BAR: 'bar',
  LINE: 'line',
  PIE: 'pie',
  TABLE: 'table',
} as const

export type GraphType = (typeof GraphType)[keyof typeof GraphType]

export const FilterType = {
  SELECT: 'select',
  MULTISELECT: 'multiselect',
  RANGE: 'range',
  DATE: 'date',
} as const

export type FilterType = (typeof FilterType)[keyof typeof FilterType]

export const RegistrationStatus = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
} as const

export type RegistrationStatus = (typeof RegistrationStatus)[keyof typeof RegistrationStatus]

export const UploadMode = {
  OVERWRITE: 'overwrite',
  APPEND: 'append',
} as const

export type UploadMode = (typeof UploadMode)[keyof typeof UploadMode]

export const ProcessingStatus = {
  STARTED: 'started',
  UPLOADED: 'uploaded',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  FAILED: 'failed',
  COMPLETED: 'completed',
} as const

export type ProcessingStatus = (typeof ProcessingStatus)[keyof typeof ProcessingStatus]

export const FileUploadStatus = {
  PENDING: 'pending',
  UPLOADING: 'uploading',
  SUCCESS: 'success',
  ERROR: 'error',
} as const

export type FileUploadStatus = (typeof FileUploadStatus)[keyof typeof FileUploadStatus]
