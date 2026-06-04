import { ErrorCode } from '../types/enums'
import type { ValidationFieldError } from '../types/api.types'

/**
 * Error extraction result for frontend consumption.
 */
export interface ErrorExtractionResult {
  code: ErrorCode
  message: string
  details?: Record<string, unknown>
}

/**
 * AxiosError-like structure for type narrowing.
 */
interface AxiosErrorLike {
  response?: {
    status?: number
    data?: unknown
  }
  message?: string
}

/**
 * Extract structured error information from various error formats.
 *
 * Handles extraction chain:
 * 1. Legacy FastAPI validation format (errors array without code field, status 422)
 * 2. RFC 7807 format with code field
 * 3. For VALIDATION_ERROR code, parse field-level errors from errors array
 * 4. AxiosError → error.message fallback
 * 5. Generic fallback message
 *
 * @param error - Unknown error to extract from
 * @returns Structured error with code, message, and optional details
 */
export function extractApiError(error: unknown): ErrorExtractionResult {
  // Try to extract from AxiosError
  if (isAxiosError(error)) {
    const responseData = error.response?.data

    if (responseData && typeof responseData === 'object') {
      const data = responseData as Record<string, unknown>

      // Check for legacy FastAPI validation format with errors array (no code field)
      if (!('code' in data) && error.response?.status === 422 && 'errors' in data && Array.isArray(data.errors)) {
        const validationErrors = data.errors as ValidationFieldError[]
        const fieldMessages = extractFieldErrors(validationErrors)
        return {
          code: ErrorCode.VALIDATION_ERROR,
          message: fieldMessages.length > 0 ? fieldMessages.join(', ') : 'Validation failed',
          details: { validation_errors: validationErrors },
        }
      }

      // Check for RFC 7807 format with code field
      if ('code' in data && typeof data.code === 'string') {
        const code = mapErrorCode(data.code)
        const message = typeof data.detail === 'string' ? data.detail : data.title as string | undefined

        // If code is VALIDATION_ERROR and errors array exists, parse field-level errors
        if (code === ErrorCode.VALIDATION_ERROR && 'errors' in data && Array.isArray(data.errors)) {
          const validationErrors = data.errors as ValidationFieldError[]
          const fieldMessages = extractFieldErrors(validationErrors)
          return {
            code,
            message: fieldMessages.length > 0 ? fieldMessages.join(', ') : message || 'Validation failed',
            details: { validation_errors: validationErrors },
          }
        }

        return {
          code,
          message: message || 'An error occurred',
          details: data.details as Record<string, unknown> | undefined,
        }
      }
    }

    // Fallback to error message
    if (error.message) {
      return {
        code: ErrorCode.INTERNAL_ERROR,
        message: error.message,
      }
    }
  }

  // Handle generic Error objects
  if (error instanceof Error && error.message) {
    return {
      code: ErrorCode.INTERNAL_ERROR,
      message: error.message,
    }
  }

  // Generic fallback with Russian message as specified
  return {
    code: ErrorCode.INTERNAL_ERROR,
    message: 'Произошла ошибка',
  }
}

/**
 * Type guard for AxiosError-like objects.
 */
function isAxiosError(error: unknown): error is AxiosErrorLike {
  return (
    typeof error === 'object' &&
    error !== null &&
    ('response' in error || 'message' in error)
  )
}

/**
 * Map string error code to ErrorCode type, with fallback to INTERNAL_ERROR.
 */
function mapErrorCode(code: string): ErrorCode {
  if (Object.values(ErrorCode).includes(code as ErrorCode)) {
    return code as ErrorCode
  }
  return ErrorCode.INTERNAL_ERROR
}

/**
 * Extract field-level error messages from validation errors.
 */
function extractFieldErrors(errors: ValidationFieldError[]): string[] {
  return errors
    .map((err) => {
      if (err.loc && err.loc.length > 0) {
        const field = err.loc[err.loc.length - 1]
        return `${field}: ${err.msg}`
      }
      return err.msg
    })
    .filter((msg): msg is string => msg !== null)
}