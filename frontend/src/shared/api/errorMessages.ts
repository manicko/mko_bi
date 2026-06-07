import { ErrorCode } from '../types/enums'

/**
 * Type for partial error message maps.
 * Feature modules can define only relevant error codes.
 */
export type PartialErrorMessages = Partial<Record<ErrorCode, string>>

/**
 * Shared error message map containing general error codes.
 * Used as fallback for codes not defined in feature-specific maps.
 */
export const sharedErrorMessages: Record<ErrorCode, string> = {
  // General errors
  [ErrorCode.INTERNAL_ERROR]: 'Internal server error',
  [ErrorCode.SERVICE_UNAVAILABLE]: 'Service temporarily unavailable',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Rate limit exceeded. Please try again later.',
  // Authentication errors (fallback defaults)
  [ErrorCode.AUTHENTICATION_FAILED]: 'Authentication failed',
  [ErrorCode.TOKEN_EXPIRED]: 'Token expired',
  [ErrorCode.TOKEN_REVOKED]: 'Token revoked',
  [ErrorCode.INVALID_TOKEN]: 'Invalid token',
  // Authorization errors (fallback defaults)
  [ErrorCode.PERMISSION_DENIED]: 'Access denied',
  [ErrorCode.INSUFFICIENT_PERMISSIONS]: 'Insufficient permissions',
  [ErrorCode.ACCESS_DENIED]: 'Access denied',
  // Resource errors
  [ErrorCode.NOT_FOUND]: 'Resource not found',
  [ErrorCode.DASHBOARD_NOT_FOUND]: 'Dashboard not found',
  [ErrorCode.USER_NOT_FOUND]: 'User not found',
  [ErrorCode.GRAPH_NOT_FOUND]: 'Graph not found',
  [ErrorCode.FILTER_NOT_FOUND]: 'Filter not found',
  [ErrorCode.LAYOUT_NOT_FOUND]: 'Layout not found',
  [ErrorCode.PROCESSING_CONFIG_NOT_FOUND]: 'Processing configuration not found',
  // Validation errors
  [ErrorCode.VALIDATION_ERROR]: 'Validation error',
  [ErrorCode.INVALID_EMAIL]: 'Invalid email format',
  [ErrorCode.INVALID_PASSWORD]: 'Invalid password',
  [ErrorCode.MISSING_REQUIRED_FIELD]: 'Missing required field',
  [ErrorCode.INVALID_FIELD_VALUE]: 'Invalid field value',
  // File errors
  [ErrorCode.FILE_UPLOAD_ERROR]: 'File upload error',
  [ErrorCode.FILE_TOO_LARGE]: 'File too large',
  [ErrorCode.INVALID_FILE_TYPE]: 'Invalid file type',
  [ErrorCode.FILE_PROCESSING_ERROR]: 'File processing error',
  // Conflict errors
  [ErrorCode.EMAIL_ALREADY_EXISTS]: 'Email already in use',
  [ErrorCode.FILTER_ALREADY_BOUND]: 'Filter already bound',
  [ErrorCode.DUPLICATE_RESOURCE]: 'Duplicate resource',
  // Processing errors
  [ErrorCode.PROCESSING_FAILED]: 'Data processing failed',
  [ErrorCode.PROCESSING_IN_PROGRESS]: 'Data processing already in progress',
}

/**
 * Default English fallback message for unknown error codes.
 */
export const DEFAULT_ERROR_MESSAGE = 'An error occurred'

/**
 * Lookup error message by code.
 * Resolution order: feature map → shared map → error.detail → "An error occurred"
 *
 * @param code - The error code to look up
 * @param featureMessages - Optional feature-specific error messages
 * @param detail - Optional detail message from API response
 * @returns User-friendly English error message
 */
export function getErrorMessage(
  code: ErrorCode,
  featureMessages?: PartialErrorMessages,
  detail?: string,
): string {
  // First: check feature-specific map for override
  if (featureMessages?.[code]) {
    return featureMessages[code]
  }

  // Second: check shared map
  if (sharedErrorMessages[code]) {
    return sharedErrorMessages[code]
  }

// Third: use detail if provided
  if (detail) {
    return detail
  }

  // Fourth: fallback to default English message
  return DEFAULT_ERROR_MESSAGE
}