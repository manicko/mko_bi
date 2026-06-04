import { describe, it, expect } from 'vitest'
import {
  UserRole,
  DashboardPermission,
  GraphType,
  FilterType,
  RegistrationStatus,
  UploadMode,
  ProcessingStatus,
  FileUploadStatus,
  ErrorCode,
} from '../enums'

describe('UserRole', () => {
  it('has correct values', () => {
    expect(UserRole.ADMIN).toBe('admin')
    expect(UserRole.EDITOR).toBe('editor')
    expect(UserRole.VIEWER).toBe('viewer')
  })

  it('has exactly 3 roles', () => {
    expect(Object.keys(UserRole)).toHaveLength(3)
  })
})

describe('DashboardPermission', () => {
  it('has correct values', () => {
    expect(DashboardPermission.VIEW).toBe('view')
    expect(DashboardPermission.EDIT).toBe('edit')
    expect(DashboardPermission.ADMIN).toBe('admin')
  })

  it('has exactly 3 permissions', () => {
    expect(Object.keys(DashboardPermission)).toHaveLength(3)
  })
})

describe('GraphType', () => {
  it('has correct values', () => {
    expect(GraphType.BAR).toBe('bar')
    expect(GraphType.LINE).toBe('line')
    expect(GraphType.PIE).toBe('pie')
    expect(GraphType.TABLE).toBe('table')
  })

  it('has exactly 4 types', () => {
    expect(Object.keys(GraphType)).toHaveLength(4)
  })
})

describe('FilterType', () => {
  it('has correct values', () => {
    expect(FilterType.SELECT).toBe('select')
    expect(FilterType.MULTISELECT).toBe('multiselect')
    expect(FilterType.RANGE).toBe('range')
    expect(FilterType.DATE).toBe('date')
  })

  it('has exactly 4 types', () => {
    expect(Object.keys(FilterType)).toHaveLength(4)
  })
})

describe('RegistrationStatus', () => {
  it('has correct values', () => {
    expect(RegistrationStatus.PENDING).toBe('pending')
    expect(RegistrationStatus.APPROVED).toBe('approved')
    expect(RegistrationStatus.REJECTED).toBe('rejected')
  })
})

describe('UploadMode', () => {
  it('has correct values', () => {
    expect(UploadMode.OVERWRITE).toBe('overwrite')
    expect(UploadMode.APPEND).toBe('append')
  })
})

describe('ProcessingStatus', () => {
  it('has correct values', () => {
    expect(ProcessingStatus.STARTED).toBe('started')
    expect(ProcessingStatus.UPLOADED).toBe('uploaded')
    expect(ProcessingStatus.PROCESSING).toBe('processing')
    expect(ProcessingStatus.COMPLETED).toBe('completed')
    expect(ProcessingStatus.FAILED).toBe('failed')
    // SUCCESS is deprecated but should equal 'completed' for backward compatibility
    expect(ProcessingStatus.SUCCESS).toBe('completed')
  })

  it('has exactly 6 statuses', () => {
    expect(Object.keys(ProcessingStatus)).toHaveLength(6)
  })
})

describe('FileUploadStatus', () => {
  it('has correct values', () => {
    expect(FileUploadStatus.PENDING).toBe('pending')
    expect(FileUploadStatus.UPLOADING).toBe('uploading')
    expect(FileUploadStatus.SUCCESS).toBe('success')
    expect(FileUploadStatus.ERROR).toBe('error')
  })
})

describe('ErrorCode', () => {
  it('has correct values for general errors', () => {
    expect(ErrorCode.INTERNAL_ERROR).toBe('INTERNAL_ERROR')
    expect(ErrorCode.SERVICE_UNAVAILABLE).toBe('SERVICE_UNAVAILABLE')
    expect(ErrorCode.RATE_LIMIT_EXCEEDED).toBe('RATE_LIMIT_EXCEEDED')
  })

  it('has correct values for authentication errors', () => {
    expect(ErrorCode.AUTHENTICATION_FAILED).toBe('AUTHENTICATION_FAILED')
    expect(ErrorCode.TOKEN_EXPIRED).toBe('TOKEN_EXPIRED')
    expect(ErrorCode.TOKEN_REVOKED).toBe('TOKEN_REVOKED')
    expect(ErrorCode.INVALID_TOKEN).toBe('INVALID_TOKEN')
  })

  it('has correct values for authorization errors', () => {
    expect(ErrorCode.PERMISSION_DENIED).toBe('PERMISSION_DENIED')
    expect(ErrorCode.INSUFFICIENT_PERMISSIONS).toBe('INSUFFICIENT_PERMISSIONS')
    expect(ErrorCode.ACCESS_DENIED).toBe('ACCESS_DENIED')
  })

  it('has correct values for resource errors', () => {
    expect(ErrorCode.NOT_FOUND).toBe('NOT_FOUND')
    expect(ErrorCode.DASHBOARD_NOT_FOUND).toBe('DASHBOARD_NOT_FOUND')
    expect(ErrorCode.USER_NOT_FOUND).toBe('USER_NOT_FOUND')
  })

  it('has correct values for validation errors', () => {
    expect(ErrorCode.VALIDATION_ERROR).toBe('VALIDATION_ERROR')
    expect(ErrorCode.INVALID_EMAIL).toBe('INVALID_EMAIL')
    expect(ErrorCode.INVALID_PASSWORD).toBe('INVALID_PASSWORD')
  })

  it('has correct values for file errors', () => {
    expect(ErrorCode.FILE_UPLOAD_ERROR).toBe('FILE_UPLOAD_ERROR')
    expect(ErrorCode.FILE_TOO_LARGE).toBe('FILE_TOO_LARGE')
    expect(ErrorCode.INVALID_FILE_TYPE).toBe('INVALID_FILE_TYPE')
    expect(ErrorCode.FILE_PROCESSING_ERROR).toBe('FILE_PROCESSING_ERROR')
  })

  it('has correct values for conflict errors', () => {
    expect(ErrorCode.EMAIL_ALREADY_EXISTS).toBe('EMAIL_ALREADY_EXISTS')
    expect(ErrorCode.FILTER_ALREADY_BOUND).toBe('FILTER_ALREADY_BOUND')
    expect(ErrorCode.DUPLICATE_RESOURCE).toBe('DUPLICATE_RESOURCE')
  })

  it('has correct values for processing errors', () => {
    expect(ErrorCode.PROCESSING_FAILED).toBe('PROCESSING_FAILED')
    expect(ErrorCode.PROCESSING_IN_PROGRESS).toBe('PROCESSING_IN_PROGRESS')
  })
})
