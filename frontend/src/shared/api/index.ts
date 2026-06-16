export type { AuthResponse, Dashboard, DashboardSummary, Filter, LoginRequest, UploadResponse, UserProfile, ApiError, ValidationFieldError } from '../types/api.types'
export { ErrorCode } from '../types/enums'
export { axiosInstance } from './axiosInstance'
export { extractApiError } from './errorHandler'
export type { ErrorExtractionResult } from './errorHandler'
export { sharedErrorMessages, getErrorMessage, DEFAULT_ERROR_MESSAGE } from './errorMessages'
export type { PartialErrorMessages } from './errorMessages'

