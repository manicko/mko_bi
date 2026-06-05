import { describe, it, expect } from 'vitest'
import { extractApiError } from '../errorHandler'
import { ErrorCode } from '../../types/enums'

describe('extractApiError', () => {
  it('extracts error from RFC 7807 format with code field', () => {
    const axiosError = {
      response: {
        status: 404,
        data: {
          type: 'https://api.mkobi.com/errors/not_found',
          title: 'Resource not found',
          status: 404,
          detail: 'Dashboard with id test-id not found',
          code: 'DASHBOARD_NOT_FOUND',
          details: { resource_id: 'test-id' },
        },
      },
    }

    const result = extractApiError(axiosError)

    expect(result.code).toBe(ErrorCode.DASHBOARD_NOT_FOUND)
    expect(result.message).toBe('Dashboard with id test-id not found')
    expect(result.details).toEqual({ resource_id: 'test-id' })
  })

  it('extracts error from RFC 7807 format using title when detail missing', () => {
    const axiosError = {
      response: {
        status: 401,
        data: {
          type: 'https://api.mkobi.com/errors/invalid_token',
          title: 'Token expired',
          status: 401,
          code: 'TOKEN_EXPIRED',
        },
      },
    }

    const result = extractApiError(axiosError)

    expect(result.code).toBe(ErrorCode.TOKEN_EXPIRED)
    expect(result.message).toBe('Token expired')
  })

  it('extracts field-level messages from RFC 7807 validation error with errors array', () => {
    const axiosError = {
      response: {
        status: 422,
        data: {
          type: 'https://api.mkobi.com/errors/validation_error',
          title: 'Validation error',
          status: 422,
          detail: 'Request validation failed',
          code: 'VALIDATION_ERROR',
          errors: [
            { loc: ['body', 'email'], msg: 'Invalid email format', type: 'value_error' },
            { loc: ['body', 'password'], msg: 'Required', type: 'value_error.missing' },
          ],
        },
      },
    }

    const result = extractApiError(axiosError)

    expect(result.code).toBe(ErrorCode.VALIDATION_ERROR)
    expect(result.message).toBe('email: Invalid email format, password: Required')
    expect(result.details?.validation_errors).toHaveLength(2)
  })

  it('falls back to detail when validation error has empty errors array', () => {
    const axiosError = {
      response: {
        status: 422,
        data: {
          code: 'VALIDATION_ERROR',
          detail: 'Request validation failed',
          errors: [],
        },
      },
    }

    const result = extractApiError(axiosError)

    expect(result.code).toBe(ErrorCode.VALIDATION_ERROR)
    expect(result.message).toBe('Request validation failed')
  })

  it('handles legacy validation format without loc field', () => {
    const axiosError = {
      response: {
        status: 422,
        data: {
          errors: [{ msg: 'Some error' }],
        },
      },
    }

    const result = extractApiError(axiosError)

    // Legacy format without code field should still return VALIDATION_ERROR
    expect(result.code).toBe(ErrorCode.VALIDATION_ERROR)
    expect(result.message).toBe('Some error')
  })

  it('falls back to error.message for non-RFC 7807 AxiosError', () => {
    const axiosError = {
      response: { status: 500 },
      message: 'Network timeout',
    }

    const result = extractApiError(axiosError)

    expect(result.code).toBe(ErrorCode.INTERNAL_ERROR)
    expect(result.message).toBe('Network timeout')
  })

it('handles generic Error objects', () => {
    const error = new Error('Something went wrong')

    const result = extractApiError(error)

    expect(result.code).toBe(ErrorCode.INTERNAL_ERROR)
    expect(result.message).toBe('Something went wrong')
  })

  it('returns English fallback message for unknown error types', () => {
    const result = extractApiError({ unknown: 'object' })

    expect(result.code).toBe(ErrorCode.INTERNAL_ERROR)
    expect(result.message).toBe('An error occurred')
  })

  it('returns English fallback message for null/undefined', () => {
    expect(extractApiError(null).message).toBe('An error occurred')
    expect(extractApiError(undefined).message).toBe('An error occurred')
  })

  it('maps unknown error codes to INTERNAL_ERROR', () => {
    const axiosError = {
      response: {
        status: 500,
        data: {
          code: 'UNKNOWN_ERROR',
          detail: 'Something weird',
        },
      },
    }

    const result = extractApiError(axiosError)

    expect(result.code).toBe(ErrorCode.INTERNAL_ERROR)
    expect(result.message).toBe('Something weird')
  })

  it('handles all ErrorCode values are accessible', () => {
    // Verify ErrorCode enum has expected values
    expect(ErrorCode.INTERNAL_ERROR).toBe('INTERNAL_ERROR')
    expect(ErrorCode.VALIDATION_ERROR).toBe('VALIDATION_ERROR')
    expect(ErrorCode.NOT_FOUND).toBe('NOT_FOUND')
    expect(ErrorCode.AUTHENTICATION_FAILED).toBe('AUTHENTICATION_FAILED')
    expect(ErrorCode.PERMISSION_DENIED).toBe('PERMISSION_DENIED')
    expect(ErrorCode.FILE_TOO_LARGE).toBe('FILE_TOO_LARGE')
    expect(ErrorCode.EMAIL_ALREADY_EXISTS).toBe('EMAIL_ALREADY_EXISTS')
  })
})