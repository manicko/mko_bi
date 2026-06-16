import { extractApiError, type ErrorExtractionResult } from '../api/errorHandler'

/**
 * Hook for extracting structured error information from React Query errors.
 *
 * Wraps extractApiError for convenient use in components. Handles the error
 * extraction chain: legacy FastAPI validation format → RFC 7807 format →
 * field-level errors → AxiosError → generic fallback.
 *
 * @param error - Unknown error from React Query or API call
 * @returns Structured error with code, message, and optional details
 *
 * @example
 * ```tsx
 * const { data, error } = useMyDashboards()
 * const { code, message } = useApiError(error)
 *
 * if (error) {
 *   return <div>Error: {message}</div>
 * }
 * ```
 */
export function useApiError(error: unknown): ErrorExtractionResult {
  return extractApiError(error)
}